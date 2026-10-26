package search

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type groupedRepo struct {
	fakeRepo
	mu       sync.Mutex
	sections []string
	block    bool
}

func (r *groupedRepo) rows(ctx context.Context, q Query) ([]Hit, error) {
	r.mu.Lock()
	r.sections = append(r.sections, q.Section)
	r.mu.Unlock()
	if r.block {
		<-ctx.Done()
		return nil, ErrUnavailable
	}
	if q.Section == "site" {
		return []Hit{}, nil
	}
	out := []Hit{}
	for i := 0; i < 16; i++ {
		metadata, _ := json.Marshal(map[string]any{"section": q.Section})
		out = append(out, Hit{ID: fmt.Sprintf("%s-%02d", q.Section, i), DocumentID: fmt.Sprintf("%s-doc-%02d", q.Section, i/2), Text: "source excerpt", Language: "en", TextKind: "original", Score: float64(100 - i), Metadata: metadata})
	}
	return out, nil
}
func (r *groupedRepo) Lexical(ctx context.Context, m Manifest, q Query, n int) ([]Hit, error) {
	return r.rows(ctx, q)
}
func (r *groupedRepo) Semantic(ctx context.Context, m Manifest, q Query, v []float32, n int) ([]Hit, error) {
	return r.rows(ctx, q)
}

type groupedProvider struct {
	calls      atomic.Int32
	rerankSize atomic.Int32
	slow       bool
}

func (p *groupedProvider) Embed(context.Context, string) ([]float32, error) {
	p.calls.Add(1)
	v := make([]float32, 1024)
	v[0] = 1
	return v, nil
}
func (p *groupedProvider) Rerank(ctx context.Context, q string, hits []Hit) ([]float64, error) {
	p.rerankSize.Store(int32(len(hits)))
	if p.slow {
		<-ctx.Done()
		return nil, errProvider
	}
	scores := make([]float64, len(hits))
	for i := range scores {
		scores[i] = float64(len(hits) - i)
	}
	return scores, nil
}
func TestGroupedDiversityBudgetAndOneEmbedding(t *testing.T) {
	repo := &groupedRepo{}
	p := &groupedProvider{}
	s, _ := New(testManifest(), repo, p, DefaultOptions())
	q := query()
	q.Grouped = true
	q.Rerank = true
	out, e := s.Search(context.Background(), q)
	if e != nil || out.Mode != "hybrid" || !out.Reranked || out.Degraded {
		t.Fatal(out, e)
	}
	if p.calls.Load() != 1 || p.rerankSize.Load() > 28 {
		t.Fatal("external budget", p.calls.Load(), p.rerankSize.Load())
	}
	seen := map[string]bool{}
	counts := map[string]int{}
	for _, h := range out.Hits {
		if seen[h.DocumentID] {
			t.Fatal("duplicate document", h.DocumentID)
		}
		seen[h.DocumentID] = true
		counts[hitSection(h)]++
	}
	if len(out.Hits) != 15 || len(counts) != 5 {
		t.Fatal("expected five populated factual sections, three docs each", len(out.Hits), counts)
	}
	for _, n := range counts {
		if n != 3 {
			t.Fatal("section limit", counts)
		}
	}
	repo.mu.Lock()
	defer repo.mu.Unlock()
	for _, section := range repo.sections {
		if section == "biography" {
			t.Fatal("automatic section split opted into fiction")
		}
	}
}
func TestGroupedSmallLimitSectionOptInAndDeadline(t *testing.T) {
	repo := &groupedRepo{}
	s, _ := New(testManifest(), repo, nil, DefaultOptions())
	q := query()
	q.Grouped = true
	q.Limit = 2
	q.Mode = "lexical"
	out, e := s.Search(context.Background(), q)
	if e != nil || len(out.Hits) != 2 || hitSection(out.Hits[0]) == hitSection(out.Hits[1]) {
		t.Fatal("small limit must preserve diversity", out, e)
	}
	q.Section = "biography"
	q.Limit = 20
	out, e = s.Search(context.Background(), q)
	if e != nil || len(out.Hits) != 8 || hitSection(out.Hits[0]) != "biography" {
		t.Fatal("explicit fiction section", out, e)
	}
	o := DefaultOptions()
	o.RequestTimeout = 20 * time.Millisecond
	blocked := &groupedRepo{block: true}
	s, _ = New(testManifest(), blocked, nil, o)
	q.Section = ""
	start := time.Now()
	_, e = s.Search(context.Background(), q)
	if e != ErrUnavailable || time.Since(start) > time.Second {
		t.Fatal("grouped queries ignored shared deadline", e)
	}
}
func TestGroupedRerankTimeoutPreservesResults(t *testing.T) {
	o := DefaultOptions()
	o.RerankTimeout = 10 * time.Millisecond
	o.RequestTimeout = time.Second
	p := &groupedProvider{slow: true}
	s, _ := New(testManifest(), &groupedRepo{}, p, o)
	q := query()
	q.Grouped = true
	q.Rerank = true
	out, e := s.Search(context.Background(), q)
	if e != nil || len(out.Hits) == 0 || !out.Degraded || out.Reranked || out.Reason != "rerank_unavailable" {
		t.Fatal(out, e)
	}
}
func TestDocumentFusionChoosesQuerySpecificEvidenceAndNoDuplicateCredit(t *testing.T) {
	original := Hit{ID: "p1", DocumentID: "doc", TextKind: "original", Text: "Exact original"}
	other := Hit{ID: "p2", DocumentID: "doc", TextKind: "summary", Text: "Summary"}
	out := documentRRF([]Hit{original, other}, []Hit{other})
	if len(out) != 1 || out[0].ID != "p2" || out[0].Text != "Summary" || out[0].Score != 2.0/61 {
		t.Fatal(out)
	}
}

