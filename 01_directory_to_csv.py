#!/usr/bin/env python3
"""Extract Lesbian Connection land directory listings from page images.

The parts shared with the Maize script (codebook columns, vocabularies,
model calls, costs, checks, run folders) are in extraction_common.py.
"""

import json
import re
from pathlib import Path

from extraction_common import (
    CHOICE, CODEBOOK, COMMON_FIELDS, SCRIPT_DIR, apply_code_rules, build_schema,
    calculate_cost, call_model, check_cut_off, ends_complete, list_fields,
    load_sources, log_run, make_client, source_columns, start_run_record,
    vocabulary_text, write_rows,
)

# --- Codebook ---------------------------------------------------------------
# The LC columns: row_kind first, then the columns shared with Maize, then
# section and continues_previous. The full coding rules are in codebook.md.

FIELDS = [
("row_kind",
 "'listing' for a directory listing that describes land; 'not_a_listing' for a notice that a community has ended, or a letter from a listed community (see codebook: What counts as a row).",
 CHOICE(["listing", "not_a_listing"])),
*COMMON_FIELDS,
("section",
 "The nearest centered section heading above this listing on this page, exactly as printed. Blank if none on this page."),
("continues_previous",
 "'yes' only if this is the first text on the page and it is the end of a listing that began on the previous page (it does not start with a community name). Leave community_name blank for it. Otherwise blank."),
]

LIST_FIELDS = list_fields(FIELDS)

# {source} is filled in for each page, e.g. "Lesbian Connection, December-January 1982",
# because several coding rules depend on the date.
PROMPT = """You are a historian creating structured data from historical sources from the 1970s, 80s, and 90s. This image is a page from {source}. It is part of the land directory, which listed women's land communities. Extract every listing on the page as one row, in the order they appear, following the codebook below exactly.
Some listings continue from one page to the next. If the text at the top of the page does not start with a community name, it is the end of a listing from the previous page: extract it as its own entry and follow the instructions for the continues_previous column.
Do not extract these as rows: the page number, the running header, section headings (record them in the section field instead), introductory or explanatory paragraphs that are not a listing, anything that is not about land (books, albums, publications, trips, events, businesses with no land of their own), the "This content downloaded from..." notice at the bottom of the page, and faint text showing through from the back of the page.

Rules:
- Extract EVERY listing. Never skip one because a field is unclear or
  missing: leave that field empty instead.
- raw_text is word for word as printed. Do not correct spelling, expand
  abbreviations, or modernize anything there.
- Also report the printed page number.

""" + CODEBOOK + "\n\n# Controlled vocabularies\n\n" + vocabulary_text()

# --- Settings ---------------------------------------------------------------

# A model name starting with "claude-" is sent to Anthropic (needs
# ANTHROPIC_API_KEY in .env); anything else is sent to Gemini (GEMINI_API_KEY).
# Prices are in PRICES in extraction_common.py.
MODEL = "claude-opus-5-5"

# How hard a Claude model thinks before answering: low, medium, high, xhigh, max.
# Higher costs more. (Gemini ignores this.)
CLAUDE_EFFORT = "high"

# Each run saves everything to its own folder: output/runs/<RUN_NAME>/
# Use a new name whenever you change MODEL, PROMPT, or FIELDS, so earlier
# results are kept. Reuse the same name to retry pages that failed or to
# add more pages to a run.
RUN_NAME = "2026-10-23_codebook-v4_opus-5.5"

IMAGE_FOLDER = SCRIPT_DIR / "images"
RUN_FOLDER = SCRIPT_DIR / "output" / "runs" / RUN_NAME
OUTPUT_FILE = RUN_FOLDER / "land_directory.csv"
SETTINGS_FILE = RUN_FOLDER / "settings.json"

# Each page's results are saved here as soon as the model returns them, and a
# page that already has a file here is not sent again.
PAGES_FOLDER = RUN_FOLDER / "pages"

