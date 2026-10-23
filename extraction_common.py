"""Code shared by 01_directory_to_csv.py (Lesbian Connection page images) and
03_maize_to_csv.py (Maize issue texts): the codebook columns, the controlled
vocabularies, the calls to Gemini and Claude, costs, checks, and the run
folder's settings log.
"""

import base64
import csv
import io
import json
import mimetypes
import os
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
# pick from these lists, because the schema forces it to.
TYPE_NAMES = read_column("community_types.csv", "type_name")
GROUP_NAMES = read_column("accepted_groups.csv", "group_name")
FOCUS_NAMES = read_column("focuses.csv", "focus_name")
NO_TYPE = "none"   # the model's answer for "no type"; code turns it into a blank

CHOICE = lambda choices: {"type": "string", "enum": choices}
LIST_OF = lambda choices: {"type": "array", "items": {"type": "string", "enum": choices}}

# --- Codebook columns shared by both sources ----------------------------------
# One entry per column: (column name, instructions for the model), plus an
# optional schema when the column is not plain text. Each script puts its own
# row_kind and section columns around these. The full coding rules are in
# codebook.md (and codebook_maize.md for Maize).

COMMON_FIELDS = [
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
]


def list_fields(fields):
    """The columns whose answer is a list (accepted_groups, focuses)."""
    return [field[0] for field in fields if len(field) > 2 and field[2]["type"] == "array"]


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


def calculate_cost(model, input_tokens, output_tokens):
    input_price, output_price = PRICES[model]
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


# --- Schema -----------------------------------------------------------------

def build_schema(fields, page_number=True):
    """Turn the codebook into a JSON schema: a list of entries, plus the
    printed page number when the model reads one page at a time."""
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
    top = {"entries": {"type": "array", "items": entry}}
    if page_number:
        top = {"page_number": {
                   "type": "string",
                   "description": "The printed page number, or empty if none is visible.",
               }, **top}
    return {"type": "object", "properties": top, "required": list(top)}


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


# --- Calling the model ------------------------------------------------------

def uses_claude(model):
    """A model name starting with "claude-" goes to Anthropic; anything else to Gemini."""
    return model.startswith("claude-")


def make_client(model):
    """A client for the model's provider, with the key from .env; None (and
    a message) if the key is missing."""
    load_dotenv(SCRIPT_DIR / ".env")
    key_name = "ANTHROPIC_API_KEY" if uses_claude(model) else "GEMINI_API_KEY"
    api_key = os.getenv(key_name)
    if not api_key or api_key == "your-api-key-here":
        print(f"No API key found. Add {key_name}=... to the .env file in this folder.")
        return None
    if uses_claude(model):
        return anthropic.Anthropic(api_key=api_key)
    return genai.Client(api_key=api_key)


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


def call_model(client, model, prompt, schema, image_path=None, claude_effort="high"):
    """Send the prompt (and a page image, if given) to the model and return
    (parsed data, input tokens, output tokens)."""
    if uses_claude(model):
        return call_claude(client, model, prompt, schema, image_path, claude_effort)
    return call_gemini(client, model, prompt, schema, image_path)


