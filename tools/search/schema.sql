CREATE EXTENSION IF NOT EXISTS pg_search CASCADE;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS search;
CREATE SCHEMA IF NOT EXISTS indexer_state;
CREATE TABLE IF NOT EXISTS search.builds (
 build_id TEXT PRIMARY KEY, content_version TEXT NOT NULL UNIQUE,
 data_version TEXT NOT NULL, embedding_profile TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('building','ready','failed')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS search.passages (
 row_id BIGSERIAL PRIMARY KEY, build_id TEXT NOT NULL REFERENCES search.builds,
 id TEXT NOT NULL, document_id TEXT NOT NULL, title TEXT NOT NULL, text TEXT NOT NULL,
 language TEXT NOT NULL, source_voice TEXT NOT NULL, text_voice TEXT NOT NULL,
 text_kind TEXT NOT NULL, year INTEGER, url_de TEXT NOT NULL, url_en TEXT NOT NULL,
 content_hash TEXT NOT NULL, embedding halfvec(1024), metadata JSONB NOT NULL DEFAULT '{}',
 UNIQUE(build_id,id)
);
CREATE TABLE IF NOT EXISTS search.entities (
 build_id TEXT NOT NULL REFERENCES search.builds, id TEXT NOT NULL, data JSONB NOT NULL,
 PRIMARY KEY(build_id,id)
);
CREATE INDEX IF NOT EXISTS passages_build ON search.passages(build_id);
CREATE INDEX IF NOT EXISTS passages_search ON search.passages USING paradedb
 (row_id,title,text,(build_id::pdb.literal),(language::pdb.literal),
 (source_voice::pdb.literal),(text_voice::pdb.literal),(text_kind::pdb.literal),year);
CREATE TABLE IF NOT EXISTS indexer_state.runs (
 build_id TEXT PRIMARY KEY, input_hash TEXT NOT NULL, profile TEXT NOT NULL,
 status TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 1,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), error_code TEXT
);
CREATE TABLE IF NOT EXISTS indexer_state.run_items (
 build_id TEXT NOT NULL REFERENCES indexer_state.runs, passage_id TEXT NOT NULL,
 input_hash TEXT NOT NULL, artifact_key TEXT, status TEXT NOT NULL,
 PRIMARY KEY(build_id,passage_id)
);
CREATE TABLE IF NOT EXISTS indexer_state.artifacts (
 artifact_key TEXT PRIMARY KEY, profile TEXT NOT NULL, input_hash TEXT NOT NULL,
 sha256 TEXT NOT NULL, dimensions INTEGER NOT NULL, local_path TEXT NOT NULL,
 validated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
