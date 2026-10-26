package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"jackieleven/internal/search"
	"jackieleven/internal/searchapi"
)

func main() {
	if run() != nil {
		fmt.Fprintln(os.Stderr, "search service could not start or stopped unexpectedly")
		os.Exit(1)
	}
}
func run() error {
	listen := flag.String("listen", "127.0.0.1:8081", "numeric loopback listen address")
	manifest := flag.String("manifest", "", "immutable local search manifest")
	requestTimeout := flag.Duration("request-timeout", 10*time.Second, "total request deadline")
	providerTimeout := flag.Duration("provider-timeout", 3*time.Second, "provider call deadline")
	rerankTimeout := flag.Duration("rerank-timeout", 6*time.Second, "reranking call deadline")
	enableMCP := flag.Bool("mcp", false, "enable local read-only MCP at /mcp")
	flag.Parse()
	host, _, e := net.SplitHostPort(*listen)
	if e != nil || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() {
		return search.ErrInvalid
	}
	m, e := search.LoadManifest(*manifest)
	if e != nil {
		return e
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	db, e := search.OpenPostgres(ctx, os.Getenv("JACKIE_SEARCH_DATABASE_URL"), 1500*time.Millisecond)
	if e != nil {
		return e
	}
	defer db.Close()
	var provider search.Provider
	if os.Getenv("JACKIE_SEARCH_EXTERNAL") == "1" {
		key := strings.TrimSpace(os.Getenv("JACKIE_DEEPINFRA_API_KEY"))
		if key == "" && os.Getenv("JACKIE_DEEPINFRA_API_KEY_FILE") != "" {
			f, err := os.Open(os.Getenv("JACKIE_DEEPINFRA_API_KEY_FILE"))
			if err != nil {
				return search.ErrInvalid
			}
			raw, err := io.ReadAll(io.LimitReader(f, 8193))
			f.Close()
			if err != nil || len(raw) > 8192 {
				return search.ErrInvalid
			}
			key = strings.TrimSpace(string(raw))
		}
		if key == "" {
			return search.ErrInvalid
		}
		provider = search.NewDeepInfra(key)
	}
	opts := search.DefaultOptions()
	opts.RequestTimeout = *requestTimeout
	opts.ProviderTimeout = *providerTimeout
	opts.RerankTimeout = *rerankTimeout
	service, e := search.New(m, db, provider, opts)
	if e != nil {
		return e
	}
	handler := searchapi.New(service)
	if *enableMCP {
		handler = searchapi.NewWithMCP(service, *requestTimeout)
	}
	// Start even if DB is unavailable; /healthz lives while /readyz reports 503.
	server := &http.Server{Addr: *listen, Handler: handler, ReadHeaderTimeout: 2 * time.Second, ReadTimeout: 3 * time.Second, WriteTimeout: *requestTimeout + time.Second, IdleTimeout: 30 * time.Second, MaxHeaderBytes: 16 << 10, ErrorLog: log.New(io.Discard, "", 0)}
	listener, e := net.Listen("tcp", *listen)
	if e != nil {
		return search.ErrUnavailable
	}
	done := make(chan error, 1)
	go func() { done <- server.Serve(listener) }()
	select {
	case <-ctx.Done():
		shutdown, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		if server.Shutdown(shutdown) != nil {
			server.Close()
		}
		return nil
	case err := <-done:
		if err == http.ErrServerClosed {
			return nil
		}
		return search.ErrUnavailable
	}
}
