// Package search provides retrieval bound to one immutable archive snapshot.
package search

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"os"
	"strings"
	"unicode"
	"unicode/utf8"
)

const EmbeddingProfile = "qwen3-8b-1024-v1"
const EmbeddingModel = "Qwen/Qwen3-Embedding-8B"
const RerankModel = "Qwen/Qwen3-Reranker-8B"
const QueryInstruction = "Instruct: Given a question about the Scottish songwriter Jackie Leven, retrieve passages from his own writing, press coverage, concert history and discography that answer it\nQuery: "
const Release = "search-v1"

var (
	ErrUnavailable = errors.New("search unavailable")
	ErrNotFound    = errors.New("not found")
	ErrCapacity    = errors.New("capacity exhausted")
	ErrInvalid     = errors.New("invalid query")
)

type Manifest struct {
	APIVersion       string `json:"api_version"`
	BuildID          string `json:"build_id"`
	ContentVersion   string `json:"content_version"`
	DataVersion      string `json:"data_version"`
	EmbeddingProfile string `json:"embedding_profile"`
	PassageCount     int    `json:"passage_count"`
	DocumentCount    int    `json:"document_count"`
}

func (m Manifest) Validate() error {
	if m.APIVersion != "v1" || m.BuildID == "" || m.ContentVersion == "" || m.DataVersion == "" || (m.EmbeddingProfile != "none" && m.EmbeddingProfile != EmbeddingProfile) || m.PassageCount < 0 || m.DocumentCount < 0 {
		return ErrInvalid
	}
	return nil
}
func LoadManifest(path string) (Manifest, error) {
	var m Manifest
	f, e := os.Open(path)
	if e != nil {
		return m, ErrInvalid
	}
	defer f.Close()
	d := json.NewDecoder(io.LimitReader(f, 65537))
	if d.Decode(&m) != nil || d.Decode(new(any)) != io.EOF {
		return m, ErrInvalid
	}
	return m, m.Validate()
}

type Versions struct {
	APIVersion     string `json:"api_version"`
	ContentVersion string `json:"content_version"`
	DataVersion    string `json:"data_version"`
	SearchRelease  string `json:"search_release"`
}

func (m Manifest) Versions() Versions {
	return Versions{"v1", m.ContentVersion, m.DataVersion, Release}
}

type Hit struct {
	ID          string          `json:"id"`
	DocumentID  string          `json:"document_id"`
	Title       string          `json:"title"`
	Text        string          `json:"text"`
	Language    string          `json:"language"`
	SourceVoice string          `json:"source_voice"`
	TextVoice   string          `json:"text_voice"`
	TextKind    string          `json:"text_kind"`
	URL         string          `json:"url"`
	Score       float64         `json:"score"`
	Metadata    json.RawMessage `json:"metadata,omitempty"`
}
type Query struct {
	Text, Language, Mode, Voice, Section string
	Limit                                int
	From, To                             *int
	Rerank                               bool
	Grouped                              bool
}

func (q Query) Validate() error {
	if strings.TrimSpace(q.Text) == "" || len(q.Text) > 1024 || !utf8.ValidString(q.Text) || q.Limit < 1 || q.Limit > 50 || (q.Language != "de" && q.Language != "en") || (q.Mode != "lexical" && q.Mode != "semantic" && q.Mode != "hybrid") {
		return ErrInvalid
	}
	for _, r := range q.Text {
		if unicode.IsControl(r) {
			return ErrInvalid
		}
	}
	if q.Section != "" && !validSection(q.Section) {
		return ErrInvalid
	}
	switch q.Voice {
	case "", "leven", "third_party", "editorial", "pastiche":
	default:
		return ErrInvalid
	}
	if (q.From != nil && (*q.From < 1 || *q.From > 9999)) || (q.To != nil && (*q.To < 1 || *q.To > 9999)) || (q.From != nil && q.To != nil && *q.From > *q.To) {
		return ErrInvalid
	}
	return nil
}

type Response struct {
	Versions
	Mode       string `json:"mode"`
	Degraded   bool   `json:"degraded"`
	Reason     string `json:"reason,omitempty"`
	Reranked   bool   `json:"reranked"`
	DurationMS int64  `json:"duration_ms"`
	Hits       []Hit  `json:"hits"`
}
type PassageResponse struct {
	Versions
	Passage Hit `json:"passage"`
}
type EntityResponse struct {
	Versions
	Entity json.RawMessage `json:"entity"`
}
type Repository interface {
	Ready(context.Context, Manifest) error
	Lexical(context.Context, Manifest, Query, int) ([]Hit, error)
	Semantic(context.Context, Manifest, Query, []float32, int) ([]Hit, error)
	Passage(context.Context, Manifest, string, string) (Hit, error)
	Entity(context.Context, Manifest, string) (json.RawMessage, error)
}
type Provider interface {
	Embed(context.Context, string) ([]float32, error)
	Rerank(context.Context, string, []Hit) ([]float64, error)
}
