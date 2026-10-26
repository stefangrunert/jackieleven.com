package search

import (
	"context"
	"fmt"
	"net"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	pgvector "github.com/pgvector/pgvector-go"
	pgxvec "github.com/pgvector/pgvector-go/pgx"
)

// Opt-in: touches only two uniquely named synthetic builds in an existing local schema.
func TestPostgresIntegration(t *testing.T) {
	dsn := os.Getenv("JACKIE_SEARCH_TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("set JACKIE_SEARCH_TEST_DATABASE_URL for isolated local DB test")
	}
	c, e := pgx.ParseConfig(dsn)
	if e != nil || net.ParseIP(c.Host) == nil || !net.ParseIP(c.Host).IsLoopback() {
		t.Fatal("test requires a numeric loopback DB")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	admin, e := pgx.ConnectConfig(ctx, c)
	if e != nil {
		t.Fatal("test DB connection failed")
	}
	defer admin.Close(context.Background())
	if e = pgxvec.RegisterTypes(ctx, admin); e != nil {
		t.Fatal("vector type registration failed")
	}
	id := fmt.Sprintf("service-test-%d", time.Now().UnixNano())
	other := id + "-other"
	defer func() {
		cleanup, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		for _, table := range []string{"passages", "entities", "builds"} {
			_, e := admin.Exec(cleanup, "DELETE FROM search."+table+" WHERE build_id=ANY($1)", []string{id, other})
			if e != nil {
				t.Error("own test-build cleanup failed")
			}
		}
	}()
	m := testManifest()
	m.BuildID = id
	m.ContentVersion = id + "-content"
	for _, build := range []string{id, other} {
		version := m.ContentVersion
		if build == other {
			version += "-other"
		}
		_, e = admin.Exec(ctx, `INSERT INTO search.builds(build_id,content_version,data_version,embedding_profile,status) VALUES($1,$2,$3,$4,'ready')`, build, version, m.DataVersion, m.EmbeddingProfile)
		if e != nil {
			t.Fatal("test build insert failed")
		}
		vec := make([]float32, 1024)
		vec[0] = 1
		_, e = admin.Exec(ctx, `INSERT INTO search.passages(build_id,id,document_id,title,text,language,source_voice,text_voice,text_kind,year,url_de,url_en,content_hash,embedding) VALUES($1,'doc#p','doc','Synthetic unique title','syntheticuniquetoken original readable text','en','third_party','editorial','summary',2001,'/de/synthetic','/en/synthetic','test-hash',$2)`, build, pgvector.NewHalfVector(vec))
		if e != nil {
			t.Fatal("test passage insert failed")
		}
		_, e = admin.Exec(ctx, `INSERT INTO search.entities(build_id,id,data) VALUES($1,'person','{"id":"person","label":"Synthetic"}')`, build)
		if e != nil {
			t.Fatal("test entity insert failed")
		}
	}
	db, e := OpenPostgres(ctx, dsn, time.Second)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if e = db.Ready(ctx, m); e != nil {
		t.Fatal("readiness", e)
	}
	q := query()
	q.Text = "syntheticuniquetoken"
	q.Mode = "lexical"
	hits, e := db.Lexical(ctx, m, q, 20)
	if e != nil || len(hits) != 1 || hits[0].ID != "doc#p" {
		t.Fatalf("BM25 bound build: n=%d err=%v", len(hits), e)
	}
	q.Text = "zzzxqvdoesnotexist"
	hits, e = db.Lexical(ctx, m, q, 20)
	if e != nil || len(hits) != 0 {
		t.Fatal("exact miss", len(hits), e)
	}
	q.Text = "syntheticuniquetoken"
	q.Voice = "third_party"
	hits, e = db.Lexical(ctx, m, q, 20)
	if e != nil || len(hits) != 0 {
		t.Fatal("voice must filter actual text voice")
	}
	q.Voice = "editorial"
	v := make([]float32, 1024)
	v[0] = 1
	hits, e = db.Semantic(ctx, m, q, v, 20)
	if e != nil || len(hits) != 1 || hits[0].Score < .999 {
		t.Fatal("halfvec exact cosine", len(hits), e)
	}
	p, e := db.Passage(ctx, m, "doc#p", "en")
	if e != nil || p.URL != "/en/synthetic" || p.Text != "syntheticuniquetoken original readable text" {
		t.Fatal("exact passage", e)
	}
	_, e = db.Entity(ctx, m, "person")
	if e != nil {
		t.Fatal("entity", e)
	}
	m.ContentVersion = "wrong"
	if db.Ready(ctx, m) == nil {
		t.Fatal("accepted wrong manifest")
	}
	hits, e = db.Lexical(ctx, m, q, 20)
	if e != nil || len(hits) != 0 {
		t.Fatal("wrong version leaked passages")
	}
	if _, e = db.Entity(ctx, m, "person"); e != ErrNotFound {
		t.Fatal("wrong version entity", e)
	}
}
