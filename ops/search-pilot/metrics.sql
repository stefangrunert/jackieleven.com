\echo === relation sizes; tiny fixture, not capacity estimate ===
SELECT relname,pg_relation_size(oid) AS bytes FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind IN ('r','i') ORDER BY relname;
SELECT pg_database_size(current_database()) AS database_bytes;
SELECT name,setting,unit FROM pg_settings WHERE name IN ('shared_buffers','work_mem','maintenance_work_mem','max_connections','shared_preload_libraries','pg_textsearch.memory_limit') ORDER BY name;
