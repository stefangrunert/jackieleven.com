# How Jackie Leven acquired an autobiography he never wrote

Workshop report on Stefan and Claude Code’s collaboration on jackieleven. Recorded on 17 September 2026, on the evening of the day the work began. It describes reconstructing Leven’s own websites from the Internet Archive, writing an invented autobiography in his voice, and above all what followed: removing AI language from a text whose content was already sound.

This is a historical account of that day’s work. German conversation excerpts and tool comments below are translated into English; quoted English prose and statistical results are preserved.

## A personal project

Stefan began with a sentence that set the standard for everything that followed:

> “We have a new project here, one particularly close to my heart.”

It was to be a tribute website for the Scottish songwriter Jackie Leven (1950–2011). A biographical compendium already existed: eight files assembled from major newspapers, music journalism, obituaries and discographies, with footnotes and documented contradictions. That was enough to build a site. But it was material *about* him.

## The detective assignment

> “First, more research. I have a detective assignment for you. I remember clearly that Jackie had his own homepage, which went offline after 2011. It had a blog, concert calendar and other things. Jackieleven uk or com or something. Find it in the web archive.”

One memory, two possible domains, no link. Searching the Internet Archive’s CDX interface yielded more than the memory promised: not one site, but three, in succession over thirty years.

**jackieleven.com** began in 1996 as a fan site run by an Italian, hosted at the unglamorous address `home.xnet.it/tout/HTML/`. From October 2002, Leven wrote a monthly column there, “The Deep Pool”. **jackieleven.co.uk** became the official site in 2008, with a blog and several sections; it continued until 2025 and was suspended by its host in 2024. **jackie-leven.com** is the memorial site established after his death.

That was the real discovery, larger than the assignment: Leven had written regularly for nine years. Not interviews or press copy, but his own prose, monthly, for an audience of perhaps a few hundred people.

## The harvest

> “Important: collect all the content from Jackie’s columns in research/colums. One file per post.”

> “The pictures too, if there are any.”

The result was **76 files containing around 90,000 words** in `research/columns/`, plus 19 images. The text was reproduced verbatim, including Leven’s habits: lowercase “i”, typing errors and idiosyncratic punctuation. Each file has a YAML header recording section, date, source URL, archive link and capture date.

Much of the work consisted of fixing our own mistakes, which are more revealing than the result:

- **Leading spaces** defeated the rules for removing navigation and headers. Every line needed trimming first.
- **Dividers within columns** used the same characters as dividers between columns. One text was split into four pieces. Only a narrower rule (`(\+-){4,}`) separated them correctly.
- **A similarity check with a 0.9 threshold** merged the November 2011 obituary with an August 2011 page because both carried the same navigation. Fuzzy merging was removed; only exact duplicates are now combined.
- **Umlauts in filenames** produced slugs such as `m-rz` for “März”. A transliteration table fixed this.

None of these mistakes was spectacular. Together they could have made the corpus unusable without anyone noticing: a collection of texts still looks complete when a quarter is missing.

One technical limitation belongs here: **subagents could not write files in this environment.** Their analyses ran correctly in parallel, but their reports were not saved. They had to be extracted from the agent-run transcripts. Subsequent assignments instructed agents to return their complete reports directly.

## Put the facts in order first

> “First put the facts in order, because they are the prerequisite for the book.”

The columns and reconstructed sites produced four further research files:

| File | Contents |
|---|---|
| `09-websites.md` | History of the three domains, operators, technology, inventory of the press and interview archive, gaps |
| `10-konzertkalender.md` | 470 performances from 1997–2011, combined from 26 calendar versions across both sites |
| `11-zeitleiste.md` | Continuous chronology with a separate table of all conflicting dates |
| `12-biografie-aus-den-kolumnen.md` | Facts from Leven’s own writing, arranged by topic, every fact with a source location |

