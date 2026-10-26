package search

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	pgvector "github.com/pgvector/pgvector-go"
	pgxvec "github.com/pgvector/pgvector-go/pgx"
)

type Postgres struct {
	Pool    *pgxpool.Pool
	Timeout time.Duration
}

func OpenPostgres(ctx context.Context, dsn string, timeout time.Duration) (*Postgres, error) {
	if dsn == "" {
		return nil, ErrInvalid
	}
	c, e := pgxpool.ParseConfig(dsn)
	if e != nil {
		return nil, ErrUnavailable
	}
	c.MaxConns = 4
	c.MinConns = 0
	c.MaxConnIdleTime = time.Minute
	c.MaxConnLifetime = 30 * time.Minute
	c.ConnConfig.ConnectTimeout = timeout
	c.ConnConfig.RuntimeParams["statement_timeout"] = "1500"
	c.ConnConfig.RuntimeParams["lock_timeout"] = "500"
	c.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	c.ConnConfig.RuntimeParams["application_name"] = "jackieleven-search"
	c.ConnConfig.Tracer = nil
	c.AfterConnect = func(ctx context.Context, c *pgx.Conn) error { return pgxvec.RegisterTypes(ctx, c) }
	pool, e := pgxpool.NewWithConfig(ctx, c)
	if e != nil {
		return nil, ErrUnavailable
	}
	return &Postgres{pool, timeout}, nil
}
func (p *Postgres) Close() { p.Pool.Close() }
func (p *Postgres) Ready(ctx context.Context, m Manifest) error {
	ctx, cancel := context.WithTimeout(ctx, p.Timeout)
	defer cancel()
	var ok bool
	e := p.Pool.QueryRow(ctx, `WITH schema_check AS (SELECT p.row_id,p.build_id,p.id,p.document_id,p.title,p.text,p.language,p.source_voice,p.text_voice,p.text_kind,p.year,p.url_de,p.url_en,p.content_hash,p.embedding,p.metadata,e.build_id,e.id,e.data FROM search.passages p LEFT JOIN search.entities e ON false LIMIT 0)
 SELECT EXISTS(SELECT 1 FROM search.builds WHERE build_id=$1 AND content_version=$2 AND data_version=$3 AND embedding_profile=$4 AND status='ready')
 AND EXISTS(SELECT 1 FROM pg_extension WHERE extname='pg_search' AND extversion='0.26.3')
 AND EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector' AND extversion='0.8.6')
 AND to_regclass('search.entities') IS NOT NULL
 AND has_table_privilege('search.passages','SELECT') AND has_table_privilege('search.entities','SELECT')
 AND EXISTS(SELECT 1 FROM pg_attribute WHERE attrelid='search.passages'::regclass AND attname='embedding' AND format_type(atttypid,atttypmod)='halfvec(1024)')
 AND EXISTS(SELECT 1 FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_am am ON am.oid=c.relam WHERE i.indrelid='search.passages'::regclass AND i.indisvalid AND am.amname IN ('paradedb','bm25'))`, m.BuildID, m.ContentVersion, m.DataVersion, m.EmbeddingProfile).Scan(&ok)
	if e != nil || !ok {
		return ErrUnavailable
	}
	return nil
}

const fields = `p.id,p.document_id,p.title,p.text,p.language,p.source_voice,p.text_voice,p.text_kind,CASE WHEN $3='de' THEN p.url_de ELSE p.url_en END,p.metadata`

const excerptFields = `p.id,p.document_id,left(p.title,1024),left(p.text,1201),p.language,p.source_voice,p.text_voice,p.text_kind,CASE WHEN $3='de' THEN p.url_de ELSE p.url_en END,CASE WHEN octet_length(p.metadata::text)<=16384 THEN p.metadata ELSE '{}'::jsonb END`

