package search

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"sort"
	"sync"
	"time"
)

type Options struct {
	RequestTimeout, ProviderTimeout, RerankTimeout time.Duration
	MaxConcurrent, CacheEntries                    int
	CacheTTL                                       time.Duration
}

func DefaultOptions() Options {
	return Options{RequestTimeout: 10 * time.Second, ProviderTimeout: 3 * time.Second, RerankTimeout: 6 * time.Second, MaxConcurrent: 8, CacheEntries: 128, CacheTTL: 10 * time.Minute}
}

type cacheValue struct {
	Vector  []float32
	Created time.Time
}
type Service struct {
	Manifest Manifest
	repo     Repository
	provider Provider
	opts     Options
	slots    chan struct{}
	mu       sync.Mutex
	cache    map[[32]byte]cacheValue
}

func New(m Manifest, repo Repository, provider Provider, o Options) (*Service, error) {
	if m.Validate() != nil || repo == nil || o.RequestTimeout <= 0 || o.ProviderTimeout <= 0 || o.RerankTimeout <= 0 || o.MaxConcurrent < 1 || o.MaxConcurrent > 64 || o.CacheEntries < 0 || o.CacheEntries > 1024 || o.CacheTTL <= 0 {
		return nil, ErrInvalid
	}
	return &Service{Manifest: m, repo: repo, provider: provider, opts: o, slots: make(chan struct{}, o.MaxConcurrent), cache: make(map[[32]byte]cacheValue)}, nil
}
func (s *Service) enter(ctx context.Context) (context.Context, func(), error) {
	select {
	case s.slots <- struct{}{}:
	default:
		return nil, nil, ErrCapacity
	}
	ctx, cancel := context.WithTimeout(ctx, s.opts.RequestTimeout)
	return ctx, func() { cancel(); <-s.slots }, nil
}
func (s *Service) Ready(ctx context.Context) error {
	ctx, done, e := s.enter(ctx)
	if e != nil {
		return e
	}
	defer done()
	return s.repo.Ready(ctx, s.Manifest)
}
func (s *Service) embedding(ctx context.Context, q string) ([]float32, error) {
	key := sha256.Sum256([]byte(s.Manifest.EmbeddingProfile + "\x00" + q))
	s.mu.Lock()
	v, ok := s.cache[key]
	s.mu.Unlock()
	if ok && time.Since(v.Created) < s.opts.CacheTTL {
		return v.Vector, nil
	}
	ctx, cancel := context.WithTimeout(ctx, s.opts.ProviderTimeout)
	defer cancel()
	vec, e := s.provider.Embed(ctx, q)
	if e != nil {
		return nil, e
	}
	if len(vec) != 1024 {
		return nil, errProvider
	}
	if s.opts.CacheEntries > 0 {
		s.mu.Lock()
		defer s.mu.Unlock()
		if len(s.cache) >= s.opts.CacheEntries {
			var oldest [32]byte
			var stamp time.Time
			for k, v := range s.cache {
				if stamp.IsZero() || v.Created.Before(stamp) {
					oldest = k
					stamp = v.Created
				}
			}
			delete(s.cache, oldest)
		}
		s.cache[key] = cacheValue{append([]float32(nil), vec...), time.Now()}
	}
	return vec, nil
}
func RRF(lists ...[]Hit) []Hit {
	scores := map[string]Hit{}
	for _, list := range lists {
		seen := map[string]bool{}
		for i, h := range list {
			if seen[h.ID] {
				continue
			}
			seen[h.ID] = true
			old, ok := scores[h.ID]
			if !ok {
				old = h
				old.Score = 0
			}
			old.Score += 1 / float64(60+i+1)
			scores[h.ID] = old
		}
	}
	out := make([]Hit, 0, len(scores))
	for _, h := range scores {
		out = append(out, h)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Score == out[j].Score {
			return out[i].ID < out[j].ID
		}
		return out[i].Score > out[j].Score
	})
	return out
}

// Collapse exact short duplicates within the same document and evidence type.
// SQL excerpts at the 1201-rune boundary may hide different tails; never merge those.
func uniquePassages(hits []Hit) []Hit {
	type key struct{ document, language, sourceVoice, textVoice, kind, text string }
	seen := make(map[key]bool)
	out := make([]Hit, 0, len(hits))
	for _, hit := range hits {
		if hit.DocumentID != "" && hit.Text != "" && len([]rune(hit.Text)) < 1201 {
			k := key{hit.DocumentID, hit.Language, hit.SourceVoice, hit.TextVoice, hit.TextKind, hit.Text}
			if seen[k] {
				continue
			}
			seen[k] = true
		}
		out = append(out, hit)
	}
	return out
}

