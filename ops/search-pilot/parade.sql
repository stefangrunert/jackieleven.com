\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS pg_search CASCADE;
\i /pilot/fixture.sql
CREATE INDEX documents_search ON documents USING paradedb
 (id,title,body,(name::pdb.literal),language,voice,year,
 (body_de::pdb.simple('stemmer=german')),
 (body_en::pdb.simple('stemmer=english')));
\echo === versions ===
SELECT version();
SELECT extname,extversion FROM pg_extension ORDER BY 1;
\echo === analysis ===
SELECT 'Sänger spielten Lieder Städten'::pdb.simple('stemmer=german')::text[];
SELECT 'singing songs rivers'::pdb.simple('stemmer=english')::text[];
SELECT 'Jackie Leven'::pdb.literal::text[];
\echo === de inflection: 3,4 ===
SELECT id FROM documents WHERE body_de ||| 'Sänger Lied Stadt' ORDER BY id;
\echo === en inflection: 1 ===
SELECT id FROM documents WHERE body_en ||| 'sing song' ORDER BY id;
\echo === exact name: 1,3,4,5 ===
SELECT id FROM documents WHERE name = 'Jackie Leven' ORDER BY id;
\echo === phrase: 1,5; reversed and intervening words excluded ===
SELECT id FROM documents WHERE documents @@@ pdb.parse('title:"The Deep Pool"') ORDER BY id;
\echo === filtered phrase: 1 ===
SELECT id FROM documents WHERE documents @@@ pdb.parse('title:"The Deep Pool"') AND voice <> 'pastiche' AND year <= 2002 ORDER BY id;
\echo === unweighted field ranking ===
SELECT id,pdb.score(id) FROM documents WHERE title ||| 'river' OR body ||| 'river' ORDER BY pdb.score(id) DESC,id;
\echo === title boost 4 ===
SELECT id,pdb.score(id) FROM documents WHERE title ||| 'river'::pdb.boost(4) OR body ||| 'river' ORDER BY pdb.score(id) DESC,id;
\echo === plan ===
EXPLAIN (ANALYZE,BUFFERS) SELECT id,pdb.score(id) FROM documents WHERE body_en ||| 'sing song' AND voice <> 'pastiche' ORDER BY pdb.score(id) DESC LIMIT 5;

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
SELECT pilot_assert('DE', ARRAY(SELECT id FROM documents WHERE body_de ||| 'Sänger Lied Stadt' ORDER BY id), ARRAY[3,4]);
SELECT pilot_assert('EN', ARRAY(SELECT id FROM documents WHERE body_en ||| 'sing song' ORDER BY id), ARRAY[1]);
SELECT pilot_assert('phrase excludes inserted/reordered tokens', ARRAY(SELECT id FROM documents WHERE documents @@@ pdb.parse('title:"The Deep Pool"') ORDER BY id), ARRAY[1,5]);
SELECT pilot_assert('phrase + filters', ARRAY(SELECT id FROM documents WHERE documents @@@ pdb.parse('title:"The Deep Pool"') AND voice <> 'pastiche' AND year <= 2002 ORDER BY id), ARRAY[1]);
SELECT pilot_assert('no hits', ARRAY(SELECT id FROM documents WHERE body_en ||| 'zzzxqvnonexistent' ORDER BY id), ARRAY[]::integer[]);
SELECT pilot_assert('title boost changes first result', ARRAY(SELECT id FROM documents WHERE title ||| 'river'::pdb.boost(4) OR body ||| 'river' ORDER BY pdb.score(id) DESC,id LIMIT 1), ARRAY[6]);
\i /pilot/metrics.sql