// Every path binds both the build and content version; no caller chooses a schema.
const bound = ` FROM search.passages p JOIN search.builds b ON b.build_id=p.build_id WHERE p.build_id=$1 AND b.content_version=$2 AND b.status='ready'`
const filters = ` AND ($4::text='' OR p.text_voice=$4) AND ($5::integer IS NULL OR p.year >= $5) AND ($6::integer IS NULL OR p.year <= $6)`

func args(m Manifest, q Query) []any {
	return []any{m.BuildID, m.ContentVersion, q.Language, q.Voice, q.From, q.To}
}
func (p *Postgres) Lexical(ctx context.Context, m Manifest, q Query, n int) ([]Hit, error) {
	a := append(args(m, q), q.Text, n)
	return p.hits(ctx, `SELECT `+excerptFields+`,pdb.score(p.row_id)::double precision`+bound+filters+` AND (p.title ||| $7::pdb.boost(3) OR p.text ||| $7::text) ORDER BY pdb.score(p.row_id) DESC,p.id LIMIT $8`, a...)
}
func (p *Postgres) Semantic(ctx context.Context, m Manifest, q Query, v []float32, n int) ([]Hit, error) {
	if len(v) != 1024 {
		return nil, ErrInvalid
	}
	a := append(args(m, q), pgvector.NewHalfVector(v), n)
	return p.hits(ctx, `SELECT `+excerptFields+`,(1-(p.embedding <=> $7::halfvec))::double precision`+bound+filters+` AND p.embedding IS NOT NULL ORDER BY p.embedding <=> $7::halfvec,p.id LIMIT $8`, a...)
}
func scanHit(row pgx.Row) (Hit, error) {
	var h Hit
	e := row.Scan(&h.ID, &h.DocumentID, &h.Title, &h.Text, &h.Language, &h.SourceVoice, &h.TextVoice, &h.TextKind, &h.URL, &h.Metadata, &h.Score)
	if len(h.Metadata) > 16384 {
		h.Metadata = nil
	}
	return h, e
}
func (p *Postgres) hits(ctx context.Context, sql string, a ...any) ([]Hit, error) {
	ctx, cancel := context.WithTimeout(ctx, p.Timeout)
	defer cancel()
	rows, e := p.Pool.Query(ctx, sql, a...)
	if e != nil {
		return nil, ErrUnavailable
	}
	defer rows.Close()
	out := make([]Hit, 0)
	for rows.Next() {
		h, e := scanHit(rows)
		if e != nil {
			return nil, ErrUnavailable
		}
		if len(h.Text) > 262144 {
			return nil, ErrUnavailable
		}
		out = append(out, h)
	}
	if rows.Err() != nil {
		return nil, ErrUnavailable
	}
	return out, nil
}
func (p *Postgres) Passage(ctx context.Context, m Manifest, id, lang string) (Hit, error) {
	ctx, cancel := context.WithTimeout(ctx, p.Timeout)
	defer cancel()
	h, e := scanHit(p.Pool.QueryRow(ctx, `SELECT `+fields+`,0::double precision`+bound+` AND p.id=$4`, m.BuildID, m.ContentVersion, lang, id))
	if errors.Is(e, pgx.ErrNoRows) {
		return h, ErrNotFound
	}
	if e != nil || len(h.Text) > 262144 {
		return Hit{}, ErrUnavailable
	}
	return h, nil
}
func (p *Postgres) Entity(ctx context.Context, m Manifest, id string) (json.RawMessage, error) {
	ctx, cancel := context.WithTimeout(ctx, p.Timeout)
	defer cancel()
	var raw json.RawMessage
	e := p.Pool.QueryRow(ctx, `SELECT e.data FROM search.entities e JOIN search.builds b ON b.build_id=e.build_id WHERE e.build_id=$1 AND b.content_version=$2 AND b.status='ready' AND e.id=$3`, m.BuildID, m.ContentVersion, id).Scan(&raw)
	if errors.Is(e, pgx.ErrNoRows) {
		return nil, ErrNotFound
	}
	if e != nil || len(raw) > 262144 {
		return nil, ErrUnavailable
	}
	return raw, nil
}
