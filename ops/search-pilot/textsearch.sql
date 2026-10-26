\set ON_ERROR_STOP on
CREATE EXTENSION pg_textsearch;
\i /pilot/fixture.sql
CREATE INDEX documents_de ON documents USING bm25(body) WITH (text_config='german') WHERE language='de';
CREATE INDEX documents_en ON documents USING bm25(body) WITH (text_config='english') WHERE language='en';
CREATE INDEX documents_title ON documents USING bm25(title) WITH (text_config='simple');
CREATE INDEX documents_body ON documents USING bm25(body) WITH (text_config='simple');
CREATE INDEX documents_name ON documents(name);
\echo === versions ===
SELECT version();
SELECT extname,extversion FROM pg_extension ORDER BY 1;
\echo === analysis ===
SELECT to_tsvector('german','Sänger spielten Lieder Städten');
SELECT to_tsvector('english','singing songs rivers');
SELECT to_tsvector('simple','Jackie Leven');
\echo === de inflection: 3,4 ===
SET default_text_search_config='german';
SELECT id,body <@> to_bm25query('Sänger Lied Stadt','documents_de') AS score FROM documents WHERE language='de' AND body @@ plainto_tsquery('german','Sänger Lied Stadt') ORDER BY score,id;
\echo === en inflection: 1 ===
SET default_text_search_config='english';
SELECT id,body <@> to_bm25query('sing song','documents_en') AS score FROM documents WHERE language='en' AND body @@ plainto_tsquery('english','sing song') ORDER BY score,id;
\echo === exact name: 1,3,4,5; ordinary btree ===
SELECT id FROM documents WHERE name='Jackie Leven' ORDER BY id;
\echo === phrase: 1,5 ===
SET default_text_search_config='simple';
SELECT id FROM documents WHERE title @@ phraseto_tsquery('simple','The Deep Pool') ORDER BY id;
\echo === filtered phrase: 1 ===
SELECT id FROM documents WHERE title @@ phraseto_tsquery('simple','The Deep Pool') AND voice <> 'pastiche' AND year <= 2002 ORDER BY id;
\echo === unweighted field ranking; scores from separate indexes ===
SELECT id,(title <@> to_bm25query('river','documents_title')) + (body <@> to_bm25query('river','documents_body')) AS score FROM documents WHERE title @@ to_tsquery('simple','river') OR body @@ to_tsquery('simple','river') ORDER BY score,id;
\echo === title factor 4; experimental score combination, not native BM25F ===
SELECT id,4*(title <@> to_bm25query('river','documents_title')) + (body <@> to_bm25query('river','documents_body')) AS score FROM documents WHERE title @@ to_tsquery('simple','river') OR body @@ to_tsquery('simple','river') ORDER BY score,id;
\echo === plan ===
SET default_text_search_config='english';
EXPLAIN (ANALYZE,BUFFERS) SELECT id FROM documents WHERE language='en' AND voice <> 'pastiche' ORDER BY body <@> to_bm25query('sing song','documents_en') LIMIT 5;

-- Assertions use stable IDs, never score equality across engines.
CREATE FUNCTION pilot_assert(label text, actual integer[], expected integer[])
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF actual IS DISTINCT FROM expected THEN
  RAISE EXCEPTION '%: got %, expected %', label, actual, expected;
 END IF;
 RAISE NOTICE 'PASS %: %', label, actual;
END $$;
SELECT pilot_assert('exact name', ARRAY(SELECT id FROM documents WHERE name='Jackie Leven' ORDER BY id), ARRAY[1,3,4,5]);
SET default_text_search_config='german';
SELECT pilot_assert('DE', ARRAY(SELECT id FROM documents WHERE language='de' AND body @@ plainto_tsquery('german','Sänger Lied Stadt') ORDER BY id), ARRAY[3,4]);
SET default_text_search_config='english';
SELECT pilot_assert('EN', ARRAY(SELECT id FROM documents WHERE language='en' AND body @@ plainto_tsquery('english','sing song') ORDER BY id), ARRAY[1]);
SELECT pilot_assert('no hits with explicit predicate', ARRAY(SELECT id FROM documents WHERE language='en' AND body @@ plainto_tsquery('english','zzzxqvnonexistent') ORDER BY id), ARRAY[]::integer[]);
\echo === rank-only no-hit diagnostic: forced sequential scoring returns nonmatches ===
SET enable_indexscan=off;
SET enable_bitmapscan=off;
SELECT id,body <@> to_bm25query('zzzxqvnonexistent','documents_en') AS score FROM documents WHERE language='en' ORDER BY score,id LIMIT 3;
RESET enable_indexscan;
RESET enable_bitmapscan;
SET default_text_search_config='simple';
SELECT pilot_assert('phrase excludes inserted/reordered tokens', ARRAY(SELECT id FROM documents WHERE title @@ phraseto_tsquery('simple','The Deep Pool') ORDER BY id), ARRAY[1,5]);
SELECT pilot_assert('phrase + filters', ARRAY(SELECT id FROM documents WHERE title @@ phraseto_tsquery('simple','The Deep Pool') AND voice <> 'pastiche' AND year <= 2002 ORDER BY id), ARRAY[1]);
SELECT pilot_assert('experimental title weighting', ARRAY(SELECT id FROM documents WHERE title @@ to_tsquery('simple','river') OR body @@ to_tsquery('simple','river') ORDER BY 4*(title <@> to_bm25query('river','documents_title'))+(body <@> to_bm25query('river','documents_body')),id LIMIT 1), ARRAY[6]);
\echo === force index plan for diagnosis only ===
SET enable_seqscan=off;
EXPLAIN (ANALYZE,BUFFERS) SELECT id FROM documents WHERE language='en' ORDER BY body <@> to_bm25query('sing song','documents_en') LIMIT 5;
RESET enable_seqscan;
\i /pilot/metrics.sql
