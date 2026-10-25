# Hand-coding the Maize test issues

Hand-code issues **#25 (Summer 1990)** and **#53 (Spring 1997)** before running
any model on them, so the test is fair. Copy `maize_handcoded_template.csv` to
`maize_handcoded.csv` in this folder and add one row per observation, following
`codebook.md` and `codebook_maize.md`. Record every rule you decide along the
way in `codebook_maize.md` (replacing its TO DECIDE notes) and in
`DECISIONS.md`.

The transcriptions are in
`~/Desktop/Maize-OCR/output/runs/2026-10-23_all_haiku-5.5/text/maize-25-summer1990/`
and `.../maize-53-spring1997/`, one file per page; the page images are in
`~/Desktop/Maize-OCR/images/`. Check names, numbers and addresses against the
images: the transcription can misread them (e.g. "Pelican Leo" for Pelican Lee).

## Columns

| column | what goes in it |
|---|---|
| issue | `maize-25-summer1990` or `maize-53-spring1997` |
| page | printed page number where the item begins (a number only) |
| row_kind | `listing` (Country Connections), `report` (On the Land), `announcement` (a land announcement), or `not_a_listing` |
| section | Country Connections, On the Land, or Announcements |
| community_name ... land_location_as_stated | as in `codebook.md` |
| acreage, num_residents | a number, or blank |
| type | one of the type names below, or blank |
| accepted_groups, focuses | names from the lists below, separated by `; ` |
| description, raw_text, notes | as in `codebook.md` |

Spreadsheet tip: keep the file as CSV (UTF-8) when saving; long raw_text with
commas and line breaks is fine as long as the program quotes it.

## Allowed values

**type:** Land Trust / Intentional Community/Cooperative / Private/Individual Land /
Retreat/Gathering Space / Land Fund/Seeking Land

**accepted_groups:** Lesbian women / Non-lesbian women / Girl children /
Boy children / Gay men / Non-gay men

**focuses:** Disabled women / Older women / Recovery/substance-free /
Working-class women / Lesbian separatism / Spirituality/ritual /
Farming/self-sufficiency / Workshops/education / Archives/cultural work /
Environmentalism/eco-friendly / Women of color

## How it's scored

`02_compare_to_handchecked.py` with `HAND_CSV` set to this folder's
`maize_handcoded.csv` pairs your rows with the model's by issue and name and
scores each field, the same way as for LC. description and notes aren't
scored; they go into the side-by-side review file.
