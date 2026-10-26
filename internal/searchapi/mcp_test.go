package searchapi

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"jackieleven/internal/search"
)

func TestMCPInitializeToolsAndCall(t *testing.T) {
	m := search.Manifest{APIVersion: "v1", BuildID: "b", ContentVersion: "content", DataVersion: "data", EmbeddingProfile: "none"}
	s, _ := search.New(m, repo{}, nil, search.DefaultOptions())
	server := httptest.NewServer(NewWithMCP(s, time.Second))
	defer server.Close()
	call := func(body string) (*http.Response, map[string]any) {
		t.Helper()
		req, _ := http.NewRequest("POST", server.URL+"/mcp", bytes.NewBufferString(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Accept", "application/json, text/event-stream")
		req.Header.Set("MCP-Protocol-Version", "2025-11-25")
		res, e := http.DefaultClient.Do(req)
		if e != nil {
			t.Fatal(e)
		}
		defer res.Body.Close()
		raw, _ := io.ReadAll(res.Body)
		var data map[string]any
		if len(raw) > 0 && json.Unmarshal(raw, &data) != nil {
			t.Fatalf("invalid JSON: %s", raw)
		}
		return res, data
	}
	res, data := call(`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}`)
	if res.StatusCode != 200 || data["result"].(map[string]any)["protocolVersion"] != "2025-11-25" || res.Header.Get("Mcp-Session-Id") != "" {
		t.Fatal("initialization", res.StatusCode, data)
	}
	res, _ = call(`{"jsonrpc":"2.0","method":"notifications/initialized"}`)
	if res.StatusCode != 202 {
		t.Fatal("notification status", res.StatusCode)
	}
	res, data = call(`{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}`)
	if res.StatusCode != 200 {
		t.Fatal(res.StatusCode, data)
	}
	tools := data["result"].(map[string]any)["tools"].([]any)
	if len(tools) != 3 {
		t.Fatal("tool inventory", tools)
	}
	for _, tool := range tools {
		if tool.(map[string]any)["annotations"].(map[string]any)["readOnlyHint"] != true {
			t.Fatal("read-only hint")
		}
	}
	res, data = call(`{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search","arguments":{"q":"Jackie","mode":"hybrid"}}}`)
	if res.StatusCode != 200 {
		t.Fatal(res.StatusCode, data)
	}
	result := data["result"].(map[string]any)
	if result["isError"] == true {
		t.Fatal(result)
	}
	out := result["structuredContent"].(map[string]any)
	if out["content_version"] != "content" || out["mode"] != "lexical" || out["degraded"] != true {
		t.Fatal("MCP bypassed service semantics", out)
	}
	res, data = call(`{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_passage","arguments":{"id":"unknown"}}}`)
	if data["result"].(map[string]any)["isError"] != true {
		t.Fatal("missing passage must be tool error", data)
	}
}
func TestMCPRejectsBrowserOriginAndStreamingGET(t *testing.T) {
	m := search.Manifest{APIVersion: "v1", BuildID: "b", ContentVersion: "c", DataVersion: "d", EmbeddingProfile: "none"}
	s, _ := search.New(m, repo{}, nil, search.DefaultOptions())
	h := NewWithMCP(s, time.Second)
	for _, tc := range []struct {
		method, origin, host string
		status               int
	}{{"POST", "https://evil.example", "127.0.0.1:8081", 403}, {"POST", "", "evil.example", 403}, {"GET", "", "127.0.0.1:8081", 405}} {
		r := httptest.NewRequest(tc.method, "http://"+tc.host+"/mcp", strings.NewReader(`{}`))
		r.Header.Set("Origin", tc.origin)
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		if w.Code != tc.status {
			t.Fatal(tc, w.Code)
		}
	}
}
