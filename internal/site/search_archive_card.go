package site

import "strings"

// archiveCardExcerpt is a presentation of known exported record fields, not a
// replacement for the stored evidence text. Unknown technical fields are omitted;
// the complete original record and every assertion remain in the entity reader.
func archiveCardExcerpt(text string, metadata publicSearchMetadata, lang string) string {
	var notes, values, sources []string
	predicate := archivePredicateLabel(metadata.Predicate, lang)
	valueLabels := map[string][2]string{
		"document_type": {"Dokumentart", "Document type"}, "event_type": {"Ereignis", "Event"}, "place_type": {"Ort", "Place"},
		"organization_type": {"Organisation", "Organization"}, "language": {"Sprache", "Language"},
		"birth": {"Geboren", "Born"}, "death": {"Gestorben", "Died"},
		"about": {"Über", "About"}, "reviews": {"Bespricht", "Reviews"}, "derived_from": {"Grundlage", "Based on"},
		"agent_ref": {"Beteiligt", "Participant"}, "roles": {"Rolle", "Role"}, "instrument": {"Instrument", "Instrument"},
		"credited_as": {"Genannt als", "Credited as"}, "valid_time": {"Zeitraum", "Period"},
	}
	for _, line := range strings.Split(text, "\n") {
		key, value, ok := strings.Cut(strings.TrimSpace(line), ":")
		value = strings.TrimSpace(value)
		if !ok || value == "" {
			continue
		}
		switch {
		case key == "Anmerkung" || key == "note":
			notes = append(notes, value)
		case key == "quote":
			notes = append(notes, searchMessage(lang, "Aus der Quelle: „", "From the source: “")+value+searchMessage(lang, "“", "”"))
		case key == "edtf_value":
			values = append(values, searchMessage(lang, "Zeitangabe: ", "Date: ")+value)
		case key == "status_value":
			values = append(values, entityLabel(value, lang))
		case strings.HasSuffix(key, "_value"):
			if predicate != "" {
				values = append(values, predicate+": "+value)
			} else {
				values = append(values, value)
			}
		case key == "locator":
			sources = append(sources, searchMessage(lang, "Quelle: ", "Source: ")+value)
		case strings.HasPrefix(key, "Beleg ("):
			sources = append(sources, searchMessage(lang, "Quelle: ", "Source: ")+value)
		default:
			if label, ok := valueLabels[key]; ok {
				if key == "event_type" || key == "document_type" || key == "place_type" || key == "roles" {
					value = archiveCardEnum(value, lang)
				}
				values = append(values, searchMessage(lang, label[0], label[1])+": "+value)
			}
		}
	}
	// Meaningful uncertainty remains visible; absent/default rank and certainty
	// are not prose, and are available in the complete record instead.
	var parts []string
	if metadata.Rank == "deprecated" {
		parts = append(parts, searchMessage(lang, "Verworfene Angabe.", "Deprecated statement."))
	}
	switch metadata.Certainty {
	case "uncertain":
		parts = append(parts, searchMessage(lang, "Unsichere Angabe.", "Uncertain statement."))
	case "approximate":
		parts = append(parts, searchMessage(lang, "Ungefähre Angabe.", "Approximate statement."))
	}
	parts = append(parts, notes...)
	parts = append(parts, values...)
	parts = append(parts, sources...)
	seen := map[string]bool{}
	unique := make([]string, 0, len(parts))
	for _, part := range parts {
		if !seen[part] {
			seen[part] = true
			unique = append(unique, part)
		}
	}
	if len(unique) == 0 {
		return searchMessage(lang, "Angaben und Quellenhinweise im Archiveintrag ansehen.", "Explore statements and source references in the archive record.")
	}
	return searchExcerpt(strings.Join(unique, " · "), 320)
}
func archiveCardEnum(value, lang string) string {
	labels := map[string][2]string{
		"concert_announcement": {"Konzertankündigung", "Concert announcement"}, "concert_review": {"Konzertbericht", "Concert review"},
		"review": {"Rezension", "Review"}, "interview": {"Interview", "Interview"}, "obituary": {"Nachruf", "Obituary"},
		"news": {"Meldung", "News"}, "notice": {"Meldung", "Notice"}, "article": {"Artikel", "Article"}, "profile": {"Porträt", "Profile"},
		"venue": {"Spielstätte", "Venue"}, "city": {"Stadt", "City"}, "country": {"Land", "Country"},
	}
	var values []string
	for _, part := range strings.Split(value, " | ") {
		if label, ok := labels[part]; ok {
			values = append(values, searchMessage(lang, label[0], label[1]))
		} else {
			values = append(values, entityLabel(part, lang))
		}
	}
	return strings.Join(values, " · ")
}

func archivePredicateLabel(key, lang string) string {
	labels := map[string][2]string{
		"time": {"Zeitangabe", "Date"}, "took_place_at": {"Spielstätte", "Venue"}, "performance_status": {"Durchführung", "Performance"},
		"participants": {"Mitwirkende", "Participants"}, "names": {"Name", "Name"}, "identifiers": {"Weitere Kennung", "Other identifier"},
		"published": {"Veröffentlichung", "Publication"}, "published_in": {"Erschienen in", "Published in"}, "located_in": {"Ort", "Location"},
		"part_of": {"Teil von", "Part of"}, "members": {"Mitgliedschaft", "Membership"}, "performs_as": {"Künstlername", "Stage name"},
	}
	if label, ok := labels[key]; ok {
		return searchMessage(lang, label[0], label[1])
	}
	return ""
}
