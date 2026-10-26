SELECT id FROM documents WHERE documents @@@ pdb.parse('title:"The Deep Pool"') AND voice <> 'pastiche' AND year <= 2002 ORDER BY pdb.score(id) DESC LIMIT 5;
