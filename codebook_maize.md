# Codebook addendum: Maize

This file is read into the Maize extraction prompt by `03_maize_to_csv.py`,
after `codebook.md`. Where the two disagree, this file wins for Maize.
`codebook.md` was written for Lesbian Connection's land directories; its
rules for raw_text, addresses, type, acreage, num_residents and focuses apply
to Maize as written unless this file says otherwise.

DRAFT: the sections marked TO DECIDE need my decisions (made while
hand-coding issues 25 and 53) before any paid run.

## The source
Maize: A Lesbian Country Magazine (1990-1998), quarterly. Each request gives
one whole issue as transcribed text, page by page. Each page starts with a
marker line like `=== image page-014 ===`; the printed page number, when the
page has one, is at the end of the page as `[Page number: N]`. Headings are
lines starting with `## `. The text was transcribed by machine and can have
small errors, especially in names.

## What counts as a row
Only two kinds of item become rows:

- **listing** (`row_kind` = listing): one entry in the Country Connections
  directory (from 1992 on): a land's name, address, and usually a few lines
  about it.
- **report** (`row_kind` = report): a piece of writing by or about one land
  community that presents that community: what it is, where, who lives there,
  what it offers or needs. This includes:
  - an entry in the On the Land section (often under its own `## ` heading,
    e.g. `## DOE FARM`)
  - a notice in the Land Lesy section
  - an article elsewhere in the issue whose subject is one land community
    (often headed with its name, e.g. `## OWL FARM`)
- **not_a_listing**: a notice that a land community has ended (sold, folded,
  dissolved), as in `codebook.md`.

Not rows:
- passing mentions of a land in an article, poem, review, how-to piece, or
  announcement that is about something else
- Announcements, unless one is itself a land community presenting itself
  (TO DECIDE: is that a report?)
- Letters - TO DECIDE: does a letter from a land community about itself
  count as a report?
- gatherings, festivals, workshops and events that are not a land community
  (but a report from a land that hosts one is a row about that land)
- groups without land of their own, as in `codebook.md`

The same land in the same issue can be two rows: a Country Connections
listing and an On the Land report are separate observations.

TO DECIDE - splitting: a report that covers several lands (e.g. a visit to
three places): one row per land, each with the full shared text as raw_text
and notes saying it was reported jointly (as for LC joint listings)?

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
The Maize section the item is in, as printed: "Country Connections", "On the
Land", "Land Lesy", or the article's own heading for a stand-alone article.

## community_name
As in `codebook.md`. For a report, the land's name as printed in its heading
or first lines (DOE FARM, OWL FARM). If the heading names the organization and
the land (e.g. "DOE FARM/Wisconsin Women's Land Cooperative"), copy it as
printed.

## accepted_groups
TO DECIDE. The LC rules about the 1982-and-later questionnaire directories,
the "We welcome:" list, and the 1986 default do not apply to Maize, which
has no questionnaire form. Questions:
- Maize is "by and for lesbians". Is Lesbian women coded for every listing
  or report that welcomes anyone, as for LC from 1982 on?
- Do "women", "womyn", "wimmin" mean lesbians only, or lesbian and
  non-lesbian women?
- Are Non-lesbian women coded only when named ("straight women", "all women
  regardless of orientation")?
The rules in `codebook.md` for children, males, members, and explicit
restrictions apply as written.

## type
The rules in `codebook.md` apply. TO DECIDE while hand-coding: anything in
Maize they don't fit (e.g. land shared by shareholders or a land "co-op").
