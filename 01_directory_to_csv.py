#!/usr/bin/env python3

import csv
import json
import mimetypes
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Codebook ---------------------------------------------------------------
# One entry per column: (column name, instructions for the model).
# Change the columns here and the schema and CSV header change with them.

FIELDS = [
("section",
 "If a centered, underlined section heading (e.g. TRIPS, ALTERNATIVE LAND) appears on this page above this listing, transcribe the nearest one exactly as printed. If no heading appears above it on this page, leave blank."),
("community_name",
 "Transcribe the community name exactly as written. This is usually underlined, in bold, or in all capital letters at the beginning of a listing. (e.g. FEATHERS FARM, DUTCH MOUNTAIN, NORTH CROW VACATION RANCH)"),
("street_address", 
 "Transcribe the street address exactly as printed. If it is not included, leave blank."),
("city",
 "Transcribe the city or town exactly as printed. If it is not included, leave blank."),
("state",
 "Transcribe the state or province exactly as printed. If it is not included, leave blank."),
("zip", 
 "Transcribe the zip or postal code exactly as printed. If it is not provided, leave blank."),
("country",
 "Transcribe the country exactly as printed. If it is not included, leave blank."),
("phone", 
 "Transcribe the phone numbers exactly as printed. If it is not included, leave blank."),
("acreage",
 "Transcribe the number of acres of the land community exactly as printed, if it is provided. (e.g. 3/4 acre, 100 acres) If not, leave blank."),
("num_residents",
 "Transcribe the number of residents exactly as printed. Do not count, add up, or estimate. (e.g. 4 lesbians, 1 nonlesbian) If it is not provided, leave blank."),
("land_description", 
 "Transcribe verbatim the description of the land community as described in the listing. If there is none, leave blank."),
("welcomed_groups", 
 "If a listing specifically notes that they welcome certain types of people, include those people here. (e.g. 'We welcome: girl children' 'We welcome: girl children, boy babies, nonlesbian women')"),
("notes",
 "Transcribe exactly as printed any information in the listing that is not already captured in another field. Do not repeat text that is in another field. Leave empty if there is nothing left over."),
 ("continues_previous", 
  "Write 'yes' only if this is the first text on the page and it does not start with a community name, because it is the end of a listing that began on the previous page. It may start partway through a sentence, address, or phone number. Leave community_name blank and put the text in whichever other fields fit. Otherwise leave this blank.")
]

PROMPT = """You are a historian creating structured data from historical sources from the 1970s, 80s, and 90s. This image is a page from the periodical Lesbian Connection. Specifically, it is part of Lesbian Connection's Land Directory, which listed communities across the country. Extract every listing on the page as one row, in the order they appear.
Some listings continue from one page to the next. If the text at the top of the page does not start with a community name, it is the end of a listing from the previous page: extract it as its own entry and follow the instructions for the continues_previous column.
Do not extract these as listings: the page number, section headings (record them in the section field instead), introductory or explanatory paragraphs that are not a listing, the "This content downloaded from..." notice at the bottom of the page, and faint text showing through from the back of the page.

Rules:
- Extract EVERY entry. Never skip an entry because a field is unclear or
  missing: leave that field empty instead. An entry with blank fields is
  better than a missing entry.
- Transcribe exactly as printed. Do not correct spelling, expand
  abbreviations, or modernize anything.
  Also report the printed page number. """

# --- Settings ---------------------------------------------------------------

MODEL = "gemini-3.5-flash-lite"

# Paid-tier prices in US dollars per 1 million tokens: (input, output).
# Check https://ai.google.dev/gemini-api/docs/pricing -- prices change.
PRICES = {
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
}

# Each run saves everything to its own folder: output/runs/<RUN_NAME>/
# Use a new name whenever you change MODEL, PROMPT, or FIELDS, so earlier
# results are kept. Reuse the same name to retry pages that failed or to
# add more pages to a run.
RUN_NAME = "2026-10-21_test"

SCRIPT_DIR = Path(__file__).parent
IMAGE_FOLDER = SCRIPT_DIR / "images"
RUN_FOLDER = SCRIPT_DIR / "output" / "runs" / RUN_NAME
OUTPUT_FILE = RUN_FOLDER / "land_directory.csv"
SETTINGS_FILE = RUN_FOLDER / "settings.json"

# Each page's results are saved here as soon as Gemini returns them, and a
# page that already has a file here is not sent again.
PAGES_FOLDER = RUN_FOLDER / "pages"

# Only extract these images, to check the results before a full run.
# Set to [] to extract every image in IMAGE_FOLDER.
TEST_PAGES = ["lc-may86-007.png", "lc-may86-008.png"]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# ----------------------------------------------------------------------------


def build_schema(fields):
    """Turn the codebook into a JSON schema: one page, with a list of entries."""
    entry = {
        "type": "object",
        "properties": {
            name: {"type": "string", "description": description}
            for name, description in fields
        },
        "required": [name for name, _ in fields],
    }
    return {
        "type": "object",
        "properties": {
            "page_number": {
                "type": "string",
                "description": "The printed page number, or empty if none is visible.",
            },
            "entries": {"type": "array", "items": entry},
        },
        "required": ["page_number", "entries"],
    }


