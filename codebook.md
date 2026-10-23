# Codebook: LC land directory listings as a flat sheet

This file is read into the extraction prompt by `01_directory_to_csv.py`, so
it is both the documentation of the coding rules and the model's instructions.
It is adapted from the Project 1 rules (`8510-Project1/docs/data_model.md`).
One row in the flat sheet is one observation: one listing of one community on
one page of one issue. The controlled vocabularies (types, accepted groups,
focuses) are added below this file by the script, from `reference/`.

Rules from Project 1 that need several issues at once are left out here and
are done later, by code or by hand: matching listings to communities,
renaming communities, closing dates, and merging an organization with its land.

## What counts as a row
- Every listing in the land directory that describes land is a row
  (`row_kind` = listing).
- A notice on the directory page that a community has ended ("has folded",
  "LAND SOLD", land "wound up in legal dissolution") is a row with
  `row_kind` = not_a_listing, no type, and `notes` beginning "Not a listing".
  So is a letter printed in the directory from a listed community that adds
  to or corrects its listing.
- Groups without land are not rows, even when LC prints them, e.g. groups
  under an editor's note like "These groups don't have land, per se".
  Exception: a lesbian residential community on its own property is a row
  even without acreage.
- Land groups LC says are "not women's land groups, but they do welcome
  lesbians" are rows, with `notes` beginning "NOT WOMEN'S LAND".
- One printed paragraph that names two separate groups is two rows. Each gets
  the full shared paragraph as `raw_text`, and `notes` says it was listed
  jointly.
- Not rows: anything that is not about land, such as listings of books,
  albums, records, publications, businesses, trips, or events, and the
  introduction or instructions at the start of the directory.

## community_name
- The name as printed, usually underlined or in capitals at the start.
- If a listing gives no name, use its opening words ("Four Women") or a place
  feature it names ("Elwha River land"), and say so in `notes`.

## raw_text
- The full listing, word for word. Never shortened.
- Keep the page's own spellings and typos ("accomodate", "no woman woman").
- Join a word split by a hyphen at a line break ("Holly-wood" becomes
  "Hollywood"); keep hyphens that belong to the text.
- Join paragraphs within a listing with a single space. Do not mark
  underlining.
- Write `[?]` for a character that cannot be read, and explain it in `notes`.
- Phone numbers and names stay in `raw_text` as printed.

## description
- A short summary in your own words of what the listing says about the place:
  what it is, where, its land and buildings, who lives there, and what it
  offers or is looking for.
- Use the controlled vocabulary's terms (e.g. "gay men", "non-lesbian
  women"), not the listing's.

## Addresses and location
- `contact_*` is the mailing address as printed, including misspellings.
  `contact_name` is a person or group the mail is addressed to ("c/o ...")
  when it is not the community itself. Phone numbers are not recorded in
  their own field.
- Exception: a state code that is plainly a typo is corrected in the
  `*_state` fields ("Elk, AC 95432" stored as CA); `raw_text` keeps the
  printed form and `notes` records the correction.
- `land_*` is where the land itself is, which is often not where the mail
  goes (e.g. a Boston PO box for land in Maine). Fill it only when the listing
  says so or the inference is strong, and explain every inference in `notes`.
  Strong inferences: mail addressed to a named farm or to the place itself; a
  street address for a group that "opens their house"; a rural route or RD box
  used for reservations. A PO box is never the land.
- `land_state` may be filled from a vague place ("southern Oregon" gives OR).
- `land_location_as_stated` keeps the listing's own wording for vague places
  ("southern Oregon", "25 miles southeast of Tucson").
- A country other than the US goes in `notes`.

## type
Every type is a judgment; explain it in `notes`. Judge the type at the date
of this listing.
- A group already living on its land is a community (usually Intentional
  Community/Cooperative), even if the land is not paid off. An unpaid mortgage
  alone does not make it a land fund.
- A group not yet on land, still negotiating, or with no land mentioned is
  Land Fund/Seeking Land.
- Land the listing says is held "in a land trust" is Land Trust, whatever
  else the listing calls itself.