def call_claude(client, model, prompt, schema, image_path, effort):
    content = []
    if image_path:
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                    "data": image_for_claude(image_path)}})
    content.append({"type": "text", "text": prompt})
    # Streaming, because a full page or issue of listings can be a long answer
    with client.beta.messages.stream(
        model=model,
        max_tokens=64000,
        output_config={
            "effort": effort,
            # answer in JSON shaped like the codebook
            "format": {"type": "json_schema", "schema": closed_schema(schema)},
        },
        # If Claude's safety checks decline a request, the API retries it on
        # another Claude model inside the same request
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": content}],
    ) as stream:
        response = stream.get_final_message()

    # Say why an answer is unusable, like the Gemini finish reason
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else "none given"
        raise ValueError(f"Claude declined (refusal; category: {category})")
    if response.stop_reason == "max_tokens":
        raise ValueError("Claude's answer was cut off (max_tokens)")
    text = next((block.text for block in response.content if block.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Claude's answer was not complete JSON (stop reason: "
                         f"{response.stop_reason}; answer ended with: ...{text[-80:]!r})")
    if response.model != model:
        print(f"  NOTE: answered by {response.model} (fallback); cost below uses {model}'s prices")
    usage = response.usage
    # output_tokens includes Claude's thinking, which is billed as output
    return data, usage.input_tokens, usage.output_tokens


def call_gemini(client, model, prompt, schema, image_path):
    contents = []
    if image_path:
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        contents.append(types.Part.from_bytes(data=image_path.read_bytes(), mime_type=mime_type))
    contents.append(prompt)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",   # answer in JSON only...
            response_json_schema=schema,              # ...shaped like this
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


# --- Sources ----------------------------------------------------------------

def load_sources(key_for_row):
    """reference/sources.csv (the Project 1 sources table), keyed by whatever
    key_for_row returns for each row (e.g. 'december82' for LC)."""
    with open(REFERENCE_FOLDER / "sources.csv", newline="", encoding="utf-8") as f:
        return {key_for_row(row): row for row in csv.DictReader(f)}


def source_columns(row):
    """The source columns every output row gets, from one sources.csv row."""
    return {"source_id": row["source_id"], "publication": row["publication"],
            "year_recorded": row["year"], "month_recorded": row["month"]}


# --- Checks and rules that need no judgment ---------------------------------

def ends_complete(text):
    """Does the text end like a finished sentence? ('...on the land.' does;
    '...Unemployment in this area' does not. A listing may also end with its
    phone number or zip code.)"""
    text = text.strip()
    return text.endswith((".", "!", "?", ")", '"', "'")) or text[-1:].isdigit()


def check_cut_off(rows):
    """Flag rows whose raw_text stops mid-sentence: the model may have
    stopped copying early."""
    for row in rows:
        if row["raw_text"] and not ends_complete(row["raw_text"]):
            print(f"CHECK: raw_text of {row['community_name'] or '(no name)'} "
                  f"({row['source_image']}) ends mid-sentence: "
                  f"'...{row['raw_text'].strip()[-40:]}'")


def apply_code_rules(rows, adds_lesbian_women=None):
    """Rules from the codebook that need no judgment, so code applies them
    the same way every time. adds_lesbian_women(row) says whether a row that
    welcomes anyone gets Lesbian women added (the rule differs by source)."""
    for row in rows:
        # The model answers 'none' for no type, because the schema needs a choice
        if row["type"] == NO_TYPE:
            row["type"] = ""
        if (adds_lesbian_women and adds_lesbian_women(row) and row["accepted_groups"]
                and "Lesbian women" not in row["accepted_groups"]):
            row["accepted_groups"].insert(0, "Lesbian women")


# --- The run folder ---------------------------------------------------------

def start_run_record(run_name, run_folder, settings_file, settings):
    """Save a run's settings before anything is sent. If the run name was
    used before with different settings, return False."""
    if settings_file.exists():
        record = json.loads(settings_file.read_text(encoding="utf-8"))
        if record["settings"] != settings:
            print(f"Run '{run_name}' was made with different MODEL, PROMPT, or FIELDS.")
            print("Give this run a new RUN_NAME so the earlier results are kept.")
            return False
        return True
    run_folder.mkdir(parents=True, exist_ok=True)
    record = {"run_name": run_name, "settings": settings, "log": []}
    settings_file.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def log_run(settings_file, entry):
    """Add a line (a dict) to settings.json for each time a script is run;
    the date is added here."""
    record = json.loads(settings_file.read_text(encoding="utf-8"))
    record["log"].append({"date": datetime.now().isoformat(timespec="seconds"), **entry})
    settings_file.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")


def write_rows(output_file, rows, columns, list_columns):
    """Save the rows as a CSV; a list of groups or focuses becomes one cell:
    "Lesbian women; Girl children"."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "; ".join(v) if k in list_columns else v for k, v in row.items()})