func TestLegacySectionFallbackIsVisible(t *testing.T) {
	hits := groupedCandidates([]Hit{{ID: "legacy", DocumentID: "old", Metadata: json.RawMessage(`{"image":"cover.jpg","fiction":false}`)}})
	var metadata map[string]any
	if len(hits) != 1 || json.Unmarshal(hits[0].Metadata, &metadata) != nil || metadata["section"] != "site" || metadata["image"] != "cover.jpg" {
		t.Fatal("legacy section fallback lost metadata", hits)
	}
}

func TestExpandedSectionRerankLimit(t *testing.T) {
	hits := []Hit{}
	for i := 0; i < 60; i++ {
		hits = append(hits, Hit{ID: fmt.Sprint(i), DocumentID: fmt.Sprint(i), Metadata: json.RawMessage(`{"section":"music"}`)})
	}
	if got := len(sectionCandidatesLimit(hits, 28)); got != 28 {
		t.Fatal("expanded rerank cap", got)
	}
}

func TestGroupedRelevanceCalibration(t *testing.T) {
	hits := []Hit{{ID: "norway", Score: 0.81387991}, {ID: "tromso", Score: 0.06859533}, {ID: "italy", Score: 0.00131617}, {ID: "blossom", Score: 0.00001297}}
	got := relevantGrouped(hits)
	if len(got) != 2 || got[0].ID != "norway" || got[1].ID != "tromso" {
		t.Fatal(got)
	}
	if got := relevantGrouped([]Hit{{ID: "negative-control", Score: 0.00326004}}); len(got) != 0 {
		t.Fatal(got)
	}
	if got := relevantGrouped([]Hit{{ID: "boundary", Score: 0.01}}); len(got) != 1 {
		t.Fatal(got)
	}
	if got := relevantGrouped(nil); got == nil {
		t.Fatal("empty JSON array required")
	}
}

type semanticOnlyGroupedRepo struct{ groupedRepo }

func (r *semanticOnlyGroupedRepo) Lexical(context.Context, Manifest, Query, int) ([]Hit, error) {
	return []Hit{}, nil
}
func TestGroupedFailedRerankDoesNotInventMatchingSections(t *testing.T) {
	o := DefaultOptions()
	o.RerankTimeout = time.Millisecond
	for _, mode := range []string{"hybrid", "semantic"} {
		s, _ := New(testManifest(), &semanticOnlyGroupedRepo{}, &groupedProvider{slow: true}, o)
		q := query()
		q.Grouped = true
		q.Rerank = true
		q.Mode = mode
		out, e := s.Search(context.Background(), q)
		if e != nil || len(out.Hits) != 0 || !out.Degraded || out.Mode != "lexical" || out.Reranked {
			t.Fatal(mode, out, e)
		}
	}
}

