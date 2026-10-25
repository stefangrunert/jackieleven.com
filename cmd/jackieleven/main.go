package main

import (
	"context"
	"flag"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"jackieleven/internal/site"
)

func main() {
	listen := flag.String("listen", "127.0.0.1:8080", "HTTP listen address")
	root := flag.String("root", ".", "directory containing data, templates, assets and Markdown")
	basePath := flag.String("base-path", "", "optional URL mount path, for example /jackieleven")
	trust := flag.Bool("trust-proxy", false, "trust X-Real-IP and X-Forwarded-Proto only from loopback peers")
	flag.Parse()
	app, err := site.New(site.Config{Root: *root, BasePath: *basePath, TrustProxy: *trust, Contact: site.ContactConfigFromEnv()})
	if err != nil {
		log.Fatal(err)
	}
	server := site.HTTPServer(*listen, app)
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	shutdownDone := make(chan struct{})
	go func() {
		defer close(shutdownDone)
		<-ctx.Done()
		shutdown, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		if err := server.Shutdown(shutdown); err != nil {
			log.Printf("shutdown: %v", err)
		}
	}()
	log.Printf("Jackie Leven listening on %s", *listen)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
	<-shutdownDone
}