- A place that calls itself a retreat is Retreat/Gathering Space, even if
  people live there. If it calls itself both a community and a retreat, use
  the one it names first.
- A place defined by what it offers visitors is Retreat/Gathering Space even
  without the word "retreat": a vacation ranch, a guest house, an educational
  center.
- Land the listing says one woman bought and hosts is Private/Individual Land.
  So is land women live on and are in the process of acquiring privately.
- One or two women living on their land are Private/Individual Land, unless
  the listing recruits members to build a community; then it is Intentional
  Community/Cooperative. An owner who does not live there yet stays
  Private/Individual Land even when welcoming new members.
- A bare listing (only the "We have/are" form, no description) gets no type,
  and `notes` says it is a bare listing.
- A not_a_listing row gets no type.

## acreage
- A number only (3/4 acre is 0.75). Blank if not given.
- If the listing gives two different figures, store the smaller and note both.
- Only land the listing presents as the group's own. Land they only have
  "access to", or that "surrounds" them, is left out and noted.
- For a Land Fund/Seeking Land listing, record the acreage they are trying to
  acquire and note that it is not yet held.

## num_residents
- A whole number: members of the land community who live on the land. This
  includes members' children, and men when they are part of the collective.
  Renters count when the listing places them within the community; tenants
  from outside it do not.
- 0 means the listing says no members live there. Blank means it does not say.
- A questionnaire count ("We have/are: 4 lesbians") counts members. Use it
  only when the listing makes clear they live on the land; otherwise put it in
  `notes`.
- If a range is given, store the smaller number and note the range. Founders
  are not counted as current residents.
- Part-time family members are noted, not counted. Members who are the whole
  community but live there part-time are counted, with "part-time" in `notes`.

## accepted_groups
Who the listing welcomes, from the controlled vocabulary only.
- In the questionnaire directories (1982 and later), lesbians are never on the
  "We welcome:" list because the whole directory is for lesbians.
- From 1986 on, LC says: "If the groups are open to nonlesbians or dogs it
  will specifically say so in their listing". So from 1986 on, code
  Non-lesbian women only when the listing names them, and read general words
  like "women" or "wimmin" as lesbians.
- Before 1986, "women" or "all women" means Lesbian women + Non-lesbian women.
- "Children", or children with no gender given, means Girl children + Boy
  children.
- "Males" or "men" with no orientation given means Gay men + Non-gay men, with
  any conditions noted. In the 1982 directory, males are not coded unless the
  listing names them, because the editor says to assume they are not welcome.
- People who are members of the land community are coded even when the
  welcome list leaves them out. People on the land who are not members
  (tenants, visiting friends) are not coded.
- Follow explicit restrictions ("live only with dykes", "female children
  only").
- Explain every inferred group in `notes`. A listing that names no one gets
  an empty list.

## focuses
What the community was built around, beyond who is welcome.
- Code a focus only when the listing presents it as a purpose, identity, or
  rule of the place, not a passing mention or a checked questionnaire box
  ("We have/are: ... farm land" alone is not a farming focus).
- Environmentalism/eco-friendly needs an explicit practice: chemical-free
  land, organic food-raising, solar or appropriate technology. "Living in
  harmony with nature" alone is not enough.
- Women of color: only when the listing explicitly invites, recruits, or
  centers women of color. Statements of inclusiveness or anti-racism go in
  `notes`, not coded.
- Code what a place is, not what it opposes. A rejection (e.g. finding
  separatism "unworkable") goes in `notes`.

## notes
- Explain every judgment call: the type, each inferred accepted group, each
  focus, any inferred land location, corrections, ranges, and anything
  unreadable. Quote the listing's words that the judgment rests on.
- Use the controlled vocabulary's terms.

## section, continues_previous
- `section`: the nearest centered section heading above the listing on this
  page (e.g. GUEST HOUSES/RETREATS/ETC), or blank.
- `continues_previous`: "yes" only for the first text on the page when it does
  not start with a community name because it is the end of a listing from the
  previous page. Leave `community_name` blank for it and fill the other fields
  from the text it contains.
