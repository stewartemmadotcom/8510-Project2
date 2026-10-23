#!/usr/bin/env python3

import base64
import csv
import io
import json
import mimetypes
import os
import re
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
REFERENCE_FOLDER = SCRIPT_DIR / "reference"   # copied from 8510-Project1/source_data


def read_column(csv_name, column):
    """Read one column of a reference CSV: e.g. every accepted group name."""
    with open(REFERENCE_FOLDER / csv_name, newline="", encoding="utf-8") as f:
        return [row[column] for row in csv.DictReader(f)]


# The controlled vocabularies from the Project 1 database. The model can only
# pick from these lists, because the schema below forces it to.
TYPE_NAMES = read_column("community_types.csv", "type_name")
GROUP_NAMES = read_column("accepted_groups.csv", "group_name")
FOCUS_NAMES = read_column("focuses.csv", "focus_name")
NO_TYPE = "none"   # the model's answer for "no type"; code turns it into a blank

# --- Codebook ---------------------------------------------------------------
# One entry per column: (column name, instructions for the model), plus an
# optional schema when the column is not plain text. The full coding rules are
# in codebook.md; these instructions point to them.
# Change the columns here and the schema and CSV header change with them.

CHOICE = lambda choices: {"type": "string", "enum": choices}
LIST_OF = lambda choices: {"type": "array", "items": {"type": "string", "enum": choices}}

FIELDS = [
("row_kind",
 "'listing' for a directory listing that describes land; 'not_a_listing' for a notice that a community has ended, or a letter from a listed community (see codebook: What counts as a row).",
 CHOICE(["listing", "not_a_listing"])),
("community_name",
 "The community name exactly as printed, usually underlined or in capitals at the start of the listing. If none is given, see codebook: community_name."),
("contact_name",
 "A person or group the mail is addressed to (e.g. after c/o), when it is not the community itself. Otherwise blank."),
("contact_street_address",
 "The mailing street address or box as printed, without c/o or the contact name. Blank if not given."),
("contact_city",
 "The mailing city or town as printed. Blank if not given."),
("contact_state",
 "The mailing state as printed (correct only a plain typo, see codebook). Blank if not given."),
("contact_zip",
 "The mailing zip code as printed. Blank if not given."),
("land_street_address",
 "Where the land itself is, only if the listing says so or the inference is strong (see codebook: Addresses and location). A PO box is never the land."),
("land_city",
 "The city or town where the land is, under the same rule. Blank if not known."),
("land_state",
 "The state where the land is, under the same rule; may come from a vague place like 'southern Oregon'. Blank if not known."),
("land_zip",
 "The zip code where the land is, under the same rule. Blank if not known."),
("land_location_as_stated",
 "The listing's own words for a vague location (e.g. 'southern Oregon', '25 miles southeast of Tucson'). Blank if none."),
("acreage",
 "The acreage as a number only (3/4 acre is 0.75), following codebook: acreage. Blank if not given."),
("num_residents",
 "The number of residents as a whole number, following codebook: num_residents. Blank if the listing does not say."),
("type",
 f"The community type at the date of this listing, following codebook: type. '{NO_TYPE}' for a bare listing or a not_a_listing row.",
 CHOICE(TYPE_NAMES + [NO_TYPE])),
("accepted_groups",
 "Every group the listing welcomes, following codebook: accepted_groups. An empty list if it names no one.",
 LIST_OF(GROUP_NAMES)),
("focuses",
 "What the community was built around, following codebook: focuses. An empty list if none.",
 LIST_OF(FOCUS_NAMES)),
("description",
 "A short summary in your own words, using the controlled vocabulary's terms (see codebook: description)."),
("raw_text",
 "The full listing word for word, never shortened, following codebook: raw_text."),
("notes",
 "Explain every judgment call, quoting the words it rests on (see codebook: notes)."),
("section",
 "The nearest centered section heading above this listing on this page, exactly as printed. Blank if none on this page."),
("continues_previous",
 "'yes' only if this is the first text on the page and it is the end of a listing that began on the previous page (it does not start with a community name). Leave community_name blank for it. Otherwise blank."),
]

LIST_FIELDS = [field[0] for field in FIELDS if len(field) > 2 and field[2]["type"] == "array"]


