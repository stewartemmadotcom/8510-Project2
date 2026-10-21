#!/usr/bin/env python3

import csv
import json
import mimetypes
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Codebook ---------------------------------------------------------------
# One entry per column: (column name, instructions for the model).
# Change the columns here and the schema and CSV header change with them.

FIELDS = [
("response_mark", 
 "At the beginning of a listing, if there is a question mark or two question marks, add them to this field. If there are none, leave blank."),
("names", 
 "Transcribe the names exactly as written. Leave any question marks out of this field. (e.g. Dorothy Colless, Jude Major, Dixie & Deb)"),
("care_of", 
 "If there is a person or organization, such as a farm, land group, business, or title printed in the listing after c/o or after the name, include it exactly as printed. (e.g. c/o Whypperwillow Wyminz Land) If not, leave empty. If only an address follows c/o, leave this field empty."),
("street_address", 
 "Transcribe the street address exactly as printed. If it is not included, leave blank. If it is preceded by c/o, leave c/o out."),
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
("notes",
 "Any additional information provided anywhere in the listing should be transcribed exactly as printed. Leave empty if there is no additional information.")
]

PROMPT = """This image is a page from the May 1986 
periodical Lesbian Connection's Contact Dyke directory. Extract every listing on the page as one row, in the order they appear.
A listing that continues onto an indented second line is the same listing.
Skip the intro text and the numbered rules on page 9, the underlined STATE/COUNTRY headings, and the "CD Directory cont" running header. 
Ignore faint text showing through the back of the page.

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

SCRIPT_DIR = Path(__file__).parent
IMAGE_FOLDER = SCRIPT_DIR / "images" / "contacts"
OUTPUT_FILE = SCRIPT_DIR / "output" / "contacts.csv"

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


# LC's own explanation of the marks, from the Directory intro (p. 9)
RESPONSE_STATUS = {
    "?": "didn't answer our letter",
    "??": "written twice, hasn't responded",
    "": "confirmed",
}


def response_status(mark):
    """Code, not the model, translates '?' and '??' into LC's wording."""
    return RESPONSE_STATUS.get(mark.strip(), "")


def issue_from_filename(image_path):
    """Code pulls the issue out of the filename: 'lc-may86-011.png' -> 'may86'."""
    match = re.match(r"lc-([a-z]+\d{2})-", image_path.name)
    return match.group(1) if match else ""


def check_entries(entries):
    """Quick sanity checks. These don't prove the data is right,
    but they catch some common problems."""
    for entry in entries:
        if not entry["street_address"] and not entry["phone"]:
            print(f"    CHECK: {entry['names']} has no address and no phone")


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
    if not images:
        print(f"No images found in {IMAGE_FOLDER}")
        return

    client = genai.Client(api_key=api_key)
    all_rows = []
    total_cost = 0.0

    for image_path in images:
        print(f"Extracting {image_path.name} ...")
        data, response = extract_page(client, image_path)

        # Add the columns that code fills in, not the model
        for entry in data["entries"]:
            entry["response_status"] = response_status(entry["response_mark"])
            entry["page"] = data["page_number"]
            entry["issue"] = issue_from_filename(image_path)
            entry["source_image"] = image_path.name
            all_rows.append(entry)

        usage = response.usage_metadata
        output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
        cost = calculate_cost(usage.prompt_token_count or 0, output_tokens)
        total_cost += cost

        print(f"  Page {data['page_number'] or '?'}: {len(data['entries'])} listings "
              f"(count them on the page -- do they match?)")
        check_entries(data["entries"])
        print(f"  Tokens: {usage.prompt_token_count:,} in, {output_tokens:,} out   "
              f"Cost: ${cost:.6f}\n")

    # The codebook sets the column order; code-added columns go at the end
    columns = [name for name, _ in FIELDS] + ["response_status", "page", "issue", "source_image"]
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print("=" * 40)
    print(f"Saved {len(all_rows)} rows to {OUTPUT_FILE.relative_to(SCRIPT_DIR)}")
    print(f"Total cost: ${total_cost:.6f}")


if __name__ == "__main__":
    main()