The point of this order was to finish the facts *before* the prose. Writing first and supplying evidence afterwards means finding evidence for what you have already written.

The timeline therefore includes a table that reads almost like an admission: birthday (18 or 19 June), band formation (1975 according to Leven, 1977 according to everyone else), the assault (1983 or 1984), the type of cancer (three accounts, no primary source). For a man who liked embellishing his biography, the contradiction table is a research finding, not a defect.

## The outrageous idea

> “An outrageous idea occurs to me: what about letting Jackie write an autobiography? We now know his writing style, how he expresses himself, where his subtle humour, sarcasm and irony sit.”

Three decisions followed immediately: free pastiche in his voice rather than a montage of quotations; English, with a German version later; his whole life in twelve to fifteen chapters.

## The framework before the first sentence

The idea needed clear boundaries. `autobiografie/00-rahmen.md` establishes:

- The text is **not by Jackie Leven**. Every chapter carries this notice.
- It is **never published as Leven’s own words**, on the tribute site or elsewhere.
- **Every chapter ends with a “Documented / invented” section** listing both separately.

The reason appears in the framework itself: Leven was a notorious embellisher—Bob Dylan as an alleged co-writer, a professional killer as a song’s inspiration, his own whisky, later called “a complete scam” by his label boss. **His real recollections already sound invented.** If unlabelled fictional first-person prose sits beside them, nobody will later be able to distinguish his words from ours. For another author, labelling might be a courtesy. Here it is a condition.

In practice, the documented/invented section proved the project’s most useful instrument for an unexpected reason: after writing, it forces every sentence back to a source. This exposed a mistake in chapter 5 that would otherwise have remained. I had thought Tony Stratton Smith was dead when the solo contract was signed; he died in 1987, after the assault. The scene and its evidence note were corrected.

## Measure the voice before imitating it

Stylistically, the corpus falls into two phases, with a difference clear enough to count:

| | Columns 2002–2007 (43,600 words) | Blog 2008–2012 (46,900 words) |
|---|---|---|
| First person | 578 lowercase “i”, 257 “I” | 22 lowercase “i”, 829 “I” |
| Dash ` - ` | 22.8 per 1,000 words | 1.2 |
| Ellipses | 4.8 | 2.3 |
| Single quotation marks | 14.9 | 0.3 |
| Sentence length (median / longest) | 29 / 323 words | 26 / 157 words |

We chose the early column voice. Chapters 14 and 15 deliberately switch to the later blog voice with capital “I”, because they are set in the years when he wrote that way; their front matter records this.

This produced ten style rules and four traps. The most important rule was: **end a chapter with a quiet image, not a punchline.** The first draft broke it fifteen times.

## Fifteen chapters

The first draft was written in one pass. It was rich in content, kept facts properly separated, and Stefan read it with interest:

> “Yes, continue with chapters 7 to 15—I’m looking forward to reading them.”

## The objection

Then came the sentence around which the second half of the project took shape:

> “There are numerous formulations in the texts that are clearly AI, not Jackie. […] That pulls otherwise good content towards AI slop. This absolutely has to be prevented. You need to analyse it section by section and make the text more fluent, more ‘Leven-like’. We have already worked on language together in the Christ project, albeit for a different style. Don’t imitate that one-to-one, but understand why the language there became what I wanted.”

Five examples accompanied it:

> “Both facts are true. Only one of them is a room.”
> “Now the money, because nobody does the money.”
> “When he died i did the thing that men of my type do, which is that i went out and worked. Not a little.”
> “Kevin Coyne i never got to work with, and that is one of my real regrets.”
> “I never got the big audience. I got the right one.”

The crucial point was that we already had a benchmark. To ask “does this sound like Leven?”, we had 90,000 words by Leven. This led to `werkzeug/messen.py`, and the first measurement was uncomfortable:

| | Leven | First draft |
|---|---|---|
| Mean sentence length | 35.1 words | 21.5 |
| Sentence-length standard deviation | 30.0 | 17.9 |
| Longest sentence | 362 words | 99 |
| Sentences under 5 words | 2.1% | 12.6% |
| Dashes per 1,000 words | 20.1 | 8.5 |
| Ellipses per 1,000 words | 3.6 | 0.0 |
| Evaluative conclusion | 0.16 | 1.67 |
| Antithesis | 0.22 | 0.67 |
| Announcement | 0.16 | 0.47 |

Passive voice and nominal style were not the problem; neither was present. The problem was **rhythm**. Leven’s sentences meander through commas and dashes and often arrive nowhere. The first draft broke the same material into constructed units with neat landings: ten times as many evaluative conclusions, six times as many sentences under five words, and no ellipses where he averages one every three hundred words.

That is what “AI slop” means at sentence level here. Nothing is missing or incorrect. Every paragraph simply lands too neatly.

## The failed attempt: measurement as dogma

The correction immediately went wrong. I treated the mean as a target and increased sentence length to more than fifty words. Stefan stopped it in the next turn:

> “Stop—this mustn’t become mannerism. Now the text is horribly unreadable. You need a balance, not a dogma. Jackie’s texts aren’t always easy to read. We have to take that into account, especially because this is a long autobiography that people should actually read. Find the sweet spot.”

This was the day’s most important intervention, and the mistake deserves recording: **the mean was the wrong measure.** Leven’s characteristic figure is the variation—30 against a mean of 35. He writes twelve-word sentences and hundred-and-twenty-word sentences immediately after one another. The 362-word sentences are outliers in individual columns, not a general style. His own blog entry about the market-hall clock runs at 24, 30 and 15 words and reads effortlessly.

There is also a genre difference that no measurement captures: a fifteen-chapter autobiography is read differently from a two-thousand-word monthly column. What works as a quirk there becomes tiring over a hundred pages.

The new target: **a mean between 24 and 32 words, standard deviation above 20, and at most one or two sentences over eighty words per chapter.** The failed attempt and Stefan’s response are recorded in `00-sprache.md` so they will not be repeated.

## The second objection: the flat opening

> “Flat opening. Jackie would never have written: i was born in Kirkcaldy in the June of 1950, in the town that made linoleum for most of the world and produced one Prime Minister.”

Instead of guessing how he would have begun, we extracted thirty of his own column openings. The result was clear: **Leven begins with weather, place, season or the body. Never with biography.** Not one of his 979 paragraphs begins with a date phrase such as “In 1971…”, “On 14 November…” or “By 1983…”.

The revised first chapter begins:

> “May, and the hawthorn out all along the path by the railway line between Leslie and Markinch - ne'er cast a clout till May is out…”

The linoleum and Prime Minister remain, casually, two paragraphs later.

## The third objection: sentences that introduce rather than tell

> “Much better. Things where I can’t explain why they don’t sound real. Can you?”

Seven examples, all similarly constructed. Measurement revealed the pattern:

| | Leven | Pastiche |
|---|---|---|
| Paragraphs beginning “There was/is…” | 0.8% | 5.4% |
| Paragraphs beginning “X is/was a Y” | 1.3% | 7.7% |

This is the **register entry**: something is introduced to the reader before it does anything. Leven does not introduce things. They arrive in motion, through association, memory, or because he happens to pass them. “There is a ferry to Kerrera” therefore became “You go down to the slip for the Kerrera ferry and there is a board propped up there…”. The ferry still exists; the difference is that someone walks down to it.

## Sentence by sentence, through all fifteen chapters

> “Don’t limit this to those specific passages; they were examples. Take it into account generally, analysing sense and nonsense sentence by sentence. Then apply it to the chapters not yet rewritten. But again: don’t become dogmatic.”

