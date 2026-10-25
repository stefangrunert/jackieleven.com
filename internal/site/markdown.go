package site

// These deliberately small readers reproduce the published PHP reading edition.
// Markdown files remain the editorial sources; no rendered-page snapshots are used.
import (
	"fmt"
	"html"
	"html/template"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

var (
	mdBlank               = regexp.MustCompile(`\n\s*\n`)
	mdSpace               = regexp.MustCompile(`\s+`)
	mdLine                = regexp.MustCompile(`\s*\n\s*`)
	mdStrong              = regexp.MustCompile(`(?s)\*\*(.+?)\*\*`)
	mdLink                = regexp.MustCompile(`\[([^\]]+)\]\(([^)\s]+)\)`)
	mdHeading             = regexp.MustCompile(`(?s)\A(#{2,6})\s+(.*)\z`)
	mdQuote               = regexp.MustCompile(`(?m)^> ?`)
	mdRule                = regexp.MustCompile(`\A-{3,}\z`)
	mdFront               = regexp.MustCompile(`(?s)\A---\n.*?\n---\n`)
	mdApparatus           = regexp.MustCompile(`(?m)^## `)
	mdChapterHead         = regexp.MustCompile(`(?m)^#\s+.*$`)
	mdChapterEnd          = regexp.MustCompile(`\n-{3,}\s*\z`)
	mdInitialQuote        = regexp.MustCompile(`\A\s*((?:>.*(?:\n|$))+)`)
	mdWarning             = regexp.MustCompile(`^\*\*(Hinweis|Note):\*\*`)
	columnFront           = regexp.MustCompile(`(?s)\A---\n(.*?)\n---\n(.*)\z`)
	columnField           = regexp.MustCompile(`(?m)^([a-z_]+):\s*"([^"\n]*)"\s*$`)
	columnDate            = regexp.MustCompile(`-(june|aug)-08\.php$`)
	columnTitle           = regexp.MustCompile(`\A\s*# [^\n]*\n`)
	columnImage           = regexp.MustCompile(`(?m)^!\[[^\]]*\]\(bilder/[^)]+\)\s*$`)
	columnSequence        = regexp.MustCompile(`^\d{4}-\d{2}(?:-([a-z0-9]+))?_`)
	columnRule            = regexp.MustCompile(`(?m)^(-{3,})[ \t]*$`)
	columnUpper           = regexp.MustCompile(`[A-Z]`)
	columnLower           = regexp.MustCompile(`[a-z]`)
	columnRepeatedHeading = regexp.MustCompile(`\A(?:Monthly column - [A-Za-z]+ \d{4}|THE DEEP POOL(?: - [A-Z]+ \d{4}(?: - no\.\d+)?)?)\n\s*\n`)
)

func mdEscape(s string) string {
	return strings.NewReplacer("&#39;", "&#039;", "&#34;", "&quot;").Replace(html.EscapeString(s))
}
func mdTrim(s string) string { return strings.Trim(s, " \t\n\r\x00\x0b") }
func mdWord(c byte) bool {
	return c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '_' || c == '*'
}
func mdWhitespace(c byte) bool {
	return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\v' || c == '\f'
}

// PHP's emphasis expression uses lookaround; RE2 does not. Match its bytewise
// boundaries directly, after escaping and replacing bold spans.
func mdEmphasis(s string) string {
	var b strings.Builder
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] != '*' || i > 0 && mdWord(s[i-1]) || i+1 >= len(s) || mdWhitespace(s[i+1]) {
			continue
		}
		for j := i + 2; j < len(s); j++ {
			if s[j] != '*' || mdWhitespace(s[j-1]) || j+1 < len(s) && mdWord(s[j+1]) {
				continue
			}
			b.WriteString(s[start:i])
			b.WriteString("<em>")
			b.WriteString(s[i+1 : j])
			b.WriteString("</em>")
			start = j + 1
			i = j
			break
		}
	}
	b.WriteString(s[start:])
	return b.String()
}