// This replays recorded scores, not external API calls. The JSON separately
// records the five genuine before/after checks and their corpus versions.
func TestRecordedNegativeControlCannotPopulateSections(t *testing.T) {
	raw, e := os.ReadFile("testdata/grouped-quality-2026-10-26.json")
	if e != nil {
		t.Fatal(e)
	}
	var evidence struct {
		Before []struct {
			Query string `json:"query"`
			Hits  []Hit  `json:"hits"`
		} `json:"before"`
	}
	if e = json.Unmarshal(raw, &evidence); e != nil {
		t.Fatal(e)
	}
	if len(evidence.Before) != 2 || len(evidence.Before[1].Hits) != 18 {
		t.Fatal("missing full negative-control evidence")
	}
	if got := relevantGrouped(evidence.Before[1].Hits); len(got) != 0 {
		t.Fatal("negative control admitted", got)
	}
}

type inspectRepresentativeProvider struct {
	fakeProvider
	seen []Hit
}

func (p *inspectRepresentativeProvider) Rerank(_ context.Context, _ string, hits []Hit) ([]float64, error) {
	p.seen = append([]Hit(nil), hits...)
	scores := make([]float64, len(hits))
	for i := range scores {
		scores[i] = 0.46
	}
	return scores, nil
}
func TestRerankerReceivesRelevantBodyInsteadOfRepeatedTitleTie(t *testing.T) {
	meta := json.RawMessage(`{"section":"writing"}`)
	irrelevant := Hit{ID: "blossom", DocumentID: "bergen-blog", Title: "An evening flight to Bergen in Norway", Text: "In Spring there is apple blossom.", TextKind: "original", Metadata: meta, Score: 7.75}
	relevant := Hit{ID: "festival", DocumentID: "bergen-blog", Title: irrelevant.Title, Text: "An evening flight from Gatwick to Bergen in Norway for a literary festival the next day in Odda.", TextKind: "original", Metadata: meta, Score: 0.73}
	repo := &fakeRepo{lex: []Hit{irrelevant}, sem: []Hit{relevant}}
	provider := &inspectRepresentativeProvider{}
	service, _ := New(testManifest(), repo, provider, DefaultOptions())
	q := query()
	q.Text = "konzerte in norwegen"
	q.Grouped = true
	q.Rerank = true
	q.Section = "writing"
	out, e := service.Search(context.Background(), q)
	if e != nil || len(provider.seen) != 1 || provider.seen[0].ID != "festival" || len(out.Hits) != 1 || out.Hits[0].Text != relevant.Text || !out.Reranked {
		t.Fatal(out, e, provider.seen)
	}
}

type lowScoreProvider struct{ fakeProvider }

func (p *lowScoreProvider) Rerank(_ context.Context, _ string, hits []Hit) ([]float64, error) {
	scores := make([]float64, len(hits))
	for i := range scores {
		scores[i] = 0.001
	}
	return scores, nil
}
func TestGroupedRelevanceGateDoesNotChangeTechnicalUngroupedSearch(t *testing.T) {
	repo := &fakeRepo{lex: []Hit{{ID: "a", DocumentID: "a", Text: "Excerpt", Metadata: json.RawMessage(`{"section":"writing"}`)}}}
	service, _ := New(testManifest(), repo, &lowScoreProvider{}, DefaultOptions())
	q := query()
	q.Mode = "lexical"
	q.Rerank = true
	q.Section = "writing"
	out, e := service.Search(context.Background(), q)
	if e != nil || len(out.Hits) != 1 || !out.Reranked {
		t.Fatal("ungrouped semantics changed", out, e)
	}
	q.Grouped = true
	out, e = service.Search(context.Background(), q)
	if e != nil || len(out.Hits) != 0 || !out.Reranked {
		t.Fatal("grouped weak relevance not removed", out, e)
	}
}
