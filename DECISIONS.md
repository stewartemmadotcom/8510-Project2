# Decisions



# Notes 

## 2026-10-21_gemini-flash-lite-3.5 run 
- Recitation error on issue July 88, page 23 
- Books and albums sections from multiple editions show up; I did not want Gemini to include these; need to be more specific next run 

## 2026-10-22_codebook-v1_flash-lite-3.5 run (test against Project 1)
- First run with `codebook.md` and the Project 1 columns. 18 directory pages
  from the 5 hand-checked issues; no failures, no RECITATION; cost $0.18.
- Compared with `02_compare_to_handchecked.py`: 103 hand-checked rows in
  scope, 97 matched, 6 missed, 10 extra.
- Reliable: page 100%, row_kind 99%, contact city/state/zip 98-99%,
  acreage 96%, contact street 94%, raw_text 94% (mean similarity 0.99).
- Weak: focuses 43%, accepted_groups 65%, land_street_address 68%,
  land_city 70%, land_location_as_stated 70%, type 73%, num_residents 73%,
  land_zip 72%.
- Patterns seen:
  - type: the model over-uses Intentional Community/Cooperative; misses
    retreats by function (Who Farm, Penthesileia) and one-or-two-women land
    (Misty Bottoms, Dutch Mountain).
  - land_*: the model leaves out RD/Rt/RFD boxes that I recorded as the
    land, and fills land_city from the mailing city where I left it blank.
  - land_location_as_stated: mostly the same place in slightly different
    words; exact-match scoring is too strict for this field.
  - accepted_groups: the model adds Non-lesbian women and Boy children more
    often than I did.
  - focuses: the model codes too few.
  - contact_name: the model leaves out the person when the community is
    named after them (Susan Stone, Jan F Walsh).
  - Extra rows: groups LC says have no land (Dec 1982: Ellie's Nest, River
    Most Wild, Aradia, Women's Wilderness Experience, Lesbians on Land;
    Mar 1983: Gabriel's, Sea Gnomes Home) were extracted anyway.
  - Missed rows: folded notices (A Woman's Place, Heraseed), the joint
    listing split (California Women's Land Trust), Feathers Farm's letter,
    Bee Song Honey Farms; Women Only Ranch (Mar 1986 p. 19) was not in the
    test pages.
- raw_text: only 6 of 97 matched listings were below 0.98 similarity.
  - Serious (2):
    - Cedar (Mar 1983 p. 18, 0.61): correct, but the end of Bee Song Honey
      Farms was attached. The model skipped the start of Bee Song at the
      bottom of p. 18, so the continuation on p. 19 merged into Cedar, the
      last listing on p. 18. One skipped listing made two errors (Bee Song
      missed, Cedar wrong).
    - Herland (Mar 1986 p. 8, 0.80): stopped mid-sentence ("Unemployment in
      this area"), losing the rest including the We welcome / We have/are
      lists. Also "I am interested" became "I have interested". Not split
      across pages; the model just stopped early.
  - Editor's notes copied in (2): Folly Farm (0.89) and Wilderness Way
    (0.91) start with the editor's note printed above them ("NOTE: The
    following is not a women's land group..."; "NOTE: These groups don't have
    land, per se..."). The listing text itself is right.
  - Small slips (2): Fly Away Home (0.978) and Greenhope (0.979): dropped
    words ("on", "we", "and working"), "every" became "everything", an em
    dash became an en dash, a missing space ("tipi.We").
  - Question for me: Wilderness Way is under LC's "don't have land, per se"
    note, but I included it in Project 1. Is there an exception to my
    no-land rule that the codebook should say?
- Changes to consider for the next run:
  - codebook: section headings and editor's notes are not part of a
    listing's raw_text.
  - a check that flags raw_text ending mid-sentence (would have caught
    Herland).
  - a check for a merged row whose added text reads like a different
    community (would have caught Cedar).
  - raw_text from the model still needs proofreading where exact wording
    matters.

## 2026-10-22_codebook-v2_flash-lite-3.5 run (codebook made more specific)
- Same 18 pages and model as v1; cost $0.21; no failures.
- Codebook changes, each based on patterns in my Project 1 notes:
  - land_*: written out my actual practice. A rural route (RD/Rt/RFD/HCR)
    or street address is the land (copy all four parts) unless the people
    live elsewhere; a PO box never is. In Project 1, 34 of 37 rural-route
    addresses and 20 of 35 street addresses were coded as the land.
  - land_location_as_stated: copy the place phrase exactly, nothing else.
  - contact_name: fill the person's name even when the community is named
    after her.
  - type: the "two-woman rule" spelled out (apprentices and visitors don't
    make it a community; only recruiting members to live there does).
  - num_residents: one number only; 0 when owners live elsewhere; a
    questionnaire count counts only with "women living on the land".
  - accepted_groups: in questionnaire directories (1982 on), Non-lesbian
    women only when named; "women" means lesbians.
  - focuses: any rule against drugs/alcohol is Recovery/substance-free (my
    most-missed focus); organic gardening as farming is Farming only.
  - rows: ended-community sentences inside intros are their own rows;
    no-land groups skipped; joint listings split (with the 1976 example).
  - raw_text: copy to the end; leave out editor's notes and headings.
- Code changes: merging no longer joins numbers as text ("2" + "2" had
  become "2 2"); new CHECK messages for a fragment joined onto a listing that
  already looked complete (caught Cedar) and for raw_text ending
  mid-sentence (caught Herland).
- Results (v1 -> v2): differences per listing 3.12 -> 2.81.
  - Clearly better: land_street_address 68 -> 84%, land_zip 72 -> 85%,
    land_city 70 -> 79%, acreage 96 -> 98%, contact_zip 99 -> 100%.
  - No real change: focuses 43 -> 44%, accepted_groups 65 -> 67%,
    raw_text 94 -> 94%, land_location_as_stated 70 -> 70%.
  - Worse: type 73 -> 70% (now over-corrects: 10 communities called
    Private/Individual Land), num_residents 73 -> 67%, contact_name
    88 -> 86%.
  - Missed rows 6 -> 5 (California Women's Land Trust now split correctly).
    Extra rows 10 -> 13: the no-land groups were still extracted, plus 3 new
    ones (Lesbian Self-Sufficiency Weekends, Vacation, Healing Intensives).
- The judgment fields churn between runs: for type, 11 listings were fixed
  but 14 others became wrong; for focuses, 10 fixed and 10 newly wrong. So
  part of the error is the model being inconsistent, not the codebook. A few
  points of change on 98 listings can be run-to-run noise.
- Caution: some new codebook examples come from these same test listings
  (e.g. Hardscrabble Hill, Days Creek, "NO DRUGS!"), so scores on this test
  set may look better than they would on issues not hand-checked yet.
- Next to try: the same codebook with a stronger model, to see whether
  the judgment fields are limited by flash-lite rather than the codebook.


# Plan (draft, not decided yet): extracting LC and Maize into the Project 1 database

Goal: use an LLM through an API to fill the relational database from Project 1
(`8510-Project1/schema.sql`) from Lesbian Connection and Maize, instead of
entering every row by hand.

## Main idea: the LLM does not build the database directly

The database has 8 linked tables with IDs, and many coding rules are judgment
calls. An LLM is good at reading one page and filling in fields, but bad at
keeping IDs consistent across hundreds of pages. So the work is split into
stages, and each stage is done by whoever (model, code, or me) does it best.

### Stage 1: the model extracts one flat row per listing or mention
Fields match `community_observations`:
- `contact_*` and `land_*` address fields, `land_location_as_stated`
- `acreage`, `num_residents`, `description`, `raw_text`, `page`
- the community name as printed
- accepted groups, focuses, and type, picked only from my controlled
  vocabularies (the schema can force this, so the model can't invent new
  categories)
- `notes`: the model explains every judgment call, the same rule I follow
  when coding by hand

### Stage 2: code applies the rules that need no judgment
Some codebook rules are fixed and code can apply them the same way every time:
- Lesbian women is coded for every listing that welcomes anyone
- "children" with no gender = Girl children + Boy children
- the 1986 change in LC's default for non-lesbian women (by issue date)

Rules that need interpretation (type, who counts as a resident, acreage that
isn't the group's own) stay with the model, with the codebook in the prompt.

### Stage 3: matching communities (needs me)
Deciding which listings are the same community (Owl Farm = Oregon Women's
Land Trust; Rowdybush Farm -> Laughing Rock Farm) takes knowledge across
issues that the model can't see one page at a time.
- Code suggests matches by name, starting from the communities already in
  Project 1.
- I approve or fix a matching list, and that list becomes `community_id`.

### Stage 4: code builds the tables
Code assigns `source_id` (from filenames), `observation_id`, and fills the two
junction tables. Then the existing `schema.sql` and `build_db.py` load it.

## Testing: compare against Project 1 first

Project 1 has 107 observations checked cell by cell against the page, from the
same LC issues. Run the pipeline on those issues and compare its rows with
mine, field by field. This shows:
- how accurate the model is for each field (e.g. addresses vs. `num_residents`)
- where to fix the prompt, and which fields I still need to check by hand
- evidence for the method write-up

## Maize is different from LC

LC's land directories are lists of listings. Maize is a magazine: communities
appear inside articles, letters, and ads, and most pages mention none.
- Two passes: a cheap first pass asks only whether a page mentions a land
  community and which ones; a second pass extracts full observations from
  those pages.
- My scope rules were written for LC directories ("Not a listing" rows,
  classified ads). Before automating Maize, code a couple of issues by hand
  and decide what counts as an observation in an article or letter, then add
  those rules to the codebook.
- `maize2` has OCR text for some issues. Page images are usually more
  accurate (and the codebook says to transcribe from the image), but the text
  could be used for the cheap first pass.

## Order
1. LC first: change the 01 script's fields to match `community_observations`.
2. Compare with the Project 1 rows and fix the prompt until accuracy is good
   enough.
3. Write the community matching step.
4. Hand-code a few Maize issues, extend the codebook, then add Maize.

## Open questions
- `raw_text` asks for whole listings word for word. The RECITATION error on
  July 88 p. 23 suggests Gemini may sometimes refuse long verbatim copying.
  Options: retry that page, try another model, or keep `raw_text` out of the
  model's job (e.g. take it from OCR text and check it by hand).
- How accurate is "good enough" for each field before I trust it without
  checking every row?
- Should model-made rows be marked in the database (e.g. a column saying
  "hand-checked" or "model, unchecked") so queries can tell them apart?
