#!/usr/bin/env python3
"""Extract land listings and reports from the Maize transcriptions.

Reads the page texts made in the Maize-OCR project, sends one whole issue at
a time to the model with codebook.md + codebook_maize.md, and writes one row
per Country Connections listing or community report, in the same columns as
the Lesbian Connection script (01_directory_to_csv.py).
"""

import json
import re
from pathlib import Path

from extraction_common import (
    CHOICE, CODEBOOK, COMMON_FIELDS, SCRIPT_DIR, apply_code_rules, build_schema,
    calculate_cost, call_model, check_cut_off, list_fields, load_sources,
    log_run, make_client, source_columns, start_run_record, vocabulary_text,
    write_rows,
)

# --- Codebook ---------------------------------------------------------------
# The Maize columns: row_kind first, then the columns shared with LC, then
# section and the page where the item begins. The full coding rules are in
# codebook.md and codebook_maize.md.

FIELDS = [
("row_kind",
 "'listing' for a Country Connections entry; 'report' for an On the Land entry; 'announcement' for a notice in Announcements by or about a specific land community; 'not_a_listing' for an entry in any of these sections saying a community has ended (see Maize codebook: What counts as a row).",
 CHOICE(["listing", "report", "announcement", "not_a_listing"])),
*COMMON_FIELDS,
("section",
 "'Country Connections', 'On the Land', or 'Announcements' (see Maize codebook: section)."),
("page",
 "The printed page number where the item begins, from the [Page number: N] at the end of that page; a number only. Blank if that page has no printed number."),
("image_page",
 "The image page where the item begins, from the marker line above it, e.g. 'page-014'."),
]

LIST_FIELDS = list_fields(FIELDS)

CODEBOOK_MAIZE = (SCRIPT_DIR / "codebook_maize.md").read_text(encoding="utf-8")

# {source} is filled in for each issue, e.g. "Maize, Spring 1997 (issue 53)".
# The issue's text follows this prompt in the same request.
PROMPT = """You are a historian creating structured data from historical sources from the 1970s, 80s, and 90s. Below the codebook is the full text of one issue of {source}, a magazine by and for lesbians living in the country, transcribed page by page. Extract every entry in the issue's Country Connections and On the Land sections, and every announcement in its Announcements section that is by or about a specific land community, as one row, in the order they appear, following the codebook and the Maize addendum below exactly.

Rules:
- Extract EVERY Country Connections and On the Land entry and every land
  announcement. Never skip one because a field is unclear or missing: leave
  that field empty instead.
- Do not extract anything outside those three sections, even when it is
  about a land community: articles, gathering reports, Land Lesy, letters,
  poems, reviews, how-to pieces. In Announcements, skip notices that are not
  about a specific land (gatherings, publications, businesses, events).
- raw_text is word for word as transcribed. Do not correct spelling, expand
  abbreviations, or modernize anything there.

""" + CODEBOOK + "\n\n" + CODEBOOK_MAIZE + "\n\n# Controlled vocabularies\n\n" + vocabulary_text()

# --- Settings ---------------------------------------------------------------

# A model name starting with "claude-" is sent to Anthropic (needs
# ANTHROPIC_API_KEY in .env); anything else is sent to Gemini (GEMINI_API_KEY).
# Prices are in PRICES in extraction_common.py.
MODEL = "gemini-3.8-flash"

# How hard a Claude model thinks before answering. (Gemini ignores this.)
CLAUDE_EFFORT = "high"

# Each run saves everything to its own folder: output/runs/<RUN_NAME>/
# Use a new name whenever you change MODEL or the codebooks, so earlier
# results are kept. Reuse the same name to retry issues that failed or to
# add more issues to a run.
RUN_NAME = "2026-10-23_maize-v1_flash-3.8"

# The page transcriptions made in the Maize-OCR project, one folder per issue
MAIZE_TEXT_FOLDER = (Path.home() / "Desktop" / "Maize-OCR" / "output" / "runs"
                     / "2026-10-23_all_haiku-5.5" / "text")

RUN_FOLDER = SCRIPT_DIR / "output" / "runs" / RUN_NAME
OUTPUT_FILE = RUN_FOLDER / "land_directory.csv"
SETTINGS_FILE = RUN_FOLDER / "settings.json"

# Each issue's results are saved here as soon as the model returns them, and
# an issue that already has a file here is not sent again.
ISSUES_FOLDER = RUN_FOLDER / "issues"

# Only extract these issues (folder names in MAIZE_TEXT_FOLDER), to check the
# results before a full run. Set to [] to extract every issue.
# The test set: the two issues hand-coded in reference/maize_handcoded/.
TEST_ISSUES = ["maize-53-spring1997"]

# codebook_maize.md is a draft until its "TO DECIDE" notes are replaced by
# decisions. The script won't send anything while they're there, unless this
# is set to True (for trying the script itself, not for real results).
ALLOW_DRAFT_CODEBOOK = False

# ----------------------------------------------------------------------------


def maize_issue_name(file_name):
    """'primary/maize/MaizeNumber35Winter 9993.pdf' -> 'maize-35-winter1993',
    the same folder names the Maize-OCR project uses."""
    match = re.search(r"Number(\d+)\s*([A-Za-z]+)\s*(\d{4})", Path(file_name).stem)
    if not match:
        return ""
    number, season, year = match.groups()
    return f"maize-{number}-{season.lower()}19{year[-2:]}"


