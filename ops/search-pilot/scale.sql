\set ON_ERROR_STOP on
\timing on
-- 10 base records plus 99 copies = 1000 synthetic rows. Not relevance evidence.
INSERT INTO documents SELECT id+10*n,language,voice,year,title,body,name,body_de,body_en FROM documents CROSS JOIN generate_series(1,99) n;
REINDEX TABLE documents;
ANALYZE documents;
SELECT count(*) AS synthetic_rows FROM documents;
\i /pilot/metrics.sql