This produced the second tool, `werkzeug/pruefen.py`. It flags ten sentence forms rare or absent in Leven: existential openings, copular definitions, dates at paragraph openings, backward-pointing clefts, evaluative continuations, antithesis, self-characterisation, announcements, numbered wisdom and suspected aphorisms. It also flags short paragraph endings as possible punchlines.

The first run across fifteen chapters produced more than a hundred candidates. Examples of changes:

| Figure | Before | After |
|---|---|---|
| Numbered wisdom | “**One.** … **Two.** … **Three.** … **Four.**” (chapter 15) | The same four thoughts as paragraphs, without numbering |
| Register entry | “Mikki Rain is the chieftain. John Ralph is the tribal seer.” | “Mikki Rain has been its chieftain since Dorset … John Ralph carries the relics about and does the seeing” |
| Staccato punchline | “Alone. Sitting. Watching somebody else's departure.” | “On my own, on the sand, watching other people leave, and pleased about it in a way i could not have defended to a committee.” |
| Sentence about itself | “That is a shameful sentence and it is accurate.” | “…and i have never yet found a way of putting that down which does not shame me while i am putting it down.” |
| Announcement | “Now the money, because nobody does the money.” | “Nobody ever does the money, so.”—immediately followed by the figure |
| Antithesis | “It was not a crisis, it was a solution.” | “…so plainly then - it worked. It took the trouble away every time, for about four hours.” |

We also found a perspective error that no style tool would report: chapter 10 said “the reason i stayed with him until the end of my life”. A narrator who is still alive cannot write that.

## What the tool cannot do

The day’s methodological core came from the Christ project: **mechanical checks report; they do not decide.** The `pruefen.py` docstring addresses itself:

> “The tool decides nothing. Every match is a candidate that must be read in context: ‘They danced.’ is a sentence about men dancing; ‘Only one of them is a room.’ is a punchline. The counter cannot tell the difference.”

Each of the 31 remaining matches was individually reviewed and left unchanged, because all belonged to one of four groups:

- **Leven’s own words:** “Shame.” · “Not everyone can do this.” · “Smartie is a retired racehorse.” · “DOLL BY DOLL HAVE MOVED.”
- **Other people’s direct speech:** Bly’s “That is what the death of a father does to a man's soul. Look at it.” · Hillman’s “Let the snake be a snake.”
- **Plain facts:** “He stayed five weeks.” · “He was my little brother.” · “i was in the room.”
- **Jokes in his register:** “i simply have an excellent memory and a website.”

One line of script could have smoothed every one of these away. The result would have been a text with no irregularities and no author—exactly the slop this exercise sought to remove. Measurement prevents AI language only when judgement intervenes.

## What came from the Christ project

Stefan explicitly referred to `~/www/christ`, with the qualification that we should understand how its language had developed rather than imitate it. We adopted three things, none of them a formulation:

1. **The separation of mechanical checking and judgement.** “Report, don’t decide” there; the same instruction in the docstring here.
2. **The catalogue of AI figures.** Eleven figures from a German written style, adapted to an English spoken voice, explicitly dropping those that did not apply. The dash insertion is Leven’s principal hinge, not an error. Staccato exists as a rare exception, not a prohibition.
3. **The documented failed attempt.** In the Christ project, unsuccessful versions sit beside successful ones with explanations. That is why the fifty-word catastrophe and Stefan’s stop instruction are in the language document, not merely a lost conversation.

The tone was *not* adopted. The Christ text is German, written and calm. Leven is English, spoken, fast, coarse and suddenly tender.

## Where this pass left the work

All fifteen chapters were written, checked and revised. Final measurements:

| | Leven | Draft 1 | Draft 2 |
|---|---|---|---|
| Announcements per 1,000 words | 0.16 | 0.47 | **0.07** |
| Antitheses per 1,000 words | 0.22 | 0.67 | **0.14** |
| Paragraph endings under 8 words | 6.3% | 7.2% | **4.4%** |
| Sentences under 5 words | 2.1% | 9.4% | **8.1%** |
| Sentence length: mean / standard deviation | 35.1 / 30.0 | 22.5 / 17.1 | **23.7 / 17.3** |

