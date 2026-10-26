package search

import (
	"context"
	"encoding/json"
	"math"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestDeepInfraWireNormalizationAndRerank(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer test-only" {
			t.Error("missing auth")
		}
		var body map[string]any
		if json.NewDecoder(r.Body).Decode(&body) != nil {
			t.Fatal("body")
		}
		switch r.URL.Path {
		case "/v1/openai/embeddings":
			if body["model"] != EmbeddingModel || body["input"] != QueryInstruction+"hello" {
				t.Error("embedding profile input changed")
			}
			v := make([]float64, 4096)
			v[0] = 3
			v[1] = 4
			v[1024] = 100
			json.NewEncoder(w).Encode(map[string]any{"data": []any{map[string]any{"index": 0, "embedding": v}}})
		case "/v1/inference/" + RerankModel:
			if len(body["queries"].([]any)) != 2 || body["queries"].([]any)[0] != "hello" || body["queries"].([]any)[1] != "hello" {
				t.Error("reranker needs one query per document")
			}
			if len(body["documents"].([]any)) != 2 {
				t.Error("documents")
			}
			json.NewEncoder(w).Encode(map[string]any{"scores": []float64{.2, .7}})
		default:
			t.Error("unexpected endpoint")
			w.WriteHeader(404)
		}
	}))
	defer server.Close()
	p := NewDeepInfra("test-only")
	p.BaseURL = server.URL
	v, e := p.Embed(context.Background(), "hello")
	if e != nil || len(v) != 1024 || math.Abs(float64(v[0])-.6) > 1e-6 || math.Abs(float64(v[1])-.8) > 1e-6 {
		t.Fatal("truncate then normalize", e)
	}
	scores, e := p.Rerank(context.Background(), "hello", []Hit{{Text: "one"}, {Text: "two"}})
	if e != nil || scores[1] != .7 {
		t.Fatal(scores, e)
	}
}
func TestProviderRejectsBadVectorsErrorsAndRedirects(t *testing.T) {
	for _, v := range [][]float64{nil, make([]float64, 1024), make([]float64, 4096)} {
		if _, e := NormalizeEmbedding(v); e == nil {
			t.Fatal("accepted invalid vector")
		}
	}
	v := make([]float64, 4096)
	v[0] = math.NaN()
	if _, e := NormalizeEmbedding(v); e == nil {
		t.Fatal("NaN")
	}
	for _, status := range []int{302, 429, 500} {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Location", "http://127.0.0.1:1/private")
			w.WriteHeader(status)
			w.Write([]byte("private secret query"))
		}))
		p := NewDeepInfra("test-only")
		p.BaseURL = server.URL
		_, e := p.Embed(context.Background(), "private query")
		server.Close()
		if e == nil || strings.Contains(e.Error(), "private") {
			t.Fatal("provider body leaked", e)
		}
	}
}
