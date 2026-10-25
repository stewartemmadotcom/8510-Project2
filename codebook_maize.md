# Codebook addendum: Maize

This file is read into the Maize extraction prompt by `03_maize_to_csv.py`,
after `codebook.md`. Where the two disagree, this file wins for Maize.
`codebook.md` was written for Lesbian Connection's land directories; its
rules for raw_text, addresses, type, acreage, num_residents and focuses apply
to Maize as written unless this file says otherwise.

Rules marked "Decided" were settled while hand-coding issues 25 and 53. Two
questions are still open (marked OPEN QUESTION): code those cases as best
you can and flag them in notes, so the rules can be decided from real cases.

## The source
Maize: A Lesbian Country Magazine (1990-1998), quarterly. Each request gives
one whole issue as transcribed text, page by page. Each page starts with a
marker line like `=== image page-014 ===`; the printed page number, when the
page has one, is at the end of the page as `[Page number: N]`. Headings are
lines starting with `## `. The text was transcribed by machine and can have
small errors, especially in names.

## What counts as a row
Only items in three sections of the magazine become rows. Use the issue's
contents page to see which items each section holds: the items listed under
ON THE LAND (indented below it) are that section's entries, even when each
has its own heading.

- **listing** (`row_kind` = listing): one entry in the Country Connections
  directory (from 1992 on): a land's name, address, and usually a few lines
  about it.
- **report** (`row_kind` = report): one entry in the On the Land section,
  usually under its own `## ` heading with the land's name (e.g.
  `## DOE FARM`, `## OWL FARM`).
- **announcement** (`row_kind` = announcement): one notice in the
  Announcements section that is by or about a specific land community: e.g.
  a land seeking members or residents, land for sale or to share, a land's
  open house or work weekend. Announcements about anything else are not
  rows: gatherings and festivals not tied to one land, publications,
  businesses, workshops elsewhere, personal notices.
  Also not rows (decided 2026-10-24, #53): a notice selling a share in a
  piece of land with no community name (e.g. "FOR SALE: Half-interest in
  country, secluded 5.5 acres..."), and a notice about a land community's
  web page or publication rather than its land (e.g. "WE'MOON is now
  on-line").
- **not_a_listing**: an entry in any of these sections saying a land
  community has ended (sold, folded, dissolved), as in `codebook.md`.

Nothing else in the issue is a row, even when it is about a land community:
not articles, gathering reports, Land Lesy, Letters, poems, reviews, or
how-to pieces. (Decided 2026-10-23: these are much more interpretive;
Country Connections, On the Land and land announcements are the
directory-like parts of Maize.)

An On the Land entry that is only photos with captions is still a row:
name it from the captions, take the place from them if given, put the
heading and captions in raw_text, and leave the rest blank (e.g. SuBAMUH,
#53: "Susan B. Anthony Memorial Unrest Home", Ohio). (Decided 2026-10-23.)

The same land in the same issue can be two rows: a Country Connections
listing and an On the Land report are separate observations.

An On the Land entry about a business, project, or group with no land of its
own is not a row, even though it is printed in On the Land (e.g.
Groundworks, #53: Becky Bee's natural-building workshops, held on other
women's lands). This follows the `codebook.md` rule on groups without land.
(Decided 2026-10-23.)

An On the Land entry that is a personal journal or memoir from one woman's
land is not a row (e.g. Wildflower Farm, "A Partial Journal", #53): it tells
her own story rather than presenting the land, and doesn't say clearly who
lives there or who is welcome. (Decided 2026-10-23.)

OPEN QUESTION - splitting: no case yet of one report, listing or
announcement that covers several separate lands (e.g. a visit to three
places). If you find one, give each land its own row with the full shared
text as raw_text (as for LC joint listings), and start each row's notes with
"OPEN QUESTION (joint report):" followed by the other lands it was reported
with.

## page
The printed page number where the item begins, taken from the
`[Page number: N]` at the end of that page. If the page has no printed
number, leave page blank and give the image page (e.g. "image page-014") in
notes.

## raw_text
As in `codebook.md`: the full item, word for word, from its heading or name
to its last word, across pages if it continues. Leave out the page markers
and `[Page number: N]` lines. Keep `[Caption: ...]` text only if the caption
is about this land; leave out `[Illustration]`, `[Photo]` and `[Ad]` markers.
Long reports are copied in full.

## section
"Country Connections", "On the Land", or "Announcements".

## community_name
As in `codebook.md`. An announcement with no community name is named from
its heading, as printed (e.g. "WIMMIN'S LAND IN VERA CRUZ"). For an On the Land report, the land's name as printed
in its heading or first lines (DOE FARM, OWL FARM). If the heading names the
organization and the land (e.g. "DOE FARM/Wisconsin Women's Land
Cooperative"), copy it as printed.

## accepted_groups
The LC rules about the 1982-and-later questionnaire directories, the "We
welcome:" list, and the 1986 default do not apply to Maize, which has no
questionnaire form. Instead:
- "women", "womyn", "wimmin" (e.g. "a sanctuary for wimmin", "Wimmin
  wishing to live at OWL") mean Lesbian women + Non-lesbian women.
  (Decided 2026-10-23, for now; may be revisited.)
- "lesbians", "dykes" mean Lesbian women only.
- "Visitors are welcome" with no group named adds no group.
- An existing place that says it is open to or for "women" counts as
  welcoming them, e.g. "Any travelling woman is welcome to stop by"
  (Spinstervale) or "community homes for aging women and women with
  disabilities" (Spinsterhaven): Lesbian women + Non-lesbian women.
  (Decided 2026-10-24.)
- A land that is still only a plan (e.g. a group "buying land for womyn",
  with houses and gardens planned) gets no accepted groups, unless it
  explicitly says who is welcome ("open to all women", "we welcome..."):
  saying who the land is for is not yet an invitation. (Decided 2026-10-23,
  Wimmin's Land in Vera Cruz, #25.)
The rules in `codebook.md` for children, males, members, and explicit
restrictions apply as written.

## type
The rules in `codebook.md` apply, judged only from what this item itself
says, not from what is known about the land elsewhere. Example: OWL Farm
belongs to the Oregon Women's Land Trust, but its On the Land report (#25)
only describes residents living together, so it is Intentional
Community/Cooperative; a credit line naming a land trust's newsletter does
not make the land a Land Trust. (Decided 2026-10-23.)
A listing whose own name says it is a land trust ("OWL FARM/Oregon Women's
Land Trust", "SPIRALAND/Spiral Women's Land Trust", "... WOMEN'S LAND
TRUST") is Land Trust, even if the rest of the listing says nothing about
type. (Decided 2026-10-24.) This is different from a credit line naming a
land trust's newsletter, which doesn't count.
OPEN QUESTION - types that don't fit: no case yet of land the five types
don't fit well (e.g. land owned by shareholders, a land "co-op", a mix of
private and shared plots). If you find one, choose the closest type, and
start the notes with "OPEN QUESTION (type):" followed by what doesn't fit.

## Credit lines, illustration captions, and photo captions
Lines saying where a report came from (e.g. "Residents Reports Newsletter of
the Oregon Womens Land Trust") and illustration credits (an artist's name
and town) are not part of raw_text.
Photo captions about the land or its people are part of raw_text, even on
the next page, kept in their `[Caption: ...]` form at the end of the item,
with their photo credits (e.g. Westwind, #53: "[Caption: Rebecca in her
house at West Wind]"). (Decided 2026-10-23.)