# Only extract these images, to check the results before a full run.
# Set to [] to extract every image in IMAGE_FOLDER.
# These are the directory pages of the 5 issues hand-checked in Project 1
# (september76-014 is printed p. 12, not hand-checked, but a listing may
# continue from it onto p. 13).
TEST_PAGES = (
    [f"lc-september76-{n:03}.png" for n in range(14, 17)]
    + [f"lc-december82-{n:03}.png" for n in range(23, 28)]
    + [f"lc-march83-{n:03}.png" for n in range(20, 22)]
    + [f"lc-june83-{n:03}.png" for n in range(24, 27)]
    + [f"lc-march86-{n:03}.png" for n in range(9, 14)]
    # Not hand-checked, so not scored: the page Gemini refused (RECITATION)
    # in the 2026-10-21 run, to see whether that still happens
    + ["lc-july88-023.png"]
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# ----------------------------------------------------------------------------


def extract_page(client, image_path, source_text):
    """Send one image to the model and return (parsed data, input tokens,
    output tokens)."""
    return call_model(client, MODEL, PROMPT.replace("{source}", source_text),
                      build_schema(FIELDS), image_path=image_path, claude_effort=CLAUDE_EFFORT)


def issue_from_filename(image_path):
    """Code pulls the issue out of the filename: 'lc-may86-011.png' -> 'may86'."""
    match = re.match(r"lc-([a-z]+\d{2})-", image_path.name)
    return match.group(1) if match else ""


def image_number(image_name):
    """Code pulls the image's position in the issue: 'lc-may86-011.png' -> 11."""
    match = re.search(r"-(\d+)\.\w+$", image_name)
    return int(match.group(1)) if match else -1


def month_year_from_issue(issue):
    """Code turns the issue into a month and year: 'may86' -> ('May', '1986')."""
    match = re.fullmatch(r"([a-z]+)(\d{2})", issue)
    if not match:
        return "", ""
    month, year = match.groups()
    return month.capitalize(), f"19{year}"


def lc_source_columns(issue, sources):
    """The source columns for one LC issue. An issue missing from sources.csv
    gets its month and year from the file name, and no source_id."""
    if issue in sources:
        return source_columns(sources[issue])
    month, year = month_year_from_issue(issue)
    return {"source_id": "", "publication": "Lesbian Connection",
            "year_recorded": year, "month_recorded": month}


def page_digits(page_number):
    """The printed page as a number: '-13-' -> '13'."""
    match = re.search(r"\d+", page_number or "")
    return match.group() if match else ""


def check_entries(entries):
    """Quick sanity checks. These don't prove the data is right,
    but they catch some common problems."""
    for entry in entries:
        if entry["continues_previous"].strip().lower() == "yes":
            continue
        if not entry["community_name"]:
            print(f"    CHECK: a listing has no community name (missed continuation?)")
        elif (entry["row_kind"] == "listing"
              and not entry["contact_street_address"] and not entry["contact_city"]):
            print(f"    CHECK: {entry['community_name']} has no mailing address")


def lc_adds_lesbian_women(row):
    """In LC's questionnaire directories (1982 on), lesbians are never on the
    "We welcome:" list because the whole directory is for lesbians, so
    Lesbian women is coded for every listing that welcomes anyone."""
    return row["year_recorded"] >= "1982"


def merge_continuations(rows):
    """Code, not the model, joins a listing split across two pages:
    a row marked continues_previous is added onto the row before it."""
    merged = []
    for row in rows:
        is_continuation = row["continues_previous"].strip().lower() == "yes"
        prev = merged[-1] if merged else None
        # Only join onto the image just before this one, so a failed or
        # skipped page can't attach a fragment to the wrong listing
        prev_image = prev["source_image"].split("; ")[-1] if prev else ""
        if (is_continuation and prev and prev["issue"] == row["issue"]
                and image_number(prev_image) + 1 == image_number(row["source_image"])):
            # If the listing before already ended with a full sentence and the
            # fragment starts mid-sentence, the fragment probably belongs to a
            # listing the model skipped at the bottom of the previous page
            fragment = row["raw_text"].strip()
            if ends_complete(prev["raw_text"]) and fragment[:1].islower():
                print(f"CHECK: fragment '{fragment[:40]}...' was joined onto "
                      f"{prev['community_name']}, which already looked complete. "
                      f"Was a listing skipped at the bottom of {prev_image}?")
            for name in (field[0] for field in FIELDS):
                if name in ("row_kind", "type", "community_name", "section",
                            "continues_previous") or not row[name]:
                    continue
                if name in ("acreage", "num_residents"):
                    # A number is never joined as text ("2" + "2" is not "2 2"):
                    # keep the first page's number if it has one
                    prev[name] = prev[name] or row[name]
                elif name in LIST_FIELDS:
                    prev[name] += [item for item in row[name] if item not in prev[name]]
                else:
                    prev[name] = f"{prev[name]} {row[name]}".strip()
            prev["source_image"] += f"; {row['source_image']}"
            prev["split_across_pages"] = "yes"
            print(f"MERGED: fragment from {row['source_image']} into {prev['community_name']}")
        else:
            if is_continuation:
                print(f"CHECK: {row['source_image']} has a continuation with no listing before it")
            row["split_across_pages"] = ""
            merged.append(row)
    return merged


def fill_sections(rows):
    """A section heading applies until the next one, even across pages,
    so code carries it forward within each issue."""
    current = {}
    for row in rows:
        if row["section"]:
            current[row["issue"]] = row["section"]
        else:
            row["section"] = current.get(row["issue"], "")


def run_settings():
    """The settings that decide what the model returns. A run keeps one set."""
    return {"model": MODEL, "prompt": PROMPT, "fields": [list(field) for field in FIELDS]}


def main():
    client = make_client(MODEL)
    if client is None:
        return

    images = sorted(p for p in IMAGE_FOLDER.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    if TEST_PAGES:
        images = [p for p in images if p.name in TEST_PAGES]
        print(f"TEST RUN: only {len(images)} of the images (see TEST_PAGES)\n")
    if not images:
        print(f"No images found in {IMAGE_FOLDER}")
        return
    if not start_run_record(RUN_NAME, RUN_FOLDER, SETTINGS_FILE, run_settings()):
        return
    print(f"Run: {RUN_NAME}  (saving to {RUN_FOLDER.relative_to(SCRIPT_DIR)})\n")

    # LC issues are looked up by file name: 'lc-december82.pdf' -> 'december82'
    sources = load_sources(lambda row: Path(row["file_name"]).stem.removeprefix("lc-"))
    PAGES_FOLDER.mkdir(parents=True, exist_ok=True)
    all_rows = []
    failed = []
    total_cost = 0.0

    for image_path in images:
        issue = issue_from_filename(image_path)
        source = lc_source_columns(issue, sources)
        if not source["source_id"]:
            print(f"CHECK: {issue} is not in reference/sources.csv; add it there")
        source_text = f"{source['publication']}, {source['month_recorded']} {source['year_recorded']}"
        saved_page = PAGES_FOLDER / f"{image_path.stem}.json"
        if saved_page.exists():
            print(f"Using saved results for {image_path.name}")
            data = json.loads(saved_page.read_text(encoding="utf-8"))
            tokens = None
        else:
            print(f"Extracting {image_path.name} ...")
            try:
                data, *tokens = extract_page(client, image_path, source_text)
            except Exception as err:
                print(f"  FAILED: {err}\n")
                failed.append(f"{image_path.name}: {err}")
                continue
            saved_page.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Add the columns that code fills in, not the model
        for entry in data["entries"]:
            entry["page"] = page_digits(data["page_number"])
            entry.update(source)
            entry["issue"] = issue
            entry["source_image"] = image_path.name
            all_rows.append(entry)

        print(f"  Page {data['page_number'] or '?'}: {len(data['entries'])} listings "
              f"(count them on the page -- do they match?)")
        check_entries(data["entries"])

        if tokens is None:
            print()
            continue
        input_tokens, output_tokens = tokens
        cost = calculate_cost(MODEL, input_tokens, output_tokens)
        total_cost += cost
        print(f"  Tokens: {input_tokens:,} in, {output_tokens:,} out   "
              f"Cost: ${cost:.6f}\n")

    print("=" * 40)
    all_rows = merge_continuations(all_rows)
    check_cut_off(all_rows)
    fill_sections(all_rows)
    apply_code_rules(all_rows, adds_lesbian_women=lc_adds_lesbian_women)

    # The codebook sets the column order; code-added columns go at the end
    columns = ([field[0] for field in FIELDS if field[0] != "continues_previous"]
               + ["split_across_pages", "page", "source_id", "publication",
                  "year_recorded", "month_recorded", "issue", "source_image"])
    write_rows(OUTPUT_FILE, all_rows, columns, LIST_FIELDS)

    print("=" * 40)
    print(f"Saved {len(all_rows)} rows to {OUTPUT_FILE.relative_to(SCRIPT_DIR)}")
    print(f"Total cost: ${total_cost:.6f}")
    log_run(SETTINGS_FILE, {
        "test_pages": TEST_PAGES,
        "images": [p.name for p in images],
        "failed": failed,
        "rows": len(all_rows),
        "cost_usd": round(total_cost, 6),
    })
    if failed:
        print(f"\n{len(failed)} page(s) failed:")
        for failure in failed:
            print(f"  {failure}")
        print("Run the script again to retry them; saved pages won't be sent again.")


if __name__ == "__main__":
    main()
