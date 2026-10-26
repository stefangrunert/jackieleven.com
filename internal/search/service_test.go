package search

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func testManifest() Manifest {
	return Manifest{"v1", "test-build", "test-content", "test-data", EmbeddingProfile, 2, 1}
}

type fakeRepo struct {
	lex, sem []Hit
	fail     error
	block    <-chan struct{}
}

func (r *fakeRepo) Ready(ctx context.Context, m Manifest) error {
	if r.block != nil {
		select {
		case <-r.block:
		case <-ctx.Done():
			return ErrUnavailable
		}
	}
	return r.fail
}
func (r *fakeRepo) Lexical(context.Context, Manifest, Query, int) ([]Hit, error) {
	return append([]Hit(nil), r.lex...), r.fail
}
func (r *fakeRepo) Semantic(context.Context, Manifest, Query, []float32, int) ([]Hit, error) {
	return append([]Hit(nil), r.sem...), r.fail
}
func (r *fakeRepo) Passage(context.Context, Manifest, string, string) (Hit, error) {
	if len(r.lex) == 0 {
		return Hit{}, ErrNotFound
	}
	return r.lex[0], r.fail
}
func (r *fakeRepo) Entity(context.Context, Manifest, string) (json.RawMessage, error) {
	return json.RawMessage(`{"id":"person"}`), r.fail
}

type fakeProvider struct {
	calls atomic.Int32
	fail  bool
	slow  bool
}

func (p *fakeProvider) Embed(ctx context.Context, q string) ([]float32, error) {
	p.calls.Add(1)
	if p.slow {
		<-ctx.Done()
		return nil, ctx.Err()
	}
	if p.fail {
		return nil, errProvider
	}
	v := make([]float32, 1024)
	v[0] = 1
	return v, nil
}
func (p *fakeProvider) Rerank(context.Context, string, []Hit) ([]float64, error) {
	if p.fail {
		return nil, errProvider
	}
	return []float64{.1, .9}, nil
}
func query() Query { return Query{Text: "Jackie Leven", Language: "de", Mode: "hybrid", Limit: 20} }
func TestFusionFallbackAndCache(t *testing.T) {
	r := &fakeRepo{lex: []Hit{{ID: "a", Text: "first"}, {ID: "b", Text: "second"}}, sem: []Hit{{ID: "b", Text: "second"}, {ID: "c", Text: "third"}}}
	p := &fakeProvider{}
	s, _ := New(testManifest(), r, p, DefaultOptions())
	out, e := s.Search(context.Background(), query())
	if e != nil || out.Mode != "hybrid" || out.Hits[0].ID != "b" || out.Degraded {
		t.Fatalf("bad fusion: %+v %v", out, e)
	}
	_, _ = s.Search(context.Background(), query())
	if p.calls.Load() != 1 {
		t.Fatal("query embedding not cached")
	}
	p.fail = true
	q := query()
	q.Text = "another"
	out, e = s.Search(context.Background(), q)
	if e != nil || out.Mode != "lexical" || !out.Degraded || out.Reason != "embedding_unavailable" {
		t.Fatalf("bad fallback %+v %v", out, e)
	}
	r.fail = errors.New("private SQL detail")
	_, e = s.Search(context.Background(), q)
	if e != ErrUnavailable {
		t.Fatal("DB failure must not masquerade as no hits")
	}
}
func TestExternalOffProfileAndExactPassage(t *testing.T) {
	full := strings.Repeat("ü", 1500)
	r := &fakeRepo{lex: []Hit{{ID: "p", Text: full}}}
	m := testManifest()
	m.EmbeddingProfile = "none"
	s, _ := New(m, r, nil, DefaultOptions())
	q := query()
	q.Mode = "semantic"
	out, e := s.Search(context.Background(), q)
	if e != nil || out.Mode != "lexical" || out.Reason != "embedding_profile_none" || len([]rune(out.Hits[0].Text)) != 1201 {
		t.Fatal(out, e)
	}
	passage, e := s.Passage(context.Background(), "p", "de")
	if e != nil || passage.Passage.Text != full {
		t.Fatal("passage must preserve exact stored text")
	}
}
func TestProviderDeadlineAndCapacity(t *testing.T) {
	o := DefaultOptions()
	o.ProviderTimeout = 10 * time.Millisecond
	o.RequestTimeout = time.Second
	o.MaxConcurrent = 1
	s, _ := New(testManifest(), &fakeRepo{lex: []Hit{}}, &fakeProvider{slow: true}, o)
	out, e := s.Search(context.Background(), query())
	if e != nil || !out.Degraded || out.Hits == nil {
		t.Fatal(out, e)
	}
	gate := make(chan struct{})
	s, _ = New(testManifest(), &fakeRepo{block: gate}, nil, o)
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- s.Ready(ctx) }()
	for i := 0; i < 100 && len(s.slots) == 0; i++ {
		time.Sleep(time.Millisecond)
	}
	if e := s.Ready(context.Background()); e != ErrCapacity {
		t.Fatal("capacity not bounded", e)
	}
	cancel()
	<-done
}
func TestRerankAndCacheBound(t *testing.T) {
	p := &fakeProvider{}
	o := DefaultOptions()
	o.CacheEntries = 1
	s, _ := New(testManifest(), &fakeRepo{lex: []Hit{{ID: "a"}, {ID: "b"}}}, p, o)
	q := query()
	q.Mode = "lexical"
	q.Rerank = true
	out, e := s.Search(context.Background(), q)
	if e != nil || !out.Reranked || out.Hits[0].ID != "b" {
		t.Fatal(out, e)
	}
	q.Mode = "semantic"
	q.Rerank = false
	_, _ = s.Search(context.Background(), q)
	q.Text = "second"
	_, _ = s.Search(context.Background(), q)
	if len(s.cache) != 1 {
		t.Fatal("unbounded cache")
	}
}
func TestQueryValidation(t *testing.T) {
	for _, v := range []Query{{Text: "x", Language: "de", Mode: "lexical", Limit: 51}, {Text: "x\nsecret", Language: "de", Mode: "lexical", Limit: 1}, {Text: "x", Language: "fr", Mode: "lexical", Limit: 1}} {
		if v.Validate() != ErrInvalid {
			t.Fatal(v)
		}
	}
}
