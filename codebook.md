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
  This includes a sentence inside the directory's introduction or an
  editor's note: if it names a community that has ended, that community gets
  its own not_a_listing row, with that sentence as `raw_text`. One sentence
  naming two ended communities gives two rows.
- A letter printed in the directory from a listed community that adds to or
  corrects its listing is also a not_a_listing row.
- Groups without land are not rows, even when LC prints them. Listings under
  an editor's note like "These groups don't have land, per se" are skipped,
  unless the listing itself says the group lives on or owns its own land
  (a lesbian residential community on its own property is a row even
  without acreage). Guest houses, inns, and trips that are only businesses,
  with no land community, are skipped too.
- Land groups LC says are "not women's land groups, but they do welcome
  lesbians" are rows, with `notes` beginning "NOT WOMEN'S LAND".
- One printed paragraph that names two separate groups is two rows. Each gets
  the full shared paragraph as `raw_text`, and `notes` says it was listed
  jointly. Example: LAND TRUSTS FOR WOMEN (1976) names both Oregon Women's
  Land Trust and California Women's Land Trust, each with its own address,
  so it is two rows.
- Not rows: anything that is not about land, such as listings of books,
  albums, records, publications, businesses, trips, or events, and the
  introduction or instructions at the start of the directory.

## community_name
- The name as printed, usually underlined or in capitals at the start.
- If a listing gives no name, use its opening words ("Four Women") or a place
  feature it names ("Elwha River land"), and say so in `notes`.

## raw_text
- The full listing, word for word, from its name to its last word. Never
  shortened, and never stopped early: copy through to the end of the
  "We have/are:" list when there is one.
- Only the listing itself. Section headings and editor's notes printed above
  a listing ("NOTE: The following is not a women's land group...") are not
  part of its `raw_text`; mention them in `notes` instead.
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
  Phone numbers are not recorded in their own field.
- `contact_name` is the person or people the mail goes to: the name after
  "c/o", or the person's name that heads a listing with no community name
  ("SUSAN STONE, Box 12...", "Rebecca, Susan, Anne & Maurine"). Fill it even
  when the community is named after that person. Leave it blank when the
  mail goes only to the community by its own name.
- Exception: a state code that is plainly a typo is corrected in the
  `*_state` fields ("Elk, AC 95432" stored as CA); `raw_text` keeps the
  printed form and `notes` records the correction.
- `land_*` is where the land itself is, which is often not where the mail
  goes (e.g. a Boston PO box for land in Maine). Explain every inference in
  `notes`. Decide it from the kind of mailing address:
  - **Rural route** (RD, RFD, Rt, RR, HCR, Star Route, e.g. "Rt 1 Box 240",
    "RD 5", "RFD 2 Box 3085"): this is the land. Copy all four parts of the
    mailing address (street, city, state, zip) into `land_*`.
  - **Street address or road** ("3100 Ridgewood Rd", "Box 130-Castine Rd",
    "Samson Rd"): this is the land, so copy all four parts, unless the
    listing shows the people live somewhere else (e.g. a city address while
    the land is described as elsewhere, owners "currently living in Boston",
    cabins only planned). Then leave `land_street_address`, `land_city` and
    `land_zip` blank.
  - **PO box** ("PO Box 274", "POB 133", "Box 1713" with no road): never the
    land. Leave `land_street_address` and `land_zip` blank.
  - Whatever the mailing address, if the listing names the town the land is
    in ("Located in Days Creek, OR", "(Unger, WV)"), put that town in
    `land_city`; otherwise do not guess a land city.
- `land_state` may be filled from a vague place ("southern Oregon" gives OR)
  or from the mailing state when the listing places the land nearby.