Two figures remain different, deliberately. Almost all the **short sentences**, on review, are scene headings (“Then Reading.”, “And then Austria.”, “Little Venice.”), quotations or facts; a book needs cuts that a monthly column does not. **Standard deviation** remains at 17 rather than 30 because Leven’s extreme comes from isolated three-hundred-word column sentences. Across a hundred pages, that would produce exactly the mannerism Stefan warned against.

One weakness was identified but left unresolved: **chapters 11, 13 and 14 have the flattest variation, with standard deviations of 14–15.** Each lacks a long, gathering sentence. `00-sprache.md` records that as the next step.

The day’s limits also need recording. One reader judged the text, and he was involved in the project. Whether the chapters reach someone unfamiliar with Leven is unknown. Whether they reach someone who knows and loves him is the real question, also unanswered. The German version did not yet exist. A whole-book pass for recurring images—coal shed, ferry, coalfield—was still outstanding; individual chapters had been checked, the book as a whole had not.

The figures establish only that certain sentence forms became less frequent. They do not establish that the text is good.

---

## Editorial notes for continued work

These notes preserve the working context of the report.

- **Narrative perspective:** “We” refers to shared decisions; “I” refers to Claude Code’s own mistakes. This is deliberate: the errors concerning mean rather than variation, extraction and Stratton Smith were the agent’s, not shared decisions.
- **Conversation quotations:** The original report reproduced Stefan’s wording, including lowercase spelling and typos. This English edition translates the German excerpts; English prose examples remain unchanged. The surrounding account summarises the process.
- **Roles:** Stefan set the goal and detective assignment, insisted on facts before prose, proposed the autobiography, made the three foundational decisions (free pastiche, English with a German version, the whole life), and identified AI language in three passes that the agent had missed. His intervention against overcorrection was the most important single change. Claude Code researched, built extraction, assembled the corpus, wrote the fifteen chapters and two measurement tools, and revised the text. Subagents performed parallel corpus analysis; they could not write files in that environment.
- **Attribution:** Leven’s texts retain their authorship and rights. The corpus in `research/columns/` is the project’s source material. The song lyric ending Leven’s last blog post was omitted from chapter 15; the pastiche is explicitly labelled and is never presented as his own writing.
- **Filename collision:** At the time of this report, `research/` contained two files numbered 09: `09-websites.md` from this work and `09-alan-moffatt-genealogie.md` from a parallel session. Both were valid research files; the numbering still needed attention.

### Project files

- [research/README.md](../research/README.md) — biographical compendium, twelve files plus corpus
- [research/columns/README.md](../research/columns/README.md) — primary source: 76 texts, approximately 90,000 words, with archive links per contribution
- [autobiografie/00-rahmen.md](../autobiografie/00-rahmen.md) — what the book is and is not; labelling requirements
- [autobiografie/00-kapitelplan.md](../autobiografie/00-kapitelplan.md) — fifteen chapters with sources for each
- [autobiografie/00-sprache.md](../autobiografie/00-sprache.md) — language rules: measurements, figure catalogue, documented failed attempt and sentence-by-sentence review log
- [werkzeug/messen.py](../werkzeug/messen.py) — measures chapters against the corpus
- [werkzeug/pruefen.py](../werkzeug/pruefen.py) — reports candidates per chapter without deciding

### Commands

```sh
python3 werkzeug/messen.py              # Overall Leven / pastiche comparison
python3 werkzeug/messen.py autobiografie/07-electric-fur.md
python3 werkzeug/pruefen.py             # All chapters
python3 werkzeug/pruefen.py 07 08       # Selected chapters, with leading zero
```

### Related working material

- `~/www/testhost/christ` — source of the method: separation of mechanical checking and judgement, catalogue of AI language figures, documented failed attempts
