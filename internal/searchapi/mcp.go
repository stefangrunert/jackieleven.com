package searchapi

import (
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net"
	"net/http"
	"net/url"
	"strconv"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"jackieleven/internal/search"
)

type mcpSearchInput struct {
	Query    string `json:"q" jsonschema:"Search query, maximum 1024 UTF-8 bytes"`
	Language string `json:"lang,omitempty" jsonschema:"Original link language de or en, defaults to de"`
	Mode     string `json:"mode,omitempty" jsonschema:"lexical, semantic or hybrid; defaults to hybrid; semantic and hybrid send the query to DeepInfra"`
	Limit    int    `json:"limit,omitempty" jsonschema:"1 to 50, defaults to 20"`
	Voice    string `json:"voice,omitempty" jsonschema:"Actual text voice: leven, third_party, editorial, pastiche"`
	From     *int   `json:"from,omitempty" jsonschema:"Inclusive publication year"`
	To       *int   `json:"to,omitempty" jsonschema:"Inclusive publication year"`
	Rerank   bool   `json:"rerank,omitempty" jsonschema:"Optional external reranking, default false"`
}
type mcpPassageInput struct {
	ID       string `json:"id"`
	Language string `json:"lang,omitempty"`
}
type mcpEntityInput struct {
	ID string `json:"id"`
}

func structured(v any, e error) (*mcp.CallToolResult, map[string]any, error) {
	if e != nil {
		return nil, nil, e
	}
	raw, e := json.Marshal(v)
	if e != nil {
		return nil, nil, search.ErrUnavailable
	}
	var out map[string]any
	if json.Unmarshal(raw, &out) != nil {
		return nil, nil, search.ErrUnavailable
	}
	return nil, out, nil
}

// NewWithMCP enables the optional local-only, read-only streamable HTTP adapter.
// The adapter supplies the pinned manifest, just like the website's public facade.
func NewWithMCP(s *search.Service, timeout time.Duration) http.Handler {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	server := mcp.NewServer(&mcp.Implementation{Name: "jackieleven-archive", Version: search.Release}, &mcp.ServerOptions{Logger: logger, Instructions: "Search results distinguish source and text voices. Fetch a passage before quoting. URLs point to original documents, not fabricated anchors. Results include the pinned content version. Semantic and hybrid modes send the query to DeepInfra; reranking also sends excerpts. Lexical mode without reranking stays local."})
	readonly := &mcp.ToolAnnotations{ReadOnlyHint: true}
	mcp.AddTool(server, &mcp.Tool{Name: "search", Description: "Search the pinned Jackie Leven archive snapshot, preserving voices and provenance. Semantic/hybrid send queries to DeepInfra; reranking also sends excerpts. Use lexical without reranking for local-only retrieval.", Annotations: readonly}, func(ctx context.Context, r *mcp.CallToolRequest, in mcpSearchInput) (*mcp.CallToolResult, map[string]any, error) {
		v := url.Values{"q": {in.Query}}
		if in.Language != "" {
			v.Set("lang", in.Language)
		}
		if in.Mode != "" {
			v.Set("mode", in.Mode)
		}
		if in.Limit != 0 {
			v.Set("limit", strconv.Itoa(in.Limit))
		}
		if in.Voice != "" {
			v.Set("voice", in.Voice)
		}
		if in.From != nil {
			v.Set("from", strconv.Itoa(*in.From))
		}
		if in.To != nil {
			v.Set("to", strconv.Itoa(*in.To))
		}
		if in.Rerank {
			v.Set("rerank", "1")
		}
		q, e := parseQuery(v)
		if e != nil {
			return nil, nil, e
		}
		out, e := s.Search(ctx, q)
		return structured(out, e)
	})
	mcp.AddTool(server, &mcp.Tool{Name: "get_passage", Description: "Fetch exact stored passage text with its document link and evidence metadata.", Annotations: readonly}, func(ctx context.Context, r *mcp.CallToolRequest, in mcpPassageInput) (*mcp.CallToolResult, map[string]any, error) {
		lang := in.Language
		if lang == "" {
			lang = "de"
		}
		out, e := s.Passage(ctx, in.ID, lang)
		return structured(out, e)
	})
	mcp.AddTool(server, &mcp.Tool{Name: "get_entity", Description: "Fetch an exported entity and provenance from the pinned archive snapshot.", Annotations: readonly}, func(ctx context.Context, r *mcp.CallToolRequest, in mcpEntityInput) (*mcp.CallToolResult, map[string]any, error) {
		out, e := s.Entity(ctx, in.ID)
		return structured(out, e)
	})
	transport := mcp.NewStreamableHTTPHandler(func(*http.Request) *mcp.Server { return server }, &mcp.StreamableHTTPOptions{Stateless: true, JSONResponse: true, Logger: logger})
	slots := make(chan struct{}, 8)
	bounded := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		host, _, e := net.SplitHostPort(r.Host)
		if e != nil {
			host = r.Host
		}
		ip := net.ParseIP(host)
		if ip == nil || !ip.IsLoopback() {
			failure(w, 403, "forbidden", "Loopback host required")
			return
		}
		if origin := r.Header.Get("Origin"); origin != "" {
			u, e := url.Parse(origin)
			if e != nil || u.Scheme != "http" || u.Host != r.Host || u.User != nil || u.Path != "" {
				failure(w, 403, "forbidden", "Origin rejected")
				return
			}
		}
		select {
		case slots <- struct{}{}:
			defer func() { <-slots }()
		default:
			fail(w, search.ErrCapacity)
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), timeout)
		defer cancel()
		r = r.WithContext(ctx)
		r.Body = http.MaxBytesReader(w, r.Body, 64<<10)
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("X-Robots-Tag", "noindex, nofollow")
		w.Header().Set("Referrer-Policy", "no-referrer")
		transport.ServeHTTP(w, r)
	})
	api := New(s)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/mcp" {
			bounded.ServeHTTP(w, r)
			return
		}
		api.ServeHTTP(w, r)
	})
}
