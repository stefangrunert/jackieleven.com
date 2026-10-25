package site

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

// Optional full-corpus fixture captured from reference revision 8694423.
// Provenance and comparison scope are recorded in docs/go-review.md.
// JACKIE_READING_FIXTURE points to its JSON, JACKIE_CONTENT_ROOT to sources.
func TestReferenceReadingParity(t *testing.T) {
	fixture := os.Getenv("JACKIE_READING_FIXTURE")
	if fixture == "" {
		t.Skip("Reading reference fixture not supplied")
	}
	data, err := os.ReadFile(fixture)
	if err != nil {
		t.Fatal(err)
	}
	var expected struct {
		Columns    []map[string]any                         `json:"columns"`
		ColumnHTML map[string]string                        `json:"column_html"`
		Chapters   map[string]map[string]map[string]any     `json:"chapters"`
		Markdown   []struct{ Input, Output, Inline string } `json:"markdown"`
	}
	if err := json.Unmarshal(data, &expected); err != nil {
		t.Fatal(err)
	}
	root := os.Getenv("JACKIE_CONTENT_ROOT")
	if root == "" {
		t.Fatal("JACKIE_CONTENT_ROOT required")
	}
	files := []string{}
	for _, k := range expected.Columns {
		files = append(files, k["datei"].(string))
	}
	columns, err := LoadColumns(root, files)
	if err != nil {
		t.Fatal(err)
	}
	encoded, _ := json.Marshal(columns)
	var normalized []map[string]any
	json.Unmarshal(encoded, &normalized)
	if !reflect.DeepEqual(normalized, expected.Columns) {
		for i, k := range normalized {
			if !reflect.DeepEqual(k, expected.Columns[i]) {
				t.Errorf("column model mismatch: %s", k["slug"])
			}
		}
	}
	for _, k := range normalized {
		slug := k["slug"].(string)
		if actual := string(ColumnHTML(ColumnReadingText(k))); actual != expected.ColumnHTML[slug] {
			t.Errorf("column HTML mismatch: %s", slug)
		}
	}
	for lang, chapters := range expected.Chapters {
		for slug, want := range chapters {
			if got := ChapterParts(root, slug, lang); !reflect.DeepEqual(got, want) {
				t.Errorf("chapter parts mismatch: %s/%s", lang, slug)
			}
		}
	}
	for i, pair := range expected.Markdown {
		if got := string(Markdown(pair.Input)); got != pair.Output {
			t.Errorf("markdown mismatch %d\nGOT: %.300s\nWANT: %.300s", i, got, pair.Output)
		}
		if got := string(MarkdownInline(pair.Input)); got != pair.Inline {
			t.Errorf("inline mismatch %d\nGOT: %.300s\nWANT: %.300s", i, got, pair.Inline)
		}
	}
	t.Logf("Compared %d column models/HTML, %d languages of chapters, %d Markdown samples", len(columns), len(expected.Chapters), len(expected.Markdown))
}

func TestMarkdownEscapesAndBoundaries(t *testing.T) {
	for _, test := range []struct{ input, want string }{
		{`<script>alert("x")</script>`, `&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;`},
		{`[unsafe](javascript:alert)`, `unsafe`},
		{`[source](https://example.test/?a=1&b=2)`, `<a href="https://example.test/?a=1&amp;b=2" rel="noopener noreferrer">source</a>`},
		{`word*inside*word *emphasis* **bold**`, `word*inside*word <em>emphasis</em> <strong>bold</strong>`},
		{`* space* *space * *a*`, `* space* <em>space * *a</em>`},
	} {
		if got := string(MarkdownInline(test.input)); got != test.want {
			t.Errorf("%q: got %q want %q", test.input, got, test.want)
		}
	}
	if got := string(ColumnHTML("a * literal\n\nline one\nline two\nline three\n\njl")); got != "<p>a * literal</p>\n<p class=\"pool-vers\">line one<br>\nline two<br>\nline three</p>\n<p class=\"pool-signatur\">jl</p>" {
		t.Error(got)
	}
}
