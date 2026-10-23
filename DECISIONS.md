# Decisions

## 2026-10-22: three codebook questions settled (codebook v3)
- **Places under LC's "don't have land, per se" note:** a place on its own
  land is a row, even when it is a business or LC says it has no land
  (Wilderness Way, a women's campground on its own 10 acres; Pagoda, a
  residential community on its own property). Groups and businesses with
  no land of their own are not rows (Ellie's Nest, Gabriel's apartments in
  Provincetown). This is what I did in Project 1; v2's "skip businesses"
  wording had made 3.8 Flash drop Wilderness Way.
- **land_location_as_stated holds place and setting:** where the land is,
  plus the listing's own words for its setting ("the Elwha River running
  through the back meadow", "beautiful desert country with big skies",
  "ocean"), and the town given for an ended community ("Athol, NY"). This is
  what I did in Project 1; v2 had said "only the place phrase".
- **Non-lesbian women before 1986:** "women"/"wimmin"/"womyn" in a statement
  of who is welcome means Lesbian + Non-lesbian women ("women and children",
  "all women of all colours and persuasions"). "Women" that only describes
  who lives there, and words naming lesbians ("lesbian-feminists"), do not
  add Non-lesbian women. From 1986 on, only when named. This is my
  Project 1 rule; v2 had wrongly read "women" as lesbians from 1982 on.
- No changes needed to the Project 1 data for any of these.


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

## 2026-10-22_codebook-v2_flash-3.8 run (same codebook, stronger model)
- Codebook v2 unchanged; model changed from gemini-3.5-flash-lite to
  gemini-3.8-flash ($0.75 in / $3.75 out per 1M tokens until Dec 31, 2026,
  then double). Same 18 pages; no failures.
- Cost $1.05 (vs $0.21), about 5 times more, mostly because 3.8 Flash
  "thinks" a lot (6,000-27,000 output tokens per page). Much slower: about
  1-3 minutes per page, about 25 minutes in all.