func MarkdownInline(s string) template.HTML {
	s = mdStrong.ReplaceAllString(mdEscape(s), "<strong>${1}</strong>")
	s = mdEmphasis(s)
	s = mdLink.ReplaceAllStringFunc(s, func(link string) string {
		m := mdLink.FindStringSubmatch(link)
		url := html.UnescapeString(m[2])
		if strings.HasPrefix(url, "https://") || strings.HasPrefix(url, "http://") {
			return `<a href="` + m[2] + `" rel="noopener noreferrer">` + m[1] + `</a>`
		}
		return m[1]
	})
	return template.HTML(s) // Only escaped text and the fixed tags above can reach this boundary.
}

func Markdown(text string) template.HTML {
	out := []string{}
	for _, block := range mdBlank.Split(mdTrim(text), -1) {
		block = mdTrim(block)
		if block == "" || mdRule.MatchString(block) {
			continue
		}
		if m := mdHeading.FindStringSubmatch(block); m != nil {
			n := len(m[1])
			out = append(out, fmt.Sprintf("<h%d>%s</h%d>", n, MarkdownInline(m[2]), n))
		} else if strings.HasPrefix(block, ">") {
			out = append(out, "<blockquote>"+string(Markdown(mdQuote.ReplaceAllString(block, "")))+"</blockquote>")
		} else {
			out = append(out, "<p>"+string(MarkdownInline(mdLine.ReplaceAllString(block, " ")))+"</p>")
		}
	}
	return template.HTML(strings.Join(out, "\n"))
}

func ColumnHTML(text string) template.HTML {
	text = columnRule.ReplaceAllString(text, "\n${1}\n")
	out := []string{}
	for _, block := range mdBlank.Split(mdTrim(text), -1) {
		block = mdTrim(block)
		if block == "" {
			continue
		}
		if mdRule.MatchString(block) {
			out = append(out, "<hr>")
			continue
		}
		if block == "jl" {
			out = append(out, `<p class="pool-signatur">jl</p>`)
			continue
		}
		if len(block) < 120 && columnUpper.MatchString(block) && !columnLower.MatchString(block) {
			out = append(out, "<h2>"+mdEscape(mdSpace.ReplaceAllString(block, " "))+"</h2>")
			continue
		}
		lines := strings.Split(block, "\n")
		max := 0
		for _, line := range lines {
			if len(line) > max {
				max = len(line)
			}
		}
		if len(lines) > 2 && max < 68 {
			out = append(out, `<p class="pool-vers">`+strings.ReplaceAll(mdEscape(block), "\n", "<br>\n")+"</p>")
		} else {
			out = append(out, "<p>"+mdEscape(mdLine.ReplaceAllString(block, " "))+"</p>")
		}
	}
	return template.HTML(strings.Join(out, "\n"))
}

func chapterParts(path string) map[string]string {
	parts := map[string]string{"anmerkung": "", "text": "", "apparat": ""}
	data, err := os.ReadFile(path)
	if err != nil {
		return parts
	}
	raw := mdFront.ReplaceAllString(strings.ReplaceAll(string(data), "\r\n", "\n"), "")
	front := raw
	if loc := mdApparatus.FindStringIndex(raw); loc != nil {
		front = raw[:loc[0]]
		parts["apparat"] = mdTrim(raw[loc[0]:])
	}
	if m := mdInitialQuote.FindStringSubmatchIndex(front); m != nil {
		head := mdBlank.Split(mdTrim(mdQuote.ReplaceAllString(front[m[2]:m[3]], "")), -1)
		keep := []string{}
		for _, p := range head {
			if !mdWarning.MatchString(mdTrim(p)) {
				keep = append(keep, p)
			}
		}
		parts["anmerkung"] = mdTrim(strings.Join(keep, "\n\n"))
		front = front[m[1]:]
	}
	if loc := mdChapterHead.FindStringIndex(front); loc != nil {
		front = front[:loc[0]] + front[loc[1]:]
	}
	parts["text"] = mdTrim(mdChapterEnd.ReplaceAllString(strings.TrimRight(front, " \t\n\r\x00\x0b"), ""))
	return parts
}