def issue_text(issue_folder):
    """All of an issue's pages in order, each starting with a marker line
    like '=== image page-014 ===' so the model can tell where items begin."""
    parts = []
    for page in sorted(issue_folder.glob("page-*.txt")):
        parts.append(f"=== image {page.stem} ===\n{page.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(parts)


def extract_issue(client, issue_folder, source_text):
    """Send one whole issue to the model and return (parsed data, input
    tokens, output tokens)."""
    prompt = (PROMPT.replace("{source}", source_text)
              + "\n\n# The issue\n\n" + issue_text(issue_folder))
    return call_model(client, MODEL, prompt, build_schema(FIELDS, page_number=False),
                      claude_effort=CLAUDE_EFFORT)


def check_entries(entries):
    """Quick sanity checks. These don't prove the data is right,
    but they catch some common problems."""
    for entry in entries:
        if not entry["community_name"]:
            print(f"    CHECK: a {entry['row_kind']} on {entry['image_page']} has no community name")
        if not entry["page"]:
            print(f"    CHECK: {entry['community_name'] or '(no name)'} has no printed page number")


def run_settings():
    """The settings that decide what the model returns. A run keeps one set."""
    return {"model": MODEL, "prompt": PROMPT, "fields": [list(field) for field in FIELDS]}


def main():
    if "TO DECIDE" in CODEBOOK_MAIZE and not ALLOW_DRAFT_CODEBOOK:
        print("codebook_maize.md still has TO DECIDE notes. Replace them with your "
              "decisions before running (or set ALLOW_DRAFT_CODEBOOK = True to try "
              "the script itself).")
        return
    client = make_client(MODEL)
    if client is None:
        return

    issues = sorted(p for p in MAIZE_TEXT_FOLDER.iterdir() if p.is_dir())
    if TEST_ISSUES:
        issues = [p for p in issues if p.name in TEST_ISSUES]
        print(f"TEST RUN: only {len(issues)} of the issues (see TEST_ISSUES)\n")
    if not issues:
        print(f"No issue folders found in {MAIZE_TEXT_FOLDER}")
        return
    if not start_run_record(RUN_NAME, RUN_FOLDER, SETTINGS_FILE, run_settings()):
        return
    print(f"Run: {RUN_NAME}  (saving to {RUN_FOLDER.relative_to(SCRIPT_DIR)})\n")

    # Maize issues are looked up by the same folder names as the transcriptions
    sources = load_sources(lambda row: maize_issue_name(row["file_name"]))
    ISSUES_FOLDER.mkdir(parents=True, exist_ok=True)
    all_rows = []
    failed = []
    total_cost = 0.0

    for issue_folder in issues:
        issue = issue_folder.name
        if issue not in sources:
            print(f"SKIPPED: {issue} is not in reference/sources.csv; add it there")
            failed.append(f"{issue}: not in reference/sources.csv")
            continue
        source = source_columns(sources[issue])
        number = sources[issue]["issue"]
        source_text = f"Maize, {source['month_recorded']} {source['year_recorded']} (issue {number})"
        saved_issue = ISSUES_FOLDER / f"{issue}.json"
        if saved_issue.exists():
            print(f"Using saved results for {issue}")
            data = json.loads(saved_issue.read_text(encoding="utf-8"))
            tokens = None
        else:
            print(f"Extracting {issue} ...")
            try:
                data, *tokens = extract_issue(client, issue_folder, source_text)
            except Exception as err:
                print(f"  FAILED: {err}\n")
                failed.append(f"{issue}: {err}")
                continue
            saved_issue.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Add the columns that code fills in, not the model
        for entry in data["entries"]:
            entry["page"] = re.sub(r"\D", "", entry["page"])
            entry.update(source)
            entry["issue"] = issue
            entry["source_image"] = f"{issue}/{entry['image_page']}"
            entry["split_across_pages"] = ""
            all_rows.append(entry)

        kinds = {kind: sum(1 for e in data["entries"] if e["row_kind"] == kind)
                 for kind in ("listing", "report", "announcement", "not_a_listing")}
        print(f"  {len(data['entries'])} rows: {kinds['listing']} listings, "
              f"{kinds['report']} reports, {kinds['announcement']} announcements, "
              f"{kinds['not_a_listing']} not_a_listing")
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
    check_cut_off(all_rows)
    # The Lesbian women rule for Maize is still to be decided (codebook_maize.md:
    # accepted_groups), so only the source-independent rules run for now
    apply_code_rules(all_rows)

    # Same columns as the LC sheet, so the comparison script and the database
    # build can read both
    columns = ([field[0] for field in FIELDS if field[0] != "image_page"]
               + ["split_across_pages", "source_id", "publication",
                  "year_recorded", "month_recorded", "issue", "source_image"])
    write_rows(OUTPUT_FILE, all_rows, columns, LIST_FIELDS)

    print("=" * 40)
    print(f"Saved {len(all_rows)} rows to {OUTPUT_FILE.relative_to(SCRIPT_DIR)}")
    print(f"Total cost: ${total_cost:.6f}")
    log_run(SETTINGS_FILE, {
        "test_issues": TEST_ISSUES,
        "issues": [p.name for p in issues],
        "failed": failed,
        "rows": len(all_rows),
        "cost_usd": round(total_cost, 6),
    })
    if failed:
        print(f"\n{len(failed)} issue(s) failed:")
        for failure in failed:
            print(f"  {failure}")
        print("Run the script again to retry them; saved issues won't be sent again.")


if __name__ == "__main__":
    main()