- Results (v2 flash-lite -> v2 3.8 Flash): differences per listing
  2.81 -> 1.32; 29 of 100 listings match me exactly in every field.
  - type 70 -> 84%, num_residents 67 -> 92%, accepted_groups 67 -> 89%,
    focuses 44 -> 73%, contact_name 86 -> 97%, raw_text 94 -> 98%
    (mean 0.993), land_street 84 -> 91%, land_city 79 -> 93%,
    land_zip 85 -> 95%, acreage 98 -> 100%, contact_city 100%.
  - land_location_as_stated 70 -> 71%: still low, but mostly the same place
    with a word more or less ("in the rolling Berkshire mountains..." vs "the
    rolling Berkshire mountains..."). My own Project 1 practice varies here
    too; the rule or the scoring needs to be looser.
  - Missed rows 5 -> 3, extra rows 13 -> 2. Bee Song Honey Farms is found
    now and the p. 19 fragment joins onto it correctly. No-land groups are
    skipped except Aradia Inc Marie Curie Task Force; Half Moon Pines is
    still extra. Wilderness Way is now missed, because the model followed
    the no-land rule: my open question about an exception still matters.
    Women Only Ranch (Mar 1986 p. 19) is still not in the test pages.
- What is left:
  - type (16 wrong): mixed; e.g. Oregon Women's Land Trust (Land Trust)
    called a community; Feathers Farm and Laughing Rock Farm called
    retreats.
  - accepted_groups: now leaves out Non-lesbian women in some 1983 listings
    where I coded them (Feathers Farm, Who Farm, Heathcote, Moon Ridge).
    Check whether those listings name non-lesbian women or whether I applied
    the pre-1986 "women" rule there.
  - focuses 73%: the hardest field; disagreements are one focus more or less.
- Conclusion: the codebook was not the main limit; flash-lite was. The
  stronger model, with the more specific codebook, gets close to my hand
  coding on most fields.
- Cost for the whole corpus: at about $0.06 per page, the 33 LC directory
  pages would be about $2; Maize would be more, since it has many more pages.
- Same caution as v2: some codebook examples come from these test listings.
  Test next on a hand-checked issue that was not used to write the codebook.

## Scoring change: land_location_as_stated
- Exact matching was too strict for this field: most disagreements were the
  same place with a word more or less ("in the Adirondacks" vs "the
  Adirondacks", a final period).
- New rule in `02_compare_to_handchecked.py`: ignore case and punctuation,
  drop leading "located / in / the / a / an / on / at", then the two match if
  they are the same or one contains the other. A blank never matches a
  filled-in value. The self-test still passes at 100%.
- All three runs re-scored with the new rule (other fields unchanged):
  v1 flash-lite 70 -> 89%, v2 flash-lite 70 -> 89%, v2 3.8 Flash 71 -> 91%.
- What is still different in the 3.8 Flash run (9) is real:
  - 7 where the model left it blank and I didn't. Several of mine are
    scenery rather than a place ("beautiful desert country with big skies",
    "on an old blue stone quarry", "ocean"), and two are towns from
    not-a-listing rows ("Athol, NY", "Talmage, CA"). Question for me: should
    this field hold descriptions of the land, or only where it is?
  - 2 where we picked different phrases from the same listing (Whispering
    Winds, Another Demention).
  - Answered 2026-10-22: place and setting (see Decisions).

## 2026-10-22_codebook-v3_argon-4 run (codebook v3, Gemini 4 Argon)
- Codebook v3 (the three decisions above) and model gemini-4-argon ($2 in /
  $10 out per 1M tokens until Nov 30, 2026, then double). The 18 test pages
  plus July 1988 p. 23 (not scored). No failures.
- Cost $1.11, about the same as 3.8 Flash ($1.05): Argon wrote fewer
  thinking tokens per page, which made up for the higher price. After
  Nov 30 the same run would cost about $2.20.
- July 1988 p. 23 extracted fine: no RECITATION refusal this time.
- Results (v2 3.8 Flash -> v3 Argon): differences per listing 1.32 -> 1.26;
  30 of 102 listings match me exactly.
  - Better: type 84 -> 89%, num_residents 92 -> 95%, accepted_groups
    89 -> 94% (partly the corrected pre-1986 rule), row_kind 99 -> 100%,
    contact_street 96 -> 98%. Missed rows 3 -> 1 (Wilderness Way and
    Feathers Farm's letter are found now; Women Only Ranch is still not in
    the test pages).
  - Worse: focuses 73 -> 66%, land_location_as_stated 91 -> 77%,
    land_state 92 -> 89%, contact_name 97 -> 94%. Extra rows 2 -> 5 (Sea
    Gnomes Home twice, Half Moon Pines, Pepperland, Aradia).
- Why the two big drops:
  - land_location_as_stated: v3 asks for the setting too, so Argon now
    fills setting phrases in listings where I left the field blank
    ("gorgeous secluded land; maple sugar bush", "forested property"). My
    own Project 1 coding recorded setting for some listings but not
    others, so this field is partly a judgment call no model can match.
  - focuses: Argon codes more than I did (added Farming 10 times,
    Spirituality 8, Archives 6, Recovery 6; left out only 10 in all).
- Both changes happened at once (codebook v2 -> v3 and 3.8 Flash -> Argon),
  so I can't tell how much each one did. A 3.8 Flash run on v3 (about $1)
  would separate them.
- Overall: Argon and 3.8 Flash are about equally good; Argon is better on
  type, residents and groups, 3.8 Flash on focuses. What disagrees now is
  mostly where my own coding is a judgment call (focuses, setting).
- Small fixes noticed: July 1988 is not in `reference/sources.csv`; land_state
  sometimes written out ("Arkansas" for AR).

## 2026-10-22_codebook-v3_flash-3.8 run (codebook v3, 3.8 Flash)
- Same codebook and pages as the Argon run; only the model differs. Cost
  $0.96. July 1988 p. 23 was refused again (RECITATION), though Argon
  extracted it: the refusal depends on the model.
- All runs side by side (accuracy %, land_location scored loosely):

  | field | v1 lite | v2 lite | v2 3.8F | v3 3.8F | v3 Argon |
  |---|---|---|---|---|---|
  | type | 73 | 70 | 84 | **92** | 89 |
  | num_residents | 73 | 67 | 92 | 92 | **95** |
  | accepted_groups | 65 | 67 | 89 | **98** | 94 |
  | focuses | 43 | 44 | 73 | **75** | 66 |
  | land_location_as_stated | 89 | 89 | **91** | 62 | 77 |
  | land street/city/zip | 68/70/72 | 84/79/85 | 91/93/95 | 92/90/96 | 92/93/93 |
  | contact_name | 88 | 86 | **97** | 96 | 94 |
  | raw_text | 94 | 94 | 98 | 97 | 97 |
  | differences per listing | 2.94 | 2.62 | **1.12** | 1.25 | 1.26 |
  | missed / extra rows | 6/10 | 5/13 | 3/2 | 1/4 | 1/5 |

- Model effect (v3 3.8 Flash vs v3 Argon, same codebook): about equal
  overall (1.25 vs 1.26). 3.8 Flash is better on type, groups and focuses;
  Argon on residents and land_location, and it did not refuse July 1988.
  Argon is not worth paying more for on this task.
- Codebook effect (v2 -> v3, both 3.8 Flash):
  - The pre-1986 "women" fix worked: accepted_groups 89 -> 98%.
  - type 84 -> 92%, missed rows 3 -> 1 (Wilderness Way found).
  - The setting rule backfired: land_location_as_stated 91 -> 62%. In 24
    listings the model filled it where I left it blank, mostly by copying
    items from the "We have/are:" list ("woods", "farm land", "creek,
    woods, open"). The v3 example "a setting word from the We have/are:
    list such as 'ocean'" (from Pagoda) caused this. It is the only reason
    differences per listing went up (1.12 -> 1.25).
- To fix in v4: take out the "We have/are:" example; setting only from a
  sentence that describes where or in what setting the land is, never from
  questionnaire items.

## 2026-10-23_codebook-v4_flash-3.8 run (setting rule fixed)
- Codebook v4: setting in land_location_as_stated only from a sentence that
  describes where the land is or its landscape; never "We have/are:" items,
  general praise, or lists of what the land has. 3.8 Flash, same 19 pages.
- Dec 1982 p. 23 was refused (RECITATION) in the first pass and extracted on
  a retry; July 1988 p. 23 was refused both times (3.8 Flash has now refused
  it in every run; Argon extracted it). Cost $1.03 + $0.07 retry.
- Best run so far: 1.09 differences per listing (v2 3.8F 1.12, v3 3.8F
  1.25, v3 Argon 1.26).
  - land_location_as_stated 62 -> 83%: the fix worked.
  - focuses 75 -> 78% (best yet); accepted_groups 98 -> 94%; type 92 -> 90%;
    other fields about the same. Changes of 1-4 points are within
    run-to-run noise.
  - Missed 1 (Women Only Ranch, not in test pages), extra 4 (Aradia,
    Pepperland, Sea Gnomes' Home, Half Moon Pines).
- What is left in land_location_as_stated (17): now mostly the model leaving
  it blank where I filled in a distance from a city ("35 miles north of
  Baltimore", "approx 30 miles SE of Portland", "15 miles from town with
  jobs"). The codebook says to leave out "distances to other cities", but
  my Project 1 coding keeps them when they locate the land. Fix for v5:
  keep a distance or direction from a named place when it says where the
  land is.
- Why type and accepted_groups were higher in v3 3.8 Flash than v4: the
  codebook did not change for those fields, so most of it is run-to-run
  variation on borderline listings (type: 2 listings; groups: 4). But 3 of
  the 4 group errors show a gap in the rule (all Dec 1982, and Argon made
  the same mistake): the model added Non-lesbian women from "women"
  outside the "We welcome:" list - The Web ("open to wimmin"), North Crow
  ("Some weeks are for womyn only"), Rebecca, Susan, Anne & Maurine's land
  ("visiting women"). My actual practice: when a listing has a "We welcome:"
  list, only that list counts; in a free-text listing with no form (Feathers
  Farm, "women and children"), a welcome to "women" means both groups.

## 2026-10-23_codebook-v4_sonnet-5.5 run (first Claude run)
- Codebook v4 (same as the v4 3.8 Flash run), model claude-sonnet-5-5
  ($2 in / $10 out per 1M tokens), effort high. Same 19 pages.
- Cost $1.41; about 10 minutes (20-60 seconds per page, vs 1-3 minutes
  for 3.8 Flash). No refusals: July 1988 p. 23, which 3.8 Flash refused in
  every run, came through.
- Results (v4 3.8 Flash -> v4 Sonnet 5.5): differences per listing
  1.09 -> 1.38.
  - Better: land_location_as_stated 83 -> 94% (best yet), contact_name
    95 -> 97%, land street/city 90 -> 92%.
  - Same: page, acreage, row_kind, contact address, raw_text (96%).
  - Worse: focuses 78 -> 52%, type 90 -> 82%, num_residents 93 -> 87%,
    accepted_groups 94 -> 89%. Extra rows 4 -> 6 (Women's Wilderness
    Experience and Sea Gnomes Home, March 1983, added).
- Patterns:
  - type: 9 of my Intentional Communities called Private/Individual Land;
    Sonnet applies the two-woman rule too widely.
  - focuses: left out Environmentalism 11 times and Archives 5, while
    adding Farming 9, Recovery 7, Spirituality 5. Disagreements both ways.
  - accepted_groups: left out men ("males") in 3 listings.
- Sonnet writes far less thinking than Gemini 3.8 Flash (about 2,000-7,000
  output tokens per page vs 6,000-27,000). The facts printed on the page
  are as good; the judgment fields (type, focuses, residents) are worse.
- Next: Opus 5.5 on the same codebook, as planned; Sonnet at a higher
  effort (xhigh) is another option.

## 2026-10-23_codebook-v4_opus-5.5 run
- Codebook v4, model claude-opus-5-5 ($4 in / $20 out per 1M tokens),
  effort high, same 19 pages. Cost $4.16 (incl. a $0.18 one-page test);
  about 20 minutes. No refusals.
- All three v4 runs (same codebook, same pages):

  | field | 3.8 Flash | Sonnet 5.5 | Opus 5.5 |
  |---|---|---|---|
  | type | **90** | 82 | 86 |
  | num_residents | **93** | 87 | **93** |
  | accepted_groups | **94** | 89 | 92 |
  | focuses | **78** | 52 | 67 |
  | land_location_as_stated | 83 | **94** | 86 |
  | land city | 90 | 92 | **96** |
  | raw_text | 96 | 96 | **97** |
  | differences per listing | **1.09** | 1.38 | 1.20 |
  | listings matching me exactly | 34 | 29 | 34 |
  | cost | **$1.10** | $1.41 | $4.16 |
  | refusals | 2 pages | none | none |

- Opus is between the other two on the judgment fields, at about 4 times
  the cost of 3.8 Flash. 3.8 Flash is still the best and cheapest; its
  weak point is refusing some pages (RECITATION), which neither Claude
  model did.
- Patterns in Opus:
  - focuses: left out Environmentalism 15 times (Sonnet 11), added
    Recovery 8. Both Claude models code Environmentalism much less often
    than I did, so the codebook's Environmentalism rule (written in v2 to
    stop over-coding) may now be stricter than my own practice. Check my
    Project 1 notes for what I counted.
  - type: 6 Intentional Communities called Private/Individual Land (same
    two-woman-rule pattern as Sonnet, less often).
  - accepted_groups: added Non-lesbian women 5 times.

## To change later (codebook v5) - not done yet
Decided 2026-10-23 to wait until Claude has been tried on codebook v4, so
the Claude runs compare fairly with the v4 3.8 Flash run.
- land_location_as_stated: keep a distance or direction from a named place
  when it says where the land is ("35 miles north of Baltimore", "approx 30
  miles SE of Portland"); take out "leave out distances to other cities".
- accepted_groups: when a listing has a "We welcome:" list, only that list
  decides who is welcome; "women"/"wimmin" elsewhere in the text ("open to
  wimmin", "womyn only" weeks, "visiting women") does not add Non-lesbian
  women. In a free-text listing with no "We welcome:" list, the pre-1986
  rule applies as now.
- To check first: the Environmentalism/eco-friendly focus rule. Both Claude
  models left it out where I coded it (Opus 15 times, Sonnet 11). Look at
  what I counted in Project 1 before loosening the rule.


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


# Summary: all scored runs (as of 2026-10-23)

Every run below used the same 18 LC directory pages from the 5 issues I
hand-checked in Project 1, and was scored against those 103 rows by
`02_compare_to_handchecked.py` (land_location_as_stated scored by place
phrase). Codebook v1 -> v4 are the versions of `codebook.md`; see each run's
notes above for what changed. Lower "differences per listing" is better: it
counts fields that disagree with my hand coding, averaged over matched
listings.

## Differences per listing (lower is better)

```
                codebook + model                       differences per listing
v1 flash-lite   ███████████████████████████████████  2.94
v2 flash-lite   ███████████████████████████████      2.62
v2 3.8 Flash    █████████████                        1.12
v3 3.8 Flash    ███████████████                      1.25
v3 4 Argon      ███████████████                      1.26
v4 3.8 Flash    █████████████                        1.09   <- best
v4 Sonnet 5.5   █████████████████                    1.38
v4 Opus 5.5     ██████████████                       1.20
```

## Cost for the 18-19 test pages

```
v1 flash-lite   █                                  $0.18
v2 flash-lite   ██                                 $0.21
v2 3.8 Flash    ████████                           $1.05
v3 3.8 Flash    ████████                           $0.96
v3 4 Argon      █████████                          $1.11
v4 3.8 Flash    █████████                          $1.10
v4 Sonnet 5.5   ███████████                        $1.41
v4 Opus 5.5     █████████████████████████████████  $4.16
```

## Full comparison

Accuracy (% of matched listings that agree with me) for the fields that
vary most; page, acreage, row_kind and the contact address were 94-100% in
every run with a strong model.

| codebook | model | type | residents | groups | focuses | land location | land street | contact name | raw_text | diffs / listing | exact listings | missed / extra rows | cost | refused pages |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | Gemini 3.5 Flash-Lite | 73 | 73 | 65 | 43 | 89 | 68 | 88 | 94 | 2.94 | 8 of 97 | 6 / 10 | $0.18 | 0 |
| v2 | Gemini 3.5 Flash-Lite | 70 | 67 | 67 | 44 | 89 | 84 | 86 | 94 | 2.62 | 6 of 98 | 5 / 13 | $0.21 | 0 |
| v2 | Gemini 3.8 Flash | 84 | 92 | 89 | 73 | **91** | 91 | 97 | **98** | 1.12 | **35** of 100 | 3 / **2** | $1.05 | 0 |
| v3 | Gemini 3.8 Flash | **92** | 92 | **98** | 74 | 62 | 92 | 96 | 97 | 1.25 | 32 of 102 | 1 / 4 | $0.96 | 1* |
| v3 | Gemini 4 Argon | 89 | **95** | 94 | 66 | 76 | 92 | 94 | 97 | 1.26 | 30 of 102 | 1 / 5 | $1.11 | 0 |
| v4 | Gemini 3.8 Flash | 90 | 93 | 94 | **78** | 83 | 90 | 95 | 96 | **1.09** | 34 of 102 | 1 / 4 | $1.10 | 2 (1 retried)* |
| v4 | Claude Sonnet 5.5 | 82 | 87 | 89 | 52 | **94** | 92 | **97** | 96 | 1.38 | 29 of 102 | 1 / 6 | $1.41 | 0 |
| v4 | Claude Opus 5.5 | 86 | 93 | 92 | 67 | 86 | 92 | 95 | 97 | 1.20 | 34 of 102 | 1 / 6 | $4.16 | 0 |

\* Refusals were RECITATION: Gemini declining to copy published text. July
1988 p. 23 (not scored) was refused by 3.8 Flash every time; Dec 1982 p. 23
was refused once and worked on a retry. Neither Claude model, nor Argon,
refused any page. The v1 and v2 flash-lite runs ran 18 pages; v3 and v4
added July 1988 p. 23 (19 pages, not scored).

## What the runs show

- **The model mattered most at first.** Moving from Flash-Lite to 3.8 Flash
  cut differences per listing from 2.6 to 1.1, more than any codebook
  change.
- **The codebook mattered for specific fields.** Writing out my land
  address rule (v2) fixed the land fields; settling the pre-1986 "women"
  rule (v3) raised accepted groups to 94-98%; the setting rule in v3
  backfired on land location until v4 fixed it.
- **Among strong models the differences are small.** 3.8 Flash, Argon and
  Opus are all at 1.1-1.3 differences per listing; run-to-run variation on
  the same model and codebook is a few listings per field.
- **Best value: Gemini 3.8 Flash with codebook v4** - lowest differences
  (1.09), best focuses (78%), about $0.06 per page. Its weak point is
  refusing some pages; Claude (Sonnet, about $0.07 per page, or Opus) can
  pick up refused pages.
- **The hardest fields are judgment calls**: focuses (52-78%), type
  (82-92%), land location (62-94%). Several remaining disagreements trace
  back to places where my own Project 1 coding is not fully consistent, or
  where the codebook doesn't yet say what I actually did (see "To change
  later (codebook v5)").
- **Facts printed on the page are reliable with any strong model**: page,
  acreage, contact address 94-100%; raw_text 96-98%.
- **Caution:** some codebook examples come from these same test listings,
  so these scores may be higher than on issues not yet hand-checked.


# Maize extraction (started 2026-10-23)

## Plan and decisions
- Maize was transcribed in the Maize-OCR project (Claude Haiku 5.5, 1,209
  pages, $1.25). Extraction reads those texts and uses Gemini 3.8 Flash,
  the best model on LC.
- Scope: only Country Connections listings and community reports (On the
  Land, Land Lesy, articles by or about one land community) become rows.
  Passing mentions in other articles, letters and announcements are left
  out.
- One whole issue per request (largest, #53, is about 51,000 tokens with
  the prompt), so reports that run across pages stay together.
- Test set: I hand-code #25 (Summer 1990) and #53 (Spring 1997) in
  `reference/maize_handcoded/maize_handcoded.csv` before seeing any model
  output for them.
- Maize rules go in `codebook_maize.md`, read after `codebook.md`. It is a
  draft with TO DECIDE notes (accepted groups, splitting joint reports,
  letters, type); `03_maize_to_csv.py` won't send anything until they are
  replaced by decisions.

## Code
- `extraction_common.py`: the parts shared by the LC and Maize scripts
  (codebook columns, vocabularies, Gemini and Claude calls, costs, checks,
  run folders). `01_directory_to_csv.py` now uses it; checked that its
  settings, schema and output are identical to before.
- `03_maize_to_csv.py`: one issue at a time, same run folders and checks as
  LC; row_kind can be listing, report or not_a_listing.
- `reference/sources.csv`: the 29 Maize issues added (source_id 6-34).
- `02_compare_to_handchecked.py`: `HAND_CSV` setting to score against the
  hand-coded Maize CSV; with it, every model row from a hand-coded issue is
  scored, on any page.