func ChapterParts(root, slug, lang string) map[string]any {
	result := map[string]any{}
	// Slugs originate in the published chapter allowlist. Validate before path use.
	if !regexp.MustCompile(`^[a-z0-9-]+$`).MatchString(slug) || lang != "de" && lang != "en" {
		return result
	}
	source := chapterParts(filepath.Join(root, "autobiografie", slug+".md"))
	translated := chapterParts(filepath.Join(root, "autobiografie", lang, slug+".md"))
	for part, origin := range map[string]string{"anmerkung": "de", "text": "en", "apparat": "de"} {
		if translated[part] != "" {
			result[part] = []any{translated[part], lang}
		} else {
			result[part] = []any{source[part], origin}
		}
	}
	return result
}

func ColumnReadingText(k map[string]any) string {
	text, _ := k["text"].(string)
	if k["art"] != "deep-pool" {
		return text
	}
	for {
		next := columnRepeatedHeading.ReplaceAllString(text, "")
		if next == text {
			return text
		}
		text = next
	}
}

func LoadColumns(root string, files []string) ([]any, error) {
	columns := []map[string]any{}
	for _, file := range files {
		if filepath.Base(file) != file || !strings.HasSuffix(file, ".md") {
			return nil, fmt.Errorf("invalid column filename: %s", file)
		}
		data, err := os.ReadFile(filepath.Join(root, "research", "columns", file))
		if err != nil {
			return nil, err
		}
		m := columnFront.FindStringSubmatch(strings.ReplaceAll(string(data), "\r\n", "\n"))
		if m == nil {
			return nil, fmt.Errorf("column frontmatter missing: %s", file)
		}
		meta := map[string]string{}
		for _, field := range columnField.FindAllStringSubmatch(m[1], -1) {
			meta[field[1]] = field[2]
		}
		pieces := strings.Split(file, "_")
		if len(pieces) < 2 {
			return nil, fmt.Errorf("invalid column name: %s", file)
		}
		art := pieces[1]
		date := meta["datum"]
		dating := "archivdatum"
		if art == "deep-pool" {
			dating = "ausgabe"
		}
		if match := columnDate.FindStringSubmatch(meta["quelle"]); match != nil {
			date = "2008-08"
			if match[1] == "june" {
				date = "2008-06"
			}
			dating = "ausgabe"
		}
		text := mdTrim(columnTitle.ReplaceAllString(m[2], ""))
		title := meta["titel"]
		if art != "deep-pool" && art != "ankuendigung" && title != "." && !strings.HasSuffix(title, "…") && !strings.HasPrefix(mdSpace.ReplaceAllString(text, " "), title) {
			text = title + "\n\n" + text
		}
		if file == "2007-09_deep-pool_september-2007.md" {
			text = strings.TrimPrefix(text, "A\nugust 2006\n\nMarch 2003a\n\n")
		}
		text = mdTrim(columnImage.ReplaceAllString(text, ""))
		sequence := ""
		if match := columnSequence.FindStringSubmatch(file); match != nil {
			sequence = match[1]
		}
		website := "jackieleven.co.uk"
		if strings.Contains(meta["quelle"], "home.xnet.it") {
			website = "jackieleven.com"
		}
		columns = append(columns, map[string]any{"slug": strings.ReplaceAll(strings.TrimSuffix(file, ".md"), "_", "-"), "datei": file, "datum": date, "datierung": dating, "art": art, "autor": meta["autor"], "archiv": meta["archiv"], "quelle": meta["quelle"], "capture": meta["capture"], "website": website, "text": text, "folge": sequence, "nummer": nil})
	}
	sort.SliceStable(columns, func(i, j int) bool {
		for _, key := range []string{"datum", "art", "folge", "capture", "datei"} {
			a := columns[i][key].(string)
			b := columns[j][key].(string)
			if a != b {
				return a < b
			}
		}
		return false
	})
	groups := map[string][]int{}
	for i, k := range columns {
		key := k["datum"].(string) + "/" + k["art"].(string)
		groups[key] = append(groups[key], i)
	}
	for _, indices := range groups {
		if len(indices) > 1 {
			for n, i := range indices {
				columns[i]["nummer"] = n + 1
			}
		}
	}
	result := make([]any, len(columns))
	for i, k := range columns {
		result[i] = k
	}
	return result, nil
}
