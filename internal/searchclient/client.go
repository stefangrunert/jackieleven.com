// Package searchclient is the website's bounded, snapshot-pinned search adapter.
// It has no database or provider credentials and never logs request text.
package searchclient

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

const MaxQueryBytes = 1024
const maxResponseBytes = 4 << 20

// Manifest identifies the immutable corpus selected at process startup.
type Manifest struct {
	APIVersion       string `json:"api_version"`
	BuildID          string `json:"build_id"`
	ContentVersion   string `json:"content_version"`
	DataVersion      string `json:"data_version"`
	EmbeddingProfile string `json:"embedding_profile"`
	PassageCount     int    `json:"passage_count"`
	DocumentCount    int    `json:"document_count"`
}
type Versions struct {
	APIVersion     string `json:"api_version"`
	ContentVersion string `json:"content_version"`
	DataVersion    string `json:"data_version"`
	SearchRelease  string `json:"search_release"`
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
type SearchResponse struct {
	Versions
	Mode       string  `json:"mode"`
	Degraded   bool    `json:"degraded"`
	Reranked   bool    `json:"reranked"`
	Reason     string  `json:"reason,omitempty"`
	DurationMS float64 `json:"duration_ms"`
	Hits       []Hit   `json:"hits"`
}
type PassageResponse struct {
	Versions
	Passage Hit `json:"passage"`
}

// Error deliberately excludes URLs, queries and upstream error bodies.
type Error struct {
	Status int
	Code   string
}

func (e *Error) Error() string              { return "search: " + e.Code }
func failure(status int, code string) error { return &Error{Status: status, Code: code} }

type Client struct {
	base     string
	manifest Manifest
	http     *http.Client
}

func New(endpoint, manifestPath string) (*Client, error) {
	u, err := url.Parse(endpoint)
	if err != nil || u.Scheme != "http" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
		return nil, errors.New("search: endpoint must be a loopback HTTP origin")
	}
	host := u.Hostname()
	if host == "localhost" {
		host = "127.0.0.1"
	}
	ip := net.ParseIP(host)
	if ip == nil || !ip.IsLoopback() {
		return nil, errors.New("search: endpoint must use a loopback address")
	}
	port := u.Port()
	if port == "" {
		port = "80"
	}
	u.Host = net.JoinHostPort(host, port)
	u.Path = ""
	f, err := os.Open(manifestPath)
	if err != nil {
		return nil, errors.New("search: cannot open manifest")
	}
	defer f.Close()
	var m Manifest
	if err := decodeBounded(f, 64<<10, &m); err != nil {
		return nil, errors.New("search: invalid manifest JSON")
	}
	if m.APIVersion != "v1" || m.BuildID == "" || m.ContentVersion == "" || m.DataVersion == "" || m.EmbeddingProfile == "" || m.PassageCount < 0 || m.DocumentCount < 0 || len(m.ContentVersion) > 256 || strings.ContainsAny(m.ContentVersion, "\r\n") {
		return nil, errors.New("search: incompatible or incomplete manifest")
	}
	transport := &http.Transport{
		Proxy:        nil,
		DialContext:  (&net.Dialer{Timeout: 2 * time.Second, KeepAlive: 30 * time.Second}).DialContext,
		MaxIdleConns: 8, MaxIdleConnsPerHost: 8, MaxConnsPerHost: 16,
		IdleConnTimeout: 30 * time.Second, ResponseHeaderTimeout: 7 * time.Second,
		MaxResponseHeaderBytes: 32 << 10,
	}
	return &Client{base: u.String(), manifest: m, http: &http.Client{Transport: transport, Timeout: 7 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}}, nil
}
func (c *Client) Manifest() Manifest { return c.manifest }

func decodeBounded(r io.Reader, limit int64, target any) error {
	b, err := io.ReadAll(io.LimitReader(r, limit+1))
	if err != nil || int64(len(b)) > limit {
		return errors.New("response size")
	}
	return json.Unmarshal(b, target)
}
func (c *Client) get(ctx context.Context, path string, values url.Values, target any) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.base+path+"?"+values.Encode(), nil)
	if err != nil {
		return failure(503, "unavailable")
	}
	req.Header.Set("X-Archive-Content-Version", c.manifest.ContentVersion)
	req.Header.Set("Accept", "application/json")
	res, err := c.http.Do(req)
	if err != nil {
		return failure(503, "unavailable")
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		switch res.StatusCode {
		case 400:
			return failure(400, "invalid_query")
		case 404:
			return failure(404, "not_found")
		case 409:
			return failure(409, "version_mismatch")
		case 429:
			return failure(429, "capacity")
		default:
			return failure(503, "unavailable")
		}
	}
	if err := decodeBounded(res.Body, maxResponseBytes, target); err != nil {
		return failure(503, "invalid_response")
	}
	return nil
}
func (c *Client) check(v Versions) error {
	if v.ContentVersion != c.manifest.ContentVersion || v.DataVersion != c.manifest.DataVersion {
		return failure(409, "version_mismatch")
	}
	if v.APIVersion != "v1" || v.SearchRelease == "" {
		return failure(503, "invalid_response")
	}
	return nil
}
func (c *Client) Search(ctx context.Context, values url.Values) (*SearchResponse, error) {
	if len(values.Get("q")) > MaxQueryBytes {
		return nil, failure(400, "invalid_query")
	}
	// Never forward arbitrary public query parameters such as a build selector.
	allowed := url.Values{}
	for _, key := range []string{"q", "lang", "mode", "voice", "from", "to", "rerank"} {
		if value := values.Get(key); value != "" {
			allowed.Set(key, value)
		}
	}
	allowed.Set("limit", "20")
	var result SearchResponse
	if err := c.get(ctx, "/v1/search", allowed, &result); err != nil {
		return nil, err
	}
	if err := c.check(result.Versions); err != nil {
		return nil, err
	}
	if (result.Mode != "lexical" && result.Mode != "semantic" && result.Mode != "hybrid") || len(result.Hits) > 50 || result.Hits == nil || result.DurationMS < 0 {
		return nil, failure(503, "invalid_response")
	}
	for _, hit := range result.Hits {
		if hit.ID == "" || hit.DocumentID == "" || hit.Text == "" {
			return nil, failure(503, "invalid_response")
		}
	}
	return &result, nil
}
func (c *Client) Passage(ctx context.Context, id, lang string) (*PassageResponse, error) {
	if id == "" || len(id) > 1024 {
		return nil, failure(400, "invalid_query")
	}
	var result PassageResponse
	if err := c.get(ctx, "/v1/passages", url.Values{"id": {id}, "lang": {lang}}, &result); err != nil {
		return nil, err
	}
	if err := c.check(result.Versions); err != nil {
		return nil, err
	}
	if result.Passage.ID != id || result.Passage.DocumentID == "" || result.Passage.Text == "" {
		return nil, failure(503, "invalid_response")
	}
	return &result, nil
}
