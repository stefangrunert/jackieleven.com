package site

import (
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
)

var basePathPattern = regexp.MustCompile(`^(?:/[A-Za-z0-9_-]+)+$`)

func normalizeBasePath(path string) (string, error) {
	if path == "" || path == "/" {
		return "", nil
	}
	path = strings.TrimSuffix(path, "/")
	if !basePathPattern.MatchString(path) {
		return "", fmt.Errorf("invalid base path %q: use slash-separated letters, digits, hyphens or underscores", path)
	}
	return path, nil
}

// assetURL leaves external sources intact and mounts only the local asset tree.
func (c *request) assetURL(value any) string {
	path := str(value)
	if strings.HasPrefix(path, "/assets/") {
		return c.app.basePath + path
	}
	return path
}

func (c *request) alternativesJSON(canonical bool, slug ...string) string {
	urls := M{}
	for _, language := range []string{"de", "en", "x-default"} {
		lang := language
		if lang == "x-default" {
			lang = "de"
		}
		route, params := "zeitreise", M{}
		if len(slug) > 0 {
			route = "station"
			params["slug"] = slug[0]
		}
		if canonical {
			urls[language] = c.routePath(route, params, lang)
		} else {
			urls[language] = c.url(route, params, lang)
		}
	}
	encoded, _ := json.Marshal(urls)
	return string(encoded)
}