- `land_location_as_stated` keeps the listing's own words for where the land
  is, copied exactly, including the leading words ("Located in Days Creek,
  OR", "southern Oregon", "25 miles southeast of Tucson"). Only the place
  phrase: not distances to other cities or descriptions of the climate.
  Blank if the listing says nothing about where the land is beyond the
  address.
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
  without the word "retreat": a vacation ranch, a guest house, an
  educational center, a place that runs courses or workshops as its main
  purpose (Who Farm Inc, Penthesileia Inc, Hardscrabble Hill Center).
- Land the listing says one woman bought and hosts is Private/Individual Land.
  So is land women live on and are in the process of acquiring privately.
- **The two-woman rule.** Land owned or lived on by one or two women (a
  couple, "Mimi & Judy", "a partnership of 2 lesbians", "We have/are: 2
  lesbians") is Private/Individual Land. This is the most common type error,
  so check it before choosing Intentional Community/Cooperative.
  - Taking apprentices, work exchanges, guests, campers, or visitors does
    not change it.
  - It becomes Intentional Community/Cooperative only when the women
    already live on the land and the listing actively recruits more members
    to live there ("looking for 1-3 semi-collective members", "want other
    women to build houses and live here").
  - An owner who does not live there yet stays Private/Individual Land even
    when welcoming new members.
- Intentional Community/Cooperative is for three or more women, or a group
  that describes itself as a collective, family, or community, living on
  the land.
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
- One whole number only (never two numbers, never a sum of residents and
  non-resident members): members of the land community who live on the
  land. This includes members' children, and men when they are part of the
  collective. Renters count when the listing places them within the
  community; tenants from outside it do not.
- 0 means no members live there: the listing says so, or the owners live
  somewhere else ("currently living in Boston", housing only planned, cabins
  "for our personal use" in long-term plans). Blank means it does not say.
- A questionnaire count ("We have/are: 4 lesbians") counts as residents when
  the same list or the text says women live on the land ("women living on
  the land", "women living and working on the land", "We live..."). Then
  use the count. Without that, leave it blank and put the count in `notes`.
- Count only people the listing places on the land: "15 resident lesbians,
  90 lesbian/nonlesbian members from all over" is 15. "6 lesbians, 4 on the
  land" is 4.
- If a range is given, store the smaller number and note the range. Founders
  are not counted as current residents.
- Part-time family members are noted, not counted. Members who are the whole
  community but live there part-time are counted, with "part-time" in `notes`.

## accepted_groups
Who the listing welcomes, from the controlled vocabulary only.
- In the questionnaire directories (1982 and later), lesbians are never on the
  "We welcome:" list because the whole directory is for lesbians.
- **Non-lesbian women in the questionnaire directories (1982 on): code them
  only when the listing names them** ("nonlesbian women", "straight women",
  "non-lesbians"). General words like "women", "wimmin", "womyn",
  "lesbian-feminists", "women living on the land" mean lesbians, not
  non-lesbian women. This is the most common accepted-groups error. (LC's
  1986 directory says so outright: "If the groups are open to nonlesbians or
  dogs it will specifically say so in their listing".)
- Only in the 1976 prose directory, "women" or "all women" means Lesbian
  women + Non-lesbian women.
- Code Lesbian women for every questionnaire-directory listing that welcomes
  anyone or describes lesbians living there.
- "Children", or children with no gender given, means Girl children + Boy
  children.
- "Males" or "men" with no orientation given means Gay men + Non-gay men, with
  any conditions noted, including "(maybe)" or "(not overnight)". "Gay
  males" or "gay men" means Gay men only. In the 1982 directory, males are
  not coded unless the listing names them, because the editor says to
  assume they are not welcome.
- Code girl and boy children only from what the listing says about children
  ("girl children" is Girl children only; "boy babies" or "boy children
  under 7" is Boy children, with the condition noted).
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
- Read the whole listing for each focus in the list; a listing often has
  two or three. Check these in particular:
- **Recovery/substance-free:** any stated rule against drugs, alcohol, or
  dope is a rule of the place, so code it: "NO DRUGS!", "No drugs,
  cigarettes", "no drugs, alcohol or cigarettes", "no... drugs or dope", "Not
  into drug abuse". A ban on smoking tobacco alone is not enough. This is
  the focus most often missed.
- **Farming/self-sufficiency:** growing the group's own food or running a
  farm, stated as something the place does or aims to do ("will provide most
  of our food", "beef and milk cows, chickens, bees", "organic gardens, small
  livestock", "need to... be self-sufficient", homesteading).
- **Workshops/education:** the place runs or plans workshops, classes,
  courses, apprenticeships, or skill-sharing.
- **Archives/cultural work:** the place houses or runs an archive, press,
  magazine, library, arts or crafts production, or music (a feminist
  library, a publishing center, a stained-glass workshop).
- **Environmentalism/eco-friendly:** only an explicit environmental
  principle or practice: chemical-free land, "ecology and alternative
  technology", solar or appropriate technology, organic food-raising
  presented as a principle of the place. Organic gardening mentioned as part
  of farming ("organic gardens, small livestock, bees") is Farming only.
  "Living in harmony with nature" alone is not enough.
- **Lesbian separatism:** the listing names separatism as its own politics,
  or says only lesbians may live there. A listing that rejects separatism
  ("I am not a separatist") is not coded; note the rejection.
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
