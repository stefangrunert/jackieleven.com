package search

import (
	"context"
	"encoding/json"
	"fmt"
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
	if e != nil || len(out.Hits) != 3 || hitSection(out.Hits[0]) != "biography" {
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
func TestDocumentFusionRetainsEvidenceAndNoDuplicateCredit(t *testing.T) {
	original := Hit{ID: "p1", DocumentID: "doc", TextKind: "original", Text: "Exact original"}
	other := Hit{ID: "p2", DocumentID: "doc", TextKind: "summary", Text: "Summary"}
	out := documentRRF([]Hit{original, other}, []Hit{other})
	if len(out) != 1 || out[0].ID != "p1" || out[0].Text != "Exact original" || out[0].Score != 2.0/61 {
		t.Fatal(out)
	}
}