def vocabulary_text():
    """The controlled vocabularies, with their definitions, for the prompt."""
    lines = []
    for title, csv_name, name_col in [("Community types", "community_types.csv", "type_name"),
                                      ("Accepted groups", "accepted_groups.csv", "group_name"),
                                      ("Focuses", "focuses.csv", "focus_name")]:
        with open(REFERENCE_FOLDER / csv_name, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        lines.append(f"## {title}")
        lines += [f"- {r[name_col]}" + (f": {r['description']}" if r.get("description") else "")
                  for r in rows]
        lines.append("")
    return "\n".join(lines)


CODEBOOK = (SCRIPT_DIR / "codebook.md").read_text(encoding="utf-8")

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
MODEL = "claude-sonnet-5-5"

# How hard a Claude model thinks before answering: low, medium, high, xhigh, max.
# Higher costs more. (Gemini ignores this.)
CLAUDE_EFFORT = "high"

# Paid-tier prices in US dollars per 1 million tokens: (input, output).
# Check https://ai.google.dev/gemini-api/docs/pricing and
# https://platform.claude.com/docs/en/about-claude/pricing -- prices change.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "gemini-4-argon": (2.00, 10.00),    # through Nov 30, 2026; doubles Dec 1, 2026
    "gemini-3.8-flash": (0.75, 3.75),   # through Dec 31, 2026; doubles Jan 1, 2027
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
}

# Each run saves everything to its own folder: output/runs/<RUN_NAME>/
# Use a new name whenever you change MODEL, PROMPT, or FIELDS, so earlier
# results are kept. Reuse the same name to retry pages that failed or to
# add more pages to a run.
RUN_NAME = "2026-10-23_codebook-v4_sonnet-5.5"

IMAGE_FOLDER = SCRIPT_DIR / "images"
RUN_FOLDER = SCRIPT_DIR / "output" / "runs" / RUN_NAME
OUTPUT_FILE = RUN_FOLDER / "land_directory.csv"
SETTINGS_FILE = RUN_FOLDER / "settings.json"

# Each page's results are saved here as soon as Gemini returns them, and a
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


def build_schema(fields):
    """Turn the codebook into a JSON schema: one page, with a list of entries."""
    properties = {}
    for field in fields:
        name, description = field[0], field[1]
        schema = dict(field[2]) if len(field) > 2 else {"type": "string"}
        schema["description"] = description
        properties[name] = schema
    entry = {
        "type": "object",
        "properties": properties,
        "required": [field[0] for field in fields],
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


def uses_claude():
    return MODEL.startswith("claude-")


def closed_schema(schema):
    """Claude's structured outputs need every object in the schema to say
    "additionalProperties": false (no fields beyond the ones listed)."""
    if isinstance(schema, dict):
        schema = {key: closed_schema(value) for key, value in schema.items()}
        if schema.get("type") == "object":
            schema["additionalProperties"] = False
    elif isinstance(schema, list):
        schema = [closed_schema(item) for item in schema]
    return schema


# Claude reads images up to 2576 pixels on the long edge; larger page scans
# are shrunk to that size before sending
CLAUDE_MAX_IMAGE_EDGE = 2576


def image_for_claude(image_path):
    """The page image as base64 JPEG, shrunk to fit Claude's size limit.
    (A resized PNG of a page is about 10 MB, over Claude's 5 MB per image;
    a high-quality JPEG keeps the text sharp at about a tenth of that.)"""
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        image.thumbnail((CLAUDE_MAX_IMAGE_EDGE, CLAUDE_MAX_IMAGE_EDGE))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def extract_page(client, image_path, source_text):
    """Send one image to the model and return (parsed data, input tokens,
    output tokens)."""
    if uses_claude():
        return extract_page_claude(client, image_path, source_text)
    return extract_page_gemini(client, image_path, source_text)


def extract_page_claude(client, image_path, source_text):
    """Send one image to Claude and return (parsed data, input tokens,
    output tokens)."""
    # Streaming, because a full page of listings can be a long answer
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        output_config={
            "effort": CLAUDE_EFFORT,
            # answer in JSON shaped like the codebook
            "format": {"type": "json_schema", "schema": closed_schema(build_schema(FIELDS))},
        },
        # If Claude's safety checks decline a page, the API retries it on
        # another Claude model inside the same request
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                             "data": image_for_claude(image_path)}},
                {"type": "text", "text": PROMPT.replace("{source}", source_text)},
            ],
        }],
    ) as stream:
        response = stream.get_final_message()

    # Say why an answer is unusable, like the Gemini finish reason
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else "none given"
        raise ValueError(f"Claude declined the page (refusal; category: {category})")
    if response.stop_reason == "max_tokens":
        raise ValueError("Claude's answer was cut off (max_tokens)")
    text = next((block.text for block in response.content if block.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Claude's answer was not complete JSON (stop reason: "
                         f"{response.stop_reason}; answer ended with: ...{text[-80:]!r})")
    if response.model != MODEL:
        print(f"  NOTE: answered by {response.model} (fallback); cost below uses {MODEL}'s prices")
    usage = response.usage
    # output_tokens includes Claude's thinking, which is billed as output
    return data, usage.input_tokens, usage.output_tokens


def extract_page_gemini(client, image_path, source_text):
    """Send one image to Gemini and return (parsed data, input tokens,
    output tokens)."""
    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    image_part = types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime_type)

    response = client.models.generate_content(
        model=MODEL,
        contents=[image_part, PROMPT.replace("{source}", source_text)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",   # answer in JSON only...
            response_json_schema=build_schema(FIELDS),  # ...shaped like this
        ),
    )

    # Say why an answer is unusable: the finish reason shows whether Gemini
    # ran out of room (MAX_TOKENS), refused to copy text (RECITATION), etc.
    candidate = response.candidates[0] if response.candidates else None
    finish = candidate.finish_reason.name if candidate and candidate.finish_reason else "none given"
    if not response.text:
        raise ValueError(f"Gemini returned no text (finish reason: {finish}; "
                         f"feedback: {response.prompt_feedback})")
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError(f"Gemini's answer was not complete JSON (finish reason: {finish}; "
                         f"answer ended with: ...{response.text[-80:]!r})")
    usage = response.usage_metadata
    # Gemini bills its thinking tokens as output too
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return data, usage.prompt_token_count or 0, output_tokens


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