func excerpt(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n]) + "…"
}
func (s *Service) Search(ctx context.Context, q Query) (Response, error) {
	start := time.Now()
	out := Response{Versions: s.Manifest.Versions(), Mode: q.Mode, Hits: []Hit{}}
	if e := q.Validate(); e != nil {
		return out, e
	}
	ctx, done, e := s.enter(ctx)
	if e != nil {
		return out, e
	}
	defer done()
	if e = s.repo.Ready(ctx, s.Manifest); e != nil {
		return out, ErrUnavailable
	}
	n := q.Limit * 3
	if n > 100 {
		n = 100
	}
	type result struct {
		hits []Hit
		err  error
	}
	lexical := make(chan result, 1)
	startLexical := func() {
		go func() { h, e := s.lexical(ctx, q, n); lexical <- result{h, e} }()
	}
	if q.Mode != "semantic" {
		startLexical()
	}
	var semantic []Hit
	if q.Mode != "lexical" {
		reason := ""
		if s.Manifest.EmbeddingProfile == "none" {
			reason = "embedding_profile_none"
		} else if s.provider == nil {
			reason = "external_disabled"
		} else {
			v, err := s.embedding(ctx, q.Text)
			if err != nil {
				reason = "embedding_unavailable"
			} else {
				semantic, err = s.semantic(ctx, q, v, n)
				if err != nil {
					return out, ErrUnavailable
				}
			}
		}
		if reason != "" {
			out.Mode = "lexical"
			out.Degraded = true
			out.Reason = reason
		}
	}
	var lex result
	if out.Mode != "semantic" {
		if q.Mode == "semantic" {
			startLexical()
		}
		select {
		case lex = <-lexical:
		case <-ctx.Done():
			return out, ErrUnavailable
		}
		if lex.err != nil {
			return out, ErrUnavailable
		}
	}
	switch out.Mode {
	case "lexical":
		out.Hits = lex.hits
	case "semantic":
		out.Hits = semantic
	case "hybrid":
		if q.Grouped {
			out.Hits = documentRRF(lex.hits, semantic)
		} else {
			out.Hits = RRF(lex.hits, semantic)
		}
	}
	if q.Grouped {
		if q.Section != "" {
			out.Hits = sectionCandidatesLimit(out.Hits, min(q.Limit, 28))
		} else {
			out.Hits = groupedCandidates(out.Hits)
		}
	} else {
		out.Hits = uniquePassages(out.Hits)
		if len(out.Hits) > q.Limit {
			out.Hits = out.Hits[:q.Limit]
		}
	}
	if out.Hits == nil {
		out.Hits = []Hit{}
	}
	// Provider and HTTP excerpts are bounded; the passage reader returns exact stored text.
	for i := range out.Hits {
		out.Hits[i].Text = excerpt(out.Hits[i].Text, 1200)
	}
	if q.Rerank && len(out.Hits) > 0 {
		if s.provider == nil {
			out.Degraded = true
			if out.Reason == "" {
				out.Reason = "rerank_unavailable"
			}
		} else {
			pctx, cancel := context.WithTimeout(ctx, s.opts.RerankTimeout)
			scores, err := s.provider.Rerank(pctx, q.Text, out.Hits)
			cancel()
			if err != nil || len(scores) != len(out.Hits) {
				out.Degraded = true
				if out.Reason == "" {
					out.Reason = "rerank_unavailable"
				}
			} else {
				for i := range out.Hits {
					out.Hits[i].Score = scores[i]
				}
				sort.SliceStable(out.Hits, func(i, j int) bool { return out.Hits[i].Score > out.Hits[j].Score })
				out.Reranked = true
			}
		}
	}
	if q.Grouped && q.Section == "" {
		out.Hits = groupedResults(out.Hits, q.Limit)
	}
	out.DurationMS = time.Since(start).Milliseconds()
	return out, nil
}
func (s *Service) Passage(ctx context.Context, id, lang string) (PassageResponse, error) {
	out := PassageResponse{Versions: s.Manifest.Versions()}
	if id == "" || len(id) > 1024 || (lang != "de" && lang != "en") {
		return out, ErrInvalid
	}
	ctx, done, e := s.enter(ctx)
	if e != nil {
		return out, e
	}
	defer done()
	if s.repo.Ready(ctx, s.Manifest) != nil {
		return out, ErrUnavailable
	}
	out.Passage, e = s.repo.Passage(ctx, s.Manifest, id, lang)
	return out, e
}
func (s *Service) Entity(ctx context.Context, id string) (EntityResponse, error) {
	out := EntityResponse{Versions: s.Manifest.Versions()}
	if id == "" || len(id) > 1024 {
		return out, ErrInvalid
	}
	ctx, done, e := s.enter(ctx)
	if e != nil {
		return out, e
	}
	defer done()
	if s.repo.Ready(ctx, s.Manifest) != nil {
		return out, ErrUnavailable
	}
	raw, e := s.repo.Entity(ctx, s.Manifest, id)
	out.Entity = json.RawMessage(raw)
	return out, e
}
