package site

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/url"
	"sort"
	"strings"
)

type searchEntityView struct {
	ID, Title, Type, Note, Raw string
	Facts                      []searchEntityFact
}
type searchEntityFact struct {
	Label  string
	Values []searchEntityValue
}
type searchEntityValue struct {
	Text, Link, Note, Status, ID string
	References                   []searchEntityReference
}
type searchEntityReference struct{ Title, Link, Locator, Quote, Kind string }

func (a *App) searchEntityURL(id, lang string) string {
	route := "/de/suche/objekt"
	if lang == "en" {
		route = "/en/search/entity"
	}
	return a.basePath + route + "?" + url.Values{"id": {id}}.Encode()
}
func entityLabel(key, lang string) string {
	labels := map[string][2]string{
		"Event": {"Ereignis", "Event"}, "Place": {"Ort", "Place"}, "Person": {"Person", "Person"}, "Document": {"Dokument", "Document"}, "Work": {"Werk", "Work"}, "Recording": {"Aufnahme", "Recording"}, "Release": {"Veröffentlichung", "Release"}, "Group": {"Gruppe", "Group"}, "Organization": {"Organisation", "Organization"}, "Persona": {"Künstlername", "Stage name"},
		"time": {"Zeitangaben", "Dates"}, "date": {"Datum", "Date"}, "publication_date": {"Erscheinungsdatum", "Publication date"}, "performance_status": {"Durchführung", "Performance status"}, "took_place_at": {"Ort", "Location"}, "participants": {"Mitwirkende", "Participants"}, "event_type": {"Art des Ereignisses", "Event type"}, "performs_as": {"Künstlernamen", "Stage names"}, "published_by": {"Veröffentlicht von", "Published by"}, "published_in": {"Erschienen in", "Published in"}, "creator": {"Urheber", "Creator"}, "author": {"Autor", "Author"}, "authors": {"Autoren", "Authors"}, "language": {"Sprache", "Language"}, "document_type": {"Dokumentart", "Document type"}, "subject": {"Gegenstand", "Subject"}, "about": {"Über", "About"}, "part_of": {"Teil von", "Part of"}, "located_in": {"Liegt in", "Located in"}, "same_as": {"Weitere Kennung", "Other identifier"}, "url": {"Adresse", "Address"}, "title": {"Titel", "Title"}, "aliases": {"Weitere Namen", "Other names"}, "description": {"Beschreibung", "Description"}, "roles": {"Rollen", "Roles"}, "scope": {"Geltungsbereich", "Scope"}, "note": {"Anmerkung", "Note"}, "certainty": {"Sicherheit", "Certainty"}, "rank": {"Rang der Aussage", "Statement rank"}, "status": {"Status", "Status"}, "type": {"Art", "Type"},
		"announced": {"Angekündigt", "Announced"}, "took_place": {"Als stattgefunden belegt", "Documented as having taken place"}, "cancelled": {"Abgesagt", "Cancelled"}, "unknown": {"Ungeklärt", "Unknown"}, "uncertain": {"Unsicher", "Uncertain"}, "approximate": {"Ungefähr", "Approximate"}, "disputed": {"Umstritten", "Disputed"}, "normal": {"Normal", "Normal"}, "preferred": {"Bevorzugt", "Preferred"}, "deprecated": {"Verworfen", "Deprecated"}, "concert": {"Konzert", "Concert"}, "vocals": {"Gesang", "Vocals"}, "guitar": {"Gitarre", "Guitar"}, "third_party": {"Fremde Quelle", "Third-party source"}, "inferred": {"Erschlossen", "Inferred"}, "self_report": {"Eigene Aussage", "Self-report"},
	}
	if label, ok := labels[key]; ok {
		return searchMessage(lang, label[0], label[1])
	}
	return strings.ReplaceAll(key, "_", " ")
}
func (a *App) searchEntity(raw json.RawMessage, lang string) *searchEntityView {
	var data map[string]any
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	if dec.Decode(&data) != nil {
		return nil
	}
	result := &searchEntityView{ID: entityScalar(data["id"]), Title: entityScalar(data["label"]), Type: entityLabel(entityScalar(data["type"]), lang), Note: entityScalar(data["note"])}
	if result.Title == "" {
		result.Title = entityScalar(data["title"])
	}
	if result.Title == "" {
		result.Title = result.ID
	}
	var b bytes.Buffer
	encoder := json.NewEncoder(&b)
	encoder.SetEscapeHTML(false)
	encoder.SetIndent("", "  ")
	if encoder.Encode(data) == nil {
		result.Raw = b.String()
	}
	keys := make([]string, 0, len(data))
	for key := range data {
		switch key {
		case "id", "label", "type", "note", "recorded_by":
			continue
		}
		keys = append(keys, key)
	}
	sort.Strings(keys)
	// Keep every assertion. Ordering fields never chooses between contradictory values.
	for _, key := range keys {
		fact := searchEntityFact{Label: entityLabel(key, lang)}
		items, ok := data[key].([]any)
		if !ok {
			items = []any{data[key]}
		}
		for _, item := range items {
			fact.Values = append(fact.Values, a.searchEntityValue(item, lang))
		}
		if len(fact.Values) > 0 {
			result.Facts = append(result.Facts, fact)
		}
	}
	return result
}
func entityScalar(value any) string {
	switch v := value.(type) {
	case string:
		return v
	case json.Number:
		return v.String()
	case bool:
		return fmt.Sprint(v)
	case nil:
		return ""
	}
	return ""
}
func entityReadable(value any, lang string) string {
	if scalar := entityScalar(value); scalar != "" {
		return entityLabel(scalar, lang)
	}
	switch v := value.(type) {
	case []any:
		items := make([]string, 0, len(v))
		for _, item := range v {
			items = append(items, entityReadable(item, lang))
		}
		return strings.Join(items, " · ")
	case map[string]any:
		keys := make([]string, 0, len(v))
		for key := range v {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		var parts []string
		for _, key := range keys {
			parts = append(parts, entityLabel(key, lang)+": "+entityReadable(v[key], lang))
		}
		return strings.Join(parts, "; ")
	}
	return ""
}
func (a *App) searchEntityValue(value any, lang string) searchEntityValue {
	out := searchEntityValue{}
	statement, ok := value.(map[string]any)
	if !ok {
		out.Text = entityReadable(value, lang)
		return out
	}
	out.Note = entityScalar(statement["note"])
	out.ID = entityScalar(statement["statement_id"])
	var text []string
	keys := make([]string, 0, len(statement))
	for key := range statement {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		item := statement[key]
		switch key {
		case "references", "recorded_by", "statement_id", "note":
			continue
		case "certainty", "rank", "status":
			if out.Status != "" {
				out.Status += " · "
			}
			out.Status += entityLabel(key, lang) + ": " + entityReadable(item, lang)
		case "entity_value", "agent_ref":
			id := entityScalar(item)
			out.Link = a.searchEntityURL(id, lang)
			text = append(text, id)
		case "edtf_value", "string_value", "text_value", "value", "status_value", "number_value":
			text = append(text, entityReadable(item, lang))
		default:
			text = append(text, entityLabel(key, lang)+": "+entityReadable(item, lang))
		}
	}
	out.Text = strings.Join(text, " · ")
	if refs, ok := statement["references"].([]any); ok {
		for _, item := range refs {
			ref, ok := item.(map[string]any)
			if !ok {
				continue
			}
			id := entityScalar(ref["document"])
			title := entityScalar(ref["locator"])
			if title == "" {
				title = id
			}
			evidence := searchEntityReference{Title: title, Locator: entityScalar(ref["scope"]), Quote: entityScalar(ref["quote"]), Kind: entityLabel(entityScalar(ref["evidence_type"]), lang)}
			if id != "" {
				evidence.Link = a.searchEntityURL(id, lang)
			}
			out.References = append(out.References, evidence)
		}
	}
	return out
}
