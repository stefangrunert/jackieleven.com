package search

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
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
		// Internal boost serialization contains these words. They must never
		// become search terms merely because a query parameter has a custom type.
		trapVector := make([]float32, 1024)
		trapVector[1] = 1
		_, e = admin.Exec(ctx, `INSERT INTO search.passages(build_id,id,document_id,title,text,language,source_voice,text_voice,text_kind,year,url_de,url_en,content_hash,embedding) VALUES($1,'doc#trap','doc','Parameter regression trap','string null score adjusted query contrastuniquetoken','en','third_party','editorial','summary',2001,'/de/synthetic','/en/synthetic','trap-hash',$2)`, build, pgvector.NewHalfVector(trapVector))
		if e != nil {
			t.Fatal("parameter trap fixture insert failed")
		}
		_, e = admin.Exec(ctx, `INSERT INTO search.entities(build_id,id,data) VALUES($1,'person','{"id":"person","label":"Synthetic"}')`, build)
		if e != nil {
			t.Fatal("test entity insert failed")
		}
	}
	readerDSN := os.Getenv("JACKIE_SEARCH_TEST_READER_DATABASE_URL")
	if readerDSN != "" {
		reader, err := pgx.Connect(ctx, readerDSN)
		if err != nil {
			t.Fatal("reader connection failed")
		}
		defer reader.Close(context.Background())
		if _, err = reader.Exec(ctx, "SET default_transaction_read_only=off"); err != nil {
			t.Fatal("reader test session setup failed")
		}
		if _, err = reader.Exec(ctx, `INSERT INTO search.entities(build_id,id,data) VALUES($1,'forbidden','{}')`, id); err == nil {
			t.Fatal("reader unexpectedly has write privilege")
		}
		dsn = readerDSN
	}
	db, e := OpenPostgres(ctx, dsn, time.Second)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	poolConfig := db.Pool.Config()
	poolConfig.MaxConns = 1
	db.Pool.Close()
	db.Pool, e = pgxpool.NewWithConfig(ctx, poolConfig)
	if e != nil {
		t.Fatal("single-connection test pool")
	}

	if e = db.Ready(ctx, m); e != nil {
		t.Fatal("readiness", e)
	}
	short, stop := context.WithTimeout(ctx, 20*time.Millisecond)
	started := time.Now()
	_, sleepErr := db.Pool.Exec(short, "SELECT pg_sleep(5)")
	stop()
	if sleepErr == nil || time.Since(started) > time.Second {
		t.Fatal("SQL cancellation did not honor context")
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
	var pidBefore, pidAfter int
	if e = db.Pool.QueryRow(ctx, "SELECT pg_backend_pid()").Scan(&pidBefore); e != nil {
		t.Fatal("backend pid")
	}
	for i := 0; i < 18; i++ {
		tc := []struct{ term, id string }{{"syntheticuniquetoken", "doc#p"}, {"contrastuniquetoken", "doc#trap"}, {"zzzxqvdoesnotexist", ""}}[i%3]
		q.Text = tc.term
		hits, e = db.Lexical(ctx, m, q, 20)
		if e != nil || (tc.id == "" && len(hits) != 0) || (tc.id != "" && (len(hits) != 1 || hits[0].ID != tc.id)) {
			t.Fatalf("reused connection query %d: n=%d err=%v", i, len(hits), e)
		}
	}
	if e = db.Pool.QueryRow(ctx, "SELECT pg_backend_pid()").Scan(&pidAfter); e != nil || pidAfter != pidBefore {
		t.Fatal("parameter regression must reuse one backend")
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
	if e != nil || len(hits) != 2 || hits[0].Score < .999 {
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
	testGroupedPostgres(t, ctx, admin, db, m)
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

// Optional regression against a pinned imported corpus; read-only.
func TestLiveNoHitRegression(t *testing.T) {
	manifestPath := os.Getenv("JACKIE_SEARCH_TEST_MANIFEST")
	if manifestPath == "" {
		t.Skip("set JACKIE_SEARCH_TEST_MANIFEST for populated-corpus regression")
	}
	m, e := LoadManifest(manifestPath)
	if e != nil {
		t.Fatal(e)
	}
	dsn := os.Getenv("JACKIE_SEARCH_TEST_READER_DATABASE_URL")
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	db, e := OpenPostgres(ctx, dsn, time.Second)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	poolConfig := db.Pool.Config()
	poolConfig.MaxConns = 1
	db.Pool.Close()
	db.Pool, e = pgxpool.NewWithConfig(ctx, poolConfig)
	if e != nil {
		t.Fatal("single-connection test pool")
	}

	q := query()
	q.Mode = "lexical"
	q.Limit = 3
	for i, term := range []string{"xxxxxxxxxxzyxzxq", "Leven", "xxxxxxxxxxzyxzxq", "Doll", "xxxxxxxxxxzyxzxq", "Norwegen", "xxxxxxxxxxzyxzxq", "Leven", "xxxxxxxxxxzyxzxq"} {
		q.Text = term
		hits, e := db.Lexical(ctx, m, q, 3)
		t.Logf("iteration=%d hits=%d error=%v", i, len(hits), e)
		if term == "xxxxxxxxxxzyxzxq" && (e != nil || len(hits) != 0) {
			t.Errorf("nonexistent term returned %d hits", len(hits))
		}
	}
}

func testGroupedPostgres(t *testing.T, ctx context.Context, admin *pgx.Conn, db *Postgres, m Manifest) {
	t.Helper()
	vector := make([]float32, 1024)
	vector[0] = 1
	insert := func(id, doc, section, language, kind, voice string, fiction bool) {
		t.Helper()
		metadata := fmt.Sprintf(`{"section":%q,"fiction":%t}`, section, fiction)
		_, e := admin.Exec(ctx, `INSERT INTO search.passages(build_id,id,document_id,title,text,language,source_voice,text_voice,text_kind,year,url_de,url_en,content_hash,embedding,metadata) VALUES($1,$2,$3,'Fixture','groupedvalidationterm',$4,'editorial',$5,$6,2001,'/de/synthetic','/en/synthetic','grouped-hash',$7,$8)`, m.BuildID, id, doc, language, voice, kind, pgvector.NewHalfVector(vector), metadata)
		if e != nil {
			t.Fatal("grouped fixture insert failed")
		}
	}
	for i := 0; i < 20; i++ {
		insert(fmt.Sprintf("group-many-%d", i), "many", "music", "en", "original", "editorial", false)
	}
	for i := 0; i < 3; i++ {
		insert(fmt.Sprintf("group-other-%d", i), fmt.Sprintf("other-%d", i), "music", "en", "original", "editorial", false)
	}
	insert("local-en", "localized", "press", "en", "summary", "editorial", false)
	insert("local-de", "localized", "press", "de", "summary", "editorial", false)
	insert("original-en", "quoted", "press", "en", "original", "editorial", false)
	insert("original-de", "quoted", "press", "de", "summary", "editorial", false)
	insert("fiction-voice", "fiction-voice", "biography", "de", "original", "pastiche", false)
	insert("fiction-flag", "fiction-flag", "press", "de", "summary", "editorial", true)
	q := query()
	q.Text = "groupedvalidationterm"
	q.Mode = "lexical"
	hits, e := db.Lexical(ctx, m, q, 50)
	if e != nil || len(hits) != 27 {
		t.Fatalf("default fiction exclusion: n=%d e=%v", len(hits), e)
	}
	q.Section = "music"
	q.Grouped = true
	for _, semantic := range []bool{false, true} {
		var hits []Hit
		var e error
		if semantic {
			hits, e = db.Semantic(ctx, m, q, vector, 4)
		} else {
			hits, e = db.Lexical(ctx, m, q, 4)
		}
		if e != nil || len(hits) != 4 {
			t.Fatalf("dedup before LIMIT (semantic=%t): n=%d e=%v", semantic, len(hits), e)
		}
		docs := map[string]bool{}
		for _, h := range hits {
			if docs[h.DocumentID] || hitSection(h) != "music" {
				t.Fatal("section or document leak")
			}
			docs[h.DocumentID] = true
		}
	}
	q.Section = "press"
	for _, semantic := range []bool{false, true} {
		var hits []Hit
		var e error
		if semantic {
			hits, e = db.Semantic(ctx, m, q, vector, 10)
		} else {
			hits, e = db.Lexical(ctx, m, q, 10)
		}
		if e != nil || len(hits) != 2 {
			t.Fatalf("localized/evidence selection (semantic=%t): n=%d e=%v", semantic, len(hits), e)
		}
		for _, h := range hits {
			if h.DocumentID == "localized" && h.ID != "local-de" {
				t.Fatal("preferred summary language not selected")
			}
			if h.DocumentID == "quoted" && h.ID != "original-en" {
				t.Fatal("original quote displaced")
			}
		}
	}
	q.Section = "biography"
	hits, e = db.Lexical(ctx, m, q, 10)
	if e != nil || len(hits) != 1 || hits[0].ID != "fiction-voice" {
		t.Fatal("biography opt-in", len(hits), e)
	}
	q.Section = ""
	q.Voice = "pastiche"
	hits, e = db.Semantic(ctx, m, q, vector, 10)
	if e != nil || len(hits) != 1 || hits[0].ID != "fiction-voice" {
		t.Fatal("pastiche voice opt-in", len(hits), e)
	}
}

// Full imported corpus smoke: no provider calls, no data mutations.
func TestLiveGroupedLexicalRegression(t *testing.T) {
	path := os.Getenv("JACKIE_SEARCH_TEST_MANIFEST")
	if path == "" {
		t.Skip("set JACKIE_SEARCH_TEST_MANIFEST for populated-corpus grouped regression")
	}
	m, e := LoadManifest(path)
	if e != nil {
		t.Fatal(e)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	db, e := OpenPostgres(ctx, os.Getenv("JACKIE_SEARCH_TEST_READER_DATABASE_URL"), 1500*time.Millisecond)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	service, e := New(m, db, nil, DefaultOptions())
	if e != nil {
		t.Fatal(e)
	}
	q := query()
	q.Text = "Leven"
	q.Mode = "lexical"
	q.Grouped = true
	out, e := service.Search(ctx, q)
	if e != nil {
		t.Fatal("grouped live search", e)
	}
	docs := map[string]bool{}
	counts := map[string]int{}
	for _, h := range out.Hits {
		var meta struct {
			Section string `json:"section"`
			Fiction bool   `json:"fiction"`
		}
		if json.Unmarshal(h.Metadata, &meta) != nil {
			t.Fatal("invalid metadata")
		}
		if !validSection(meta.Section) || meta.Fiction || h.TextVoice == "pastiche" || docs[h.DocumentID] {
			t.Fatal("grouping or fiction invariant")
		}
		docs[h.DocumentID] = true
		counts[meta.Section]++
		if counts[meta.Section] > 3 {
			t.Fatal("section limit")
		}
	}
	t.Logf("grouped hits=%d sections=%v duration_ms=%d", len(out.Hits), counts, out.DurationMS)
	q.Text = "xxxxxxxxxxzyxzxq"
	out, e = service.Search(ctx, q)
	if e != nil || len(out.Hits) != 0 {
		t.Fatal("grouped lexical miss", len(out.Hits), e)
	}
}