def extract_page(client, image_path):
    """Send one image to Gemini and return (parsed data, response)."""
    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    image_part = types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime_type)

    response = client.models.generate_content(
        model=MODEL,
        contents=[image_part, PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",   # answer in JSON only...
            response_json_schema=build_schema(FIELDS),  # ...shaped like this
        ),
    )
    return json.loads(response.text), response


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


def check_entries(entries):
    """Quick sanity checks. These don't prove the data is right,
    but they catch some common problems."""
    for entry in entries:
        if entry["continues_previous"].strip().lower() == "yes":
            continue
        if not entry["community_name"]:
            print(f"    CHECK: a listing has no community name (missed continuation?)")
        elif not entry["street_address"] and not entry["phone"]:
            print(f"    CHECK: {entry['community_name']} has no address and no phone")


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
            for name, _ in FIELDS:
                if name in ("community_name", "section", "continues_previous") or not row[name]:
                    continue
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
    """The settings that decide what Gemini returns. A run keeps one set."""
    return {"model": MODEL, "prompt": PROMPT, "fields": [list(field) for field in FIELDS]}


def start_run_record():
    """Save this run's settings before any page is extracted. If the run
    name was used before with different settings, return False."""
    if SETTINGS_FILE.exists():
        record = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if record["settings"] != run_settings():
            print(f"Run '{RUN_NAME}' was made with different MODEL, PROMPT, or FIELDS.")
            print("Give this run a new RUN_NAME so the earlier results are kept.")
            return False
        return True
    RUN_FOLDER.mkdir(parents=True, exist_ok=True)
    record = {"run_name": RUN_NAME, "settings": run_settings(), "log": []}
    SETTINGS_FILE.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def log_run(images, row_count, cost, failed):
    """Add a line to settings.json for each time the script is run."""
    record = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    record["log"].append({
        "date": datetime.now().isoformat(timespec="seconds"),
        "test_pages": TEST_PAGES,
        "images": [p.name for p in images],
        "failed": failed,
        "rows": row_count,
        "cost_usd": round(cost, 6),
    })
    SETTINGS_FILE.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")


def calculate_cost(input_tokens, output_tokens):
    input_price, output_price = PRICES[MODEL]
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def main():
    load_dotenv(SCRIPT_DIR / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("No API key found. Copy .env.example to .env and add your GEMINI_API_KEY.")
        return

    images = sorted(p for p in IMAGE_FOLDER.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    if TEST_PAGES:
        images = [p for p in images if p.name in TEST_PAGES]
        print(f"TEST RUN: only {len(images)} of the images (see TEST_PAGES)\n")
    if not images:
        print(f"No images found in {IMAGE_FOLDER}")
        return
    if not start_run_record():
        return
    print(f"Run: {RUN_NAME}  (saving to {RUN_FOLDER.relative_to(SCRIPT_DIR)})\n")

    client = genai.Client(api_key=api_key)
    PAGES_FOLDER.mkdir(parents=True, exist_ok=True)
    all_rows = []
    failed = []
    total_cost = 0.0

    for image_path in images:
        saved_page = PAGES_FOLDER / f"{image_path.stem}.json"
        if saved_page.exists():
            print(f"Using saved results for {image_path.name}")
            data = json.loads(saved_page.read_text(encoding="utf-8"))
            response = None
        else:
            print(f"Extracting {image_path.name} ...")
            try:
                data, response = extract_page(client, image_path)
            except Exception as err:
                print(f"  FAILED: {err}\n")
                failed.append(image_path.name)
                continue
            saved_page.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Add the columns that code fills in, not the model
        for entry in data["entries"]:
            entry["page"] = data["page_number"]
            entry["issue"] = issue_from_filename(image_path)
            entry["month"], entry["year"] = month_year_from_issue(entry["issue"])
            entry["source_image"] = image_path.name
            all_rows.append(entry)

        print(f"  Page {data['page_number'] or '?'}: {len(data['entries'])} listings "
              f"(count them on the page -- do they match?)")
        check_entries(data["entries"])

        if response is None:
            print()
            continue
        usage = response.usage_metadata
        output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
        cost = calculate_cost(usage.prompt_token_count or 0, output_tokens)
        total_cost += cost
        print(f"  Tokens: {usage.prompt_token_count:,} in, {output_tokens:,} out   "
              f"Cost: ${cost:.6f}\n")

    print("=" * 40)
    all_rows = merge_continuations(all_rows)
    fill_sections(all_rows)

    # The codebook sets the column order; code-added columns go at the end
    columns = ([name for name, _ in FIELDS if name != "continues_previous"]
               + ["split_across_pages", "page", "month", "year", "issue", "source_image"])
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print("=" * 40)
    print(f"Saved {len(all_rows)} rows to {OUTPUT_FILE.relative_to(SCRIPT_DIR)}")
    print(f"Total cost: ${total_cost:.6f}")
    log_run(images, len(all_rows), total_cost, failed)
    if failed:
        print(f"\n{len(failed)} page(s) failed: {', '.join(failed)}")
        print("Run the script again to retry them; saved pages won't be sent again.")


if __name__ == "__main__":
    main()