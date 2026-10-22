# Decisions



# Notes 
- Recitation error on run: 2026-10-21_gemini-flash-lite-3.5 on issue July 88, page 23 


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
