package site

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
)

// M is a content record. Catalog records deliberately retain their published JSON
// field names; HTTP routing and request state use concrete Go types.
type M = map[string]any
type Pair struct {
	Key   any
	Value any
}
type Data struct {
	Values    M
	Languages map[string]M
	Texts     map[string]M
	Columns   []any
	Sources   []any
}

func loadData(root string) (*Data, error) {
	d := &Data{Values: M{}, Languages: map[string]M{}, Texts: map[string]M{}}
	for _, name := range []string{"stationen", "pastiche", "startseite", "hoeren", "kolumnen", "diskografie", "diskografie-details", "diskografie-hoerlinks", "youtube-titel", "live-videos", "quellen", "quellen-scans", "quellen-auszuege"} {
		b, err := os.ReadFile(filepath.Join(root, "data", name+".json"))
		if err != nil {
			return nil, err
		}
		var v any
		if err = json.Unmarshal(b, &v); err != nil {
			return nil, fmt.Errorf("%s: %w", name, err)
		}
		d.Values[name] = v
	}
	for _, l := range []string{"de", "en"} {
		for _, kind := range []string{"lang", "texte"} {
			b, err := os.ReadFile(filepath.Join(root, "data", kind, l+".json"))
			if err != nil {
				return nil, err
			}
			v := M{}
			if err = json.Unmarshal(b, &v); err != nil {
				return nil, err
			}
			if kind == "lang" {
				d.Languages[l] = v
			} else {
				d.Texts[l] = v
			}
		}
	}
	var files []string
	for _, f := range listValue(get(d.Values["kolumnen"], "dateien")) {
		files = append(files, str(f))
	}
	var err error
	d.Columns, err = LoadColumns(root, files)
	if err != nil {
		return nil, err
	}
	for _, v := range listValue(d.Values["quellen"]) {
		q := cloneMap(v)
		id := str(q["id"])
		q["auszuege"] = coalesce(get(d.Values["quellen-auszuege"], id), []any{})
		q["scan"] = coalesce(get(d.Values["quellen-scans"], id), M{"pages": "", "facsimiles": []any{}})
		scan := asMap(q["scan"])
		if truth(scan["manifest"]) {
			q["url"] = scan["url"]
			q["lizenz"] = nil
			if truth(scan["license"]) && truth(scan["public_access"]) {
				q["lizenz"] = M{"name": scan["license"], "checked": scan["checked"]}
				q["zugang"] = "frei"
			} else if q["zugang"] == "frei" {
				q["zugang"] = "online"
			}
		}
		d.Sources = append(d.Sources, q)
	}
	return d, nil
}
func str(v any) string {
	if v == nil {
		return ""
	}
	switch x := v.(type) {
	case string:
		return x
	case bool:
		if x {
			return "1"
		}
		return ""
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	default:
		return fmt.Sprint(x)
	}
}
func num(v any) int {
	if n, ok := v.(int); ok {
		return n
	}
	f, _ := strconv.ParseFloat(str(v), 64)
	return int(f)
}
func truth(v any) bool {
	if v == nil {
		return false
	}
	switch x := v.(type) {
	case bool:
		return x
	case string:
		return x != "" && x != "0"
	case int:
		return x != 0
	case float64:
		return x != 0
	}
	rv := reflect.ValueOf(v)
	switch rv.Kind() {
	case reflect.Map, reflect.Slice, reflect.Array:
		return rv.Len() > 0
	}
	return true
}
func get(v any, key any) any {
	switch a := v.(type) {
	case M:
		return a[str(key)]
	case []any:
		i := num(key)
		if i >= 0 && i < len(a) {
			return a[i]
		}
	case []Pair:
		for _, p := range a {
			if equal(p.Key, key) {
				return p.Value
			}
		}
	case Pair:
		if str(key) == "Key" {
			return a.Key
		}
		if str(key) == "Value" {
			return a.Value
		}
	}
	return nil
}
func asMap(v any) M {
	if m, ok := v.(M); ok {
		return m
	}
	return M{}
}
func cloneMap(v any) M {
	m := M{}
	for k, v := range asMap(v) {
		m[k] = v
	}
	return m
}
func listValue(v any) []any {
	if a, ok := v.([]any); ok {
		return a
	}
	return nil
}
func pairs(v any) []Pair {
	if p, ok := v.([]Pair); ok {
		return p
	}
	var p []Pair
	switch a := v.(type) {
	case []any:
		for i, x := range a {
			p = append(p, Pair{i, x})
		}
	case M:
		keys := make([]string, 0, len(a))
		for k := range a {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			p = append(p, Pair{k, a[k]})
		}
	}
	return p
}
func dict(args ...any) M {
	m := M{}
	for i := 0; i+1 < len(args); i += 2 {
		m[str(args[i])] = args[i+1]
	}
	return m
}
func coalesce(a, b any) any {
	if a == nil {
		return b
	}
	return a
}
func equal(a, b any) bool {
	if a == nil || b == nil {
		return a == nil && b == nil
	}
	if isContainer(a) && isContainer(b) && count(a) == 0 && count(b) == 0 {
		return true
	}
	if isNumber(a) && isNumber(b) {
		return num(a) == num(b)
	}
	return reflect.DeepEqual(a, b)
}
func isNumber(a any) bool {
	switch a.(type) {
	case int, float64:
		return true
	}
	return false
}
func contains(a any, v any) bool {
	for _, p := range pairs(a) {
		if equal(p.Value, v) {
			return true
		}
	}
	return false
}
func count(a any) int { return len(pairs(a)) }
func join(sep string, a any) string {
	var out []string
	for _, p := range pairs(a) {
		out = append(out, str(p.Value))
	}
	return strings.Join(out, sep)
}
func filtered(a any) []any {
	var out []any
	for _, p := range pairs(a) {
		if truth(p.Value) {
			out = append(out, p.Value)
		}
	}
	return out
}
func slice(a any, start int) []any {
	x := listValue(a)
	if start < 0 {
		start = len(x) + start
	}
	if start < 0 {
		start = 0
	}
	if start > len(x) {
		return nil
	}
	return x[start:]
}
func group(a []any, key func(any) string) []Pair {
	var out []Pair
	indices := map[string]int{}
	for _, v := range a {
		k := key(v)
		i, ok := indices[k]
		if !ok {
			i = len(out)
			indices[k] = i
			out = append(out, Pair{k, []any{}})
		}
		out[i].Value = append(listValue(out[i].Value), v)
	}
	return out
}
func find(a []any, key, id string) int {
	for i, v := range a {
		if str(get(v, key)) == id {
			return i
		}
	}
	return -1
}

func isContainer(a any) bool {
	switch a.(type) {
	case M, []any, []Pair:
		return true
	}
	return false
}
