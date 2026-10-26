SELECT id FROM documents WHERE title @@ phraseto_tsquery('simple','The Deep Pool') AND voice <> 'pastiche' AND year <= 2002 ORDER BY title <@> to_bm25query('The Deep Pool','documents_title') LIMIT 5;
