package search

import (
	"context"
	"encoding/json"
	"sort"
	"sync"
)

var sections = []string{"music", "live", "timeline", "writing", "press", "biography", "site"}

const sectionCandidates = 4
const sectionResults = 3

func validSection(section string) bool {
	for _, s := range sections {
		if s == section {
			return true
		}
	}
	return false
}
func hitSection(h Hit) string {
	var m struct {
		Section string `json:"section"`
	}
	_ = json.Unmarshal(h.Metadata, &m)
	if validSection(m.Section) {
		return m.Section
	}
	return "site"
}
func documentKey(h Hit) string {
	if h.DocumentID != "" {
		return h.DocumentID
	}
	return h.ID
}
func sortHits(hits []Hit) {
	sort.SliceStable(hits, func(i, j int) bool {
		if hits[i].Score == hits[j].Score {
			return hits[i].ID < hits[j].ID
		}
		return hits[i].Score > hits[j].Score
	})
}
func querySections(q Query) []string {
	if q.Section != "" {
		return []string{q.Section}
	}
	out := make([]string, 0, len(sections))
	for _, section := range sections {
		// Automatic subdivision must never turn biography into an implicit opt-in.
		if section == "biography" && q.Voice != "pastiche" {
			continue
		}
		out = append(out, section)
	}
	return out
}

// At most two SQL operations per retrieval list; hybrid shares the four-connection
// pool. All queued work observes the original request context and deadline.
func (s *Service) groupedRetrieve(ctx context.Context, q Query, vector []float32) ([]Hit, error) {
	targets := querySections(q)
	type result struct {
		hits []Hit
		err  error
	}
	results := make([]result, len(targets))
	jobs := make(chan int, len(targets))
	for i := range targets {
		jobs <- i
	}
	close(jobs)
	var wg sync.WaitGroup
	for worker := 0; worker < 2; worker++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range jobs {
				if ctx.Err() != nil {
					results[i].err = ErrUnavailable
					continue
				}
				child := q
				child.Section = targets[i]
				// Twelve distinct documents per list allow fusion to recover cross-list
				// candidates; only four per section are sent to the optional reranker.
				if vector == nil {
					results[i].hits, results[i].err = s.repo.Lexical(ctx, s.Manifest, child, 12)
				} else {
					results[i].hits, results[i].err = s.repo.Semantic(ctx, s.Manifest, child, vector, 12)
				}
			}
		}()
	}
	wg.Wait()
	out := make([]Hit, 0, 12*len(targets))
	for _, r := range results {
		if r.err != nil {
			return nil, r.err
		}
		out = append(out, r.hits...)
	}
	sortHits(out)
	return out, nil
}
func (s *Service) lexical(ctx context.Context, q Query, n int) ([]Hit, error) {
	if q.Grouped {
		return s.groupedRetrieve(ctx, q, nil)
	}
	return s.repo.Lexical(ctx, s.Manifest, q, n)
}
func (s *Service) semantic(ctx context.Context, q Query, v []float32, n int) ([]Hit, error) {
	if q.Grouped {
		return s.groupedRetrieve(ctx, q, v)
	}
	return s.repo.Semantic(ctx, s.Manifest, q, v, n)
}

// Fusion is by document for grouped search, while retaining an actual passage as
// evidence. The lexical representative wins when both lists cover a document.
func documentRRF(lists ...[]Hit) []Hit {
	scores := make(map[string]Hit)
	for _, list := range lists {
		seen := make(map[string]bool)
		for i, h := range list {
			k := documentKey(h)
			if seen[k] {
				continue
			}
			seen[k] = true
			old, ok := scores[k]
			if !ok {
				old = h
				old.Score = 0
			}
			old.Score += 1 / float64(60+i+1)
			scores[k] = old
		}
	}
	out := make([]Hit, 0, len(scores))
	for _, h := range scores {
		out = append(out, h)
	}
	sortHits(out)
	return out
}

// Max 7*4=28 candidates, irrespective of requested limit; no section can consume
// the entire rerank budget with many paragraphs from the same document.
func groupedCandidates(hits []Hit) []Hit {
	count := map[string]int{}
	seen := map[string]bool{}
	out := make([]Hit, 0, 28)
	for _, h := range hits {
		k := documentKey(h)
		section := hitSection(h)
		if seen[k] || count[section] >= sectionCandidates {
			continue
		}
		seen[k] = true
		count[section]++
		out = append(out, h)
	}
	return out
}
func groupedResults(hits []Hit, limit int) []Hit {
	groups := map[string][]Hit{}
	order := []string{}
	seen := map[string]bool{}
	for _, h := range hits {
		section := hitSection(h)
		key := documentKey(h)
		if seen[key] || len(groups[section]) >= sectionResults {
			continue
		}
		seen[key] = true
		if len(groups[section]) == 0 {
			order = append(order, section)
		}
		groups[section] = append(groups[section], h)
	}
	// Reserve one result per relevant nonempty section before taking second/third.
	selected := map[string]int{}
	remaining := limit
	for round := 0; round < sectionResults && remaining > 0; round++ {
		for _, section := range order {
			if remaining == 0 {
				break
			}
			if len(groups[section]) > round {
				selected[section]++
				remaining--
			}
		}
	}
	out := make([]Hit, 0, limit)
	for _, section := range order {
		out = append(out, groups[section][:selected[section]]...)
	}
	return out
}
