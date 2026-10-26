\set ON_ERROR_STOP on
\timing on
SET statement_timeout = '10s';
CREATE TABLE documents (
 id integer PRIMARY KEY, language text NOT NULL, voice text NOT NULL,
 year integer NOT NULL, title text NOT NULL, body text NOT NULL,
 name text NOT NULL, body_de text NOT NULL DEFAULT '', body_en text NOT NULL DEFAULT ''
);
-- Invented examples for mechanics, not historical claims or archive quotations.
INSERT INTO documents (id,language,voice,year,title,body,name) VALUES
(1,'en','original',2001,'The Deep Pool','Jackie Leven was singing songs beside the river.','Jackie Leven'),
(2,'en','third_party',2002,'The Deep Blue Pool','Leven met Jackie near a deep blue pool.','Leven Jackie'),
(3,'de','editorial',2003,'Konzerte in Städten','Die Sänger spielten Lieder in mehreren Städten.','Jackie Leven'),
(4,'de','editorial',2004,'Ein Konzert','Ein Sänger spielt ein Lied in einer Stadt.','Jackie Leven'),
(5,'en','pastiche',2005,'The Deep Pool','Jackie Leven imagined a concert in a fictional city.','Jackie Leven'),
(6,'en','third_party',2006,'River','A quiet evening with music.','David Thomas'),
(7,'en','third_party',2006,'An evening','River river river river music.','David Thomas'),
(8,'en','editorial',2007,'Pool Deep The','Jackie Levens and Jack Leven are deliberately different strings.','Jackie Levens'),
(9,'de','editorial',2008,'Schreibweisen','Jörg Müller besucht Köln; Joerg Mueller besucht Koeln.','Jörg Müller'),
(10,'en','editorial',2009,'Catalogue','Cooking Vinyl COOK CD 123; Doll by Doll.','Doll by Doll');
UPDATE documents SET body_de=CASE WHEN language='de' THEN body ELSE '' END,
 body_en=CASE WHEN language='en' THEN body ELSE '' END;
CREATE INDEX documents_filter ON documents(language,voice,year);
ANALYZE documents;
