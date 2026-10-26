package search

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"math"
	"net/http"
	"strings"
	"time"
)

var errProvider = errors.New("provider unavailable")

// DeepInfra uses the documented embeddings and native reranker HTTP endpoints.
// Errors intentionally contain neither response bodies, query text, nor keys.
type DeepInfra struct {
	Key, BaseURL string
	Client       *http.Client
	slots        chan struct{}
}

func NewDeepInfra(key string) *DeepInfra {
	return &DeepInfra{Key: key, BaseURL: "https://api.deepinfra.com", Client: &http.Client{Timeout: 10 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}, slots: make(chan struct{}, 2)}
}
func (p *DeepInfra) post(ctx context.Context, path string, body, out any) error {
	select {
	case p.slots <- struct{}{}:
		defer func() { <-p.slots }()
	default:
		return errProvider
	}
	data, e := json.Marshal(body)
	if e != nil || len(data) > 300000 {
		return errProvider
	}
	req, e := http.NewRequestWithContext(ctx, "POST", strings.TrimRight(p.BaseURL, "/")+path, bytes.NewReader(data))
	if e != nil {
		return errProvider
	}
	req.Header.Set("Authorization", "Bearer "+p.Key)
	req.Header.Set("Content-Type", "application/json")
	res, e := p.Client.Do(req)
	if e != nil {
		return errProvider
	}
	defer res.Body.Close()
	if res.StatusCode != 200 {
		return errProvider
	}
	raw, e := io.ReadAll(io.LimitReader(res.Body, 1<<20+1))
	if e != nil || len(raw) > 1<<20 {
		return errProvider
	}
	if json.Unmarshal(raw, out) != nil {
		return errProvider
	}
	return nil
}
func NormalizeEmbedding(v []float64) ([]float32, error) {
	if len(v) != 4096 {
		return nil, errProvider
	}
	var norm float64
	for i, x := range v {
		if math.IsNaN(x) || math.IsInf(x, 0) {
			return nil, errProvider
		}
		if i < 1024 {
			norm += x * x
		}
	}
	if norm == 0 || math.IsInf(norm, 0) {
		return nil, errProvider
	}
	norm = math.Sqrt(norm)
	out := make([]float32, 1024)
	for i := range out {
		out[i] = float32(v[i] / norm)
	}
	return out, nil
}
func (p *DeepInfra) Embed(ctx context.Context, q string) ([]float32, error) {
	var out struct {
		Data []struct {
			Index     int       `json:"index"`
			Embedding []float64 `json:"embedding"`
		} `json:"data"`
	}
	if p.post(ctx, "/v1/openai/embeddings", map[string]any{"model": EmbeddingModel, "input": QueryInstruction + q, "encoding_format": "float"}, &out) != nil || len(out.Data) != 1 || out.Data[0].Index != 0 {
		return nil, errProvider
	}
	return NormalizeEmbedding(out.Data[0].Embedding)
}
func (p *DeepInfra) Rerank(ctx context.Context, q string, hits []Hit) ([]float64, error) {
	docs := make([]string, len(hits))
	for i, h := range hits {
		docs[i] = h.Text
	}
	var out struct {
		Scores []float64 `json:"scores"`
	}
	if p.post(ctx, "/v1/inference/"+RerankModel, map[string]any{"queries": []string{q}, "documents": docs}, &out) != nil || len(out.Scores) != len(hits) {
		return nil, errProvider
	}
	for _, x := range out.Scores {
		if math.IsNaN(x) || math.IsInf(x, 0) {
			return nil, errProvider
		}
	}
	return out.Scores, nil
}
