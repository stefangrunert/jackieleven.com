package search

import (
	"context"
	"encoding/json"
	"sort"
	"sync"
)

var sections = []string{"music", "live", "timeline", "writing", "press", "biography", "site"}

const sectionCandidates = 4
const sectionResults = 3

func validSection(section string) bool {
	for _, s := range sections {
		if s == section {
			return true
		}
	}
	return false
}
func hitSection(h Hit) string {
	var m struct {
		Section string `json:"section"`
	}
	_ = json.Unmarshal(h.Metadata, &m)
	if validSection(m.Section) {
		return m.Section
	}
	return "site"
}

// Older snapshots predate section metadata. Make the fallback explicit so a
// client can group the flat response without implementing a second classifier.
func withSection(h Hit, section string) Hit {
	var metadata map[string]json.RawMessage
	if json.Unmarshal(h.Metadata, &metadata) != nil || metadata == nil {
		metadata = make(map[string]json.RawMessage)
	}
	var present string
	if json.Unmarshal(metadata["section"], &present) == nil && validSection(present) {
		return h
	}
	metadata["section"], _ = json.Marshal(section)
	h.Metadata, _ = json.Marshal(metadata)
	return h
}
func documentKey(h Hit) string {
	if h.DocumentID != "" {
		return h.DocumentID
	}
	return h.ID
}
func sortHits(hits []Hit) {
	sort.SliceStable(hits, func(i, j int) bool {
		if hits[i].Score == hits[j].Score {
			return hits[i].ID < hits[j].ID
		}
		return hits[i].Score > hits[j].Score
	})
}
func querySections(q Query) []string {
	if q.Section != "" {
		return []string{q.Section}
	}
	out := make([]string, 0, len(sections))
	for _, section := range sections {
		// Automatic subdivision must never turn biography into an implicit opt-in.
		if section == "biography" && q.Voice != "pastiche" {
			continue
		}
		out = append(out, section)
	}
	return out
}

// At most two SQL operations per retrieval list; hybrid shares the four-connection
// pool. All queued work observes the original request context and deadline.
func (s *Service) groupedRetrieve(ctx context.Context, q Query, vector []float32) ([]Hit, error) {
	targets := querySections(q)
	candidateLimit := 12
	if q.Section != "" {
		candidateLimit = q.Limit * 2
		if candidateLimit > 60 {
			candidateLimit = 60
		}
	}
	type result struct {
		hits []Hit
		err  error
	}
	results := make([]result, len(targets))
	jobs := make(chan int, len(targets))
	for i := range targets {
		jobs <- i
	}
	close(jobs)
	var wg sync.WaitGroup
	for worker := 0; worker < 2; worker++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range jobs {
				if ctx.Err() != nil {
					results[i].err = ErrUnavailable
					continue
				}
				child := q
				child.Section = targets[i]
				// Twelve distinct documents per list allow fusion to recover cross-list
				// candidates; only four per section are sent to the optional reranker.
				if vector == nil {
					results[i].hits, results[i].err = s.repo.Lexical(ctx, s.Manifest, child, candidateLimit)
				} else {
					results[i].hits, results[i].err = s.repo.Semantic(ctx, s.Manifest, child, vector, candidateLimit)
				}
			}
		}()
	}
	wg.Wait()
	out := make([]Hit, 0, 12*len(targets))
	for _, r := range results {
		if r.err != nil {
			return nil, r.err
		}
		out = append(out, r.hits...)
	}
	sortHits(out)
	return out, nil
}
func (s *Service) lexical(ctx context.Context, q Query, n int) ([]Hit, error) {
	if q.Grouped {
		return s.groupedRetrieve(ctx, q, nil)
	}
	return s.repo.Lexical(ctx, s.Manifest, q, n)
}
func (s *Service) semantic(ctx context.Context, q Query, v []float32, n int) ([]Hit, error) {
	if q.Grouped {
		return s.groupedRetrieve(ctx, q, v)
	}
	return s.repo.Semantic(ctx, s.Manifest, q, v, n)
}

// Fusion ranks documents, but uses the semantic list's query-specific passage
// when both lists find a document. A title match can give every paragraph the
// same lexical score; retaining that arbitrary paragraph hides relevant evidence
// from the reranker. Scores from the two retrieval methods are never compared.
func documentRRF(lists ...[]Hit) []Hit {
	scores := make(map[string]Hit)
	for listIndex, list := range lists {
		seen := make(map[string]bool)
		for i, h := range list {
			k := documentKey(h)
			if seen[k] {
				continue
			}
			seen[k] = true
			old, ok := scores[k]
			if !ok {
				old = h
				old.Score = 0
			}
			if ok && listIndex > 0 {
				score := old.Score
				old = h
				old.Score = score
			}
			old.Score += 1 / float64(60+i+1)
			scores[k] = old
		}
	}
	out := make([]Hit, 0, len(scores))
	for _, h := range scores {
		out = append(out, h)
	}
	sortHits(out)
	return out
}

// Max 7*4=28 candidates, irrespective of requested limit; no section can consume
// the entire rerank budget with many paragraphs from the same document.
func groupedCandidates(hits []Hit) []Hit { return sectionCandidatesLimit(hits, sectionCandidates) }
func sectionCandidatesLimit(hits []Hit, maxPerSection int) []Hit {
	count := map[string]int{}
	seen := map[string]bool{}
	out := make([]Hit, 0, 28)
	for _, h := range hits {
		k := documentKey(h)
		section := hitSection(h)
		if seen[k] || count[section] >= maxPerSection {
			continue
		}
		seen[k] = true
		count[section]++
		out = append(out, withSection(h, section))
	}
	return out
}
func groupedResults(hits []Hit, limit int) []Hit {
	groups := map[string][]Hit{}
	order := []string{}
	seen := map[string]bool{}
	for _, h := range hits {
		section := hitSection(h)
		key := documentKey(h)
		if seen[key] || len(groups[section]) >= sectionResults {
			continue
		}
		seen[key] = true
		if len(groups[section]) == 0 {
			order = append(order, section)
		}
		groups[section] = append(groups[section], h)
	}
	// Reserve one result per relevant nonempty section before taking second/third.
	selected := map[string]int{}
	remaining := limit
	for round := 0; round < sectionResults && remaining > 0; round++ {
		for _, section := range order {
			if remaining == 0 {
				break
			}
			if len(groups[section]) > round {
				selected[section]++
				remaining--
			}
		}
	}
	out := make([]Hit, 0, limit)
	for _, section := range order {
		out = append(out, groups[section][:selected[section]]...)
	}
	return out
}

// Initial corpus-specific calibration, not a probability-of-truth claim. The
// 2026-10-26 full-corpus negative control peaked at 0.00326004; relevant Norway
// excerpts scored 0.0686–0.8139, irrelevant ones below 0.00132. Require both a
// conservative absolute floor and 5% of the best score, so near-zero ANN matches
// never acquire relevance merely because they are the best in an empty section.
// Apply only to successfully reranked grouped results, never raw BM25/RRF scores.
func relevantGrouped(hits []Hit) []Hit {
	best := 0.0
	for _, h := range hits {
		if h.Score > best {
			best = h.Score
		}
	}
	floor := max(0.01, best*0.05)
	out := make([]Hit, 0, len(hits))
	for _, h := range hits {
		if h.Score >= floor {
			out = append(out, h)
		}
	}
	return out
}