def load_sources():
    """Code looks up each issue in reference/sources.csv (the Project 1
    sources table) by its file name: 'lc-december82.pdf' -> 'december82'."""
    sources = {}
    with open(REFERENCE_FOLDER / "sources.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            issue = Path(row["file_name"]).stem.removeprefix("lc-")
            sources[issue] = row
    return sources


def source_columns(issue, sources):
    """The source columns for one issue. An issue missing from sources.csv
    gets its month and year from the file name, and no source_id."""
    if issue in sources:
        row = sources[issue]
        return {"source_id": row["source_id"], "publication": row["publication"],
                "year_recorded": row["year"], "month_recorded": row["month"]}
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


def ends_complete(text):
    """Does the text end like a finished sentence? ('...on the land.' does;
    '...Unemployment in this area' does not. A listing may also end with its
    phone number or zip code.)"""
    text = text.strip()
    return text.endswith((".", "!", "?", ")", '"', "'")) or text[-1:].isdigit()


def check_cut_off(rows):
    """After merging, flag listings whose raw_text stops mid-sentence: the
    model may have stopped copying early."""
    for row in rows:
        if row["raw_text"] and not ends_complete(row["raw_text"]):
            print(f"CHECK: raw_text of {row['community_name'] or '(no name)'} "
                  f"({row['source_image']}) ends mid-sentence: "
                  f"'...{row['raw_text'].strip()[-40:]}'")


def apply_code_rules(rows):
    """Rules from the codebook that need no judgment, so code applies them
    the same way every time."""
    for row in rows:
        # The model answers 'none' for no type, because the schema needs a choice
        if row["type"] == NO_TYPE:
            row["type"] = ""
        # In LC's questionnaire directories (1982 on), lesbians are never on the
        # "We welcome:" list because the whole directory is for lesbians, so
        # Lesbian women is coded for every listing that welcomes anyone
        if (row["year_recorded"] >= "1982" and row["accepted_groups"]
                and "Lesbian women" not in row["accepted_groups"]):
            row["accepted_groups"].insert(0, "Lesbian women")


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
    key_name = "ANTHROPIC_API_KEY" if uses_claude() else "GEMINI_API_KEY"
    api_key = os.getenv(key_name)
    if not api_key or api_key == "your-api-key-here":
        print(f"No API key found. Add {key_name}=... to the .env file in this folder.")
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

    if uses_claude():
        client = anthropic.Anthropic(api_key=api_key)
    else:
        client = genai.Client(api_key=api_key)
    sources = load_sources()
    PAGES_FOLDER.mkdir(parents=True, exist_ok=True)
    all_rows = []
    failed = []
    total_cost = 0.0

    for image_path in images:
        issue = issue_from_filename(image_path)
        source = source_columns(issue, sources)
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
        cost = calculate_cost(input_tokens, output_tokens)
        total_cost += cost
        print(f"  Tokens: {input_tokens:,} in, {output_tokens:,} out   "
              f"Cost: ${cost:.6f}\n")

    print("=" * 40)
    all_rows = merge_continuations(all_rows)
    check_cut_off(all_rows)
    fill_sections(all_rows)
    apply_code_rules(all_rows)

    # The codebook sets the column order; code-added columns go at the end
    columns = ([field[0] for field in FIELDS if field[0] != "continues_previous"]
               + ["split_across_pages", "page", "source_id", "publication",
                  "year_recorded", "month_recorded", "issue", "source_image"])
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            # A list of groups or focuses becomes one cell: "Lesbian women; Girl children"
            writer.writerow({k: "; ".join(v) if k in LIST_FIELDS else v for k, v in row.items()})

    print("=" * 40)
    print(f"Saved {len(all_rows)} rows to {OUTPUT_FILE.relative_to(SCRIPT_DIR)}")
    print(f"Total cost: ${total_cost:.6f}")
    log_run(images, len(all_rows), total_cost, failed)
    if failed:
        print(f"\n{len(failed)} page(s) failed:")
        for failure in failed:
            print(f"  {failure}")
        print("Run the script again to retry them; saved pages won't be sent again.")


if __name__ == "__main__":
    main()