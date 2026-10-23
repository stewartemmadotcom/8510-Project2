#!/usr/bin/env python3
"""Compare one extraction run against the hand-checked rows from Project 1.

The model's rows come from output/runs/<RUN_NAME>/land_directory.csv.
The hand-checked rows come from the Project 1 database's source CSVs, which
this script only reads. Both are put into the same flat sheet, paired up
listing by listing, and scored field by field.

Outputs, saved in the run's folder:
  comparison_summary.txt   accuracy for each field, matched/missed/extra counts
  comparison_details.csv   one row per disagreement
  review_side_by_side.csv  description and notes side by side, to read by eye

Run it with:   venv/bin/python 02_compare_to_handchecked.py
Self-test:     venv/bin/python 02_compare_to_handchecked.py --self-test
  (writes the hand-checked rows out as if they were model output, compares
  them to themselves, and checks that everything scores 100%)
"""

import csv
import json
import re
import statistics
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

# --- Settings ---------------------------------------------------------------

# Which run to compare: the folder name in output/runs/
# (keep this the same as RUN_NAME in 01_directory_to_csv.py)
RUN_NAME = "2026-10-22_codebook-v2_flash-lite-3.5"

SCRIPT_DIR = Path(__file__).parent
RUN_FOLDER = SCRIPT_DIR / "output" / "runs" / RUN_NAME

# Project 1's hand-checked data (read only, never changed here)
HAND_FOLDER = Path.home() / "Desktop" / "8510-Project1" / "source_data"

# Two rows are paired only if their names (or the start of their raw_text)
# are at least this similar, from 0 (nothing alike) to 1 (identical)
MATCH_THRESHOLD = 0.7

# raw_text counts as a match at this similarity or above
RAW_TEXT_THRESHOLD = 0.98

# How many characters from the start of raw_text to compare when pairing
RAW_START_LENGTH = 60

# The flat sheet's columns, in the same order as land_directory.csv
COLUMNS = [
    "row_kind", "community_name",
    "contact_name", "contact_street_address", "contact_city", "contact_state", "contact_zip",
    "land_street_address", "land_city", "land_state", "land_zip", "land_location_as_stated",
    "acreage", "num_residents", "type", "accepted_groups", "focuses",
    "description", "raw_text", "notes", "section", "split_across_pages", "page",
    "source_id", "publication", "year_recorded", "month_recorded", "issue", "source_image",
]

# How each scored field is compared (description and notes are not scored:
# they are written in the coder's own words, so they go to the review file)
TEXT_FIELDS = [   # same text after trimming spaces and ignoring case
    "row_kind", "type",
    "contact_name", "contact_street_address", "contact_city", "contact_state", "contact_zip",
    "land_street_address", "land_city", "land_state", "land_zip", "land_location_as_stated",
]
NUMBER_FIELDS = ["page", "acreage", "num_residents"]   # same number; blank must equal blank
LIST_FIELDS = ["accepted_groups", "focuses"]            # same set of names
SCORED_FIELDS = TEXT_FIELDS + NUMBER_FIELDS + LIST_FIELDS + ["raw_text"]

# ----------------------------------------------------------------------------


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def issue_from_file_name(file_name):
    """'primary/lesbian-connection/lc-december82.pdf' -> 'december82'."""
    stem = Path(file_name).stem
    return stem.removeprefix("lc-")


def issue_from_image(image_name):
    """'lc-december82-023.png' -> 'december82' (used if the issue column is blank)."""
    match = re.match(r"lc-([a-z]+\d{2})-", image_name)
    return match.group(1) if match else ""


def is_out_of_scope(row):
    """Classified ads aren't part of the directory pages, so they aren't scored."""
    return row["notes"].startswith("From a classified ad")


# --- Step 1: the hand-checked rows as a flat sheet --------------------------

def load_hand_rows():
    """Join Project 1's tables into one flat row per observation."""
    communities = {r["community_id"]: r for r in read_csv(HAND_FOLDER / "communities.csv")}
    types = {r["type_id"]: r["type_name"] for r in read_csv(HAND_FOLDER / "community_types.csv")}
    groups = {r["group_id"]: r["group_name"] for r in read_csv(HAND_FOLDER / "accepted_groups.csv")}
    focuses = {r["focus_id"]: r["focus_name"] for r in read_csv(HAND_FOLDER / "focuses.csv")}
    sources = {r["source_id"]: r for r in read_csv(HAND_FOLDER / "sources.csv")}

    # The junction tables: which groups and focuses each observation has
    groups_for = {}
    for link in read_csv(HAND_FOLDER / "observation_accepted_groups.csv"):
        groups_for.setdefault(link["observation_id"], []).append(groups[link["group_id"]])
    focuses_for = {}
    for link in read_csv(HAND_FOLDER / "observation_focuses.csv"):
        focuses_for.setdefault(link["observation_id"], []).append(focuses[link["focus_id"]])

    rows = []
    for obs in read_csv(HAND_FOLDER / "community_observations.csv"):
        community = communities[obs["community_id"]]
        source = sources[obs["source_id"]]
        # The community's name followed by its alternate names, all used for pairing
        names = [community["name"]] + [n for n in community["alternate_names"].split("; ") if n]
        row = {
            "observation_id": obs["observation_id"],   # kept so rows can be traced back
            "row_kind": "not_a_listing" if obs["notes"].startswith("Not a listing") else "listing",
            "community_name": "; ".join(names),
            "type": types.get(obs["type_id"], ""),
            "accepted_groups": "; ".join(groups_for.get(obs["observation_id"], [])),
            "focuses": "; ".join(focuses_for.get(obs["observation_id"], [])),
            "section": "",
            "split_across_pages": "",
            "publication": source["publication"],
            "issue": issue_from_file_name(source["file_name"]),
            "source_image": "",
        }
        # These columns are named the same in both sheets
        for name in ["contact_name", "contact_street_address", "contact_city", "contact_state",
                     "contact_zip", "land_street_address", "land_city", "land_state", "land_zip",
                     "land_location_as_stated", "acreage", "num_residents", "description",
                     "raw_text", "notes", "page", "source_id", "year_recorded", "month_recorded"]:
            row[name] = obs[name]
        rows.append(row)
    return rows


def load_model_rows(csv_path):
    """Read the model's sheet. Missing columns are treated as blank."""
    rows = read_csv(csv_path)
    for row in rows:
        for name in COLUMNS:
            row[name] = (row.get(name) or "").strip()
        # Older runs saved the page as printed, e.g. "-13-": keep only the digits
        row["page"] = re.sub(r"\D", "", row["page"])
        if not row["issue"]:
            row["issue"] = issue_from_image(row["source_image"].split("; ")[0])
    return rows


# --- Step 3: pairing rows ---------------------------------------------------

def simplify(text):
    """Lowercase, drop punctuation and a leading 'the', squeeze spaces."""
    text = re.sub(r"[^\w&\s]", " ", text.lower())
    text = " ".join(text.split())
    return text.removeprefix("the ")


def similarity(a, b):
    """0 to 1: how alike two strings are (difflib's ratio)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def names_of(row):
    """All the names a row goes by, simplified."""
    return [simplify(n) for n in row["community_name"].split("; ") if simplify(n)]


def first_words(text, how_many):
    return " ".join(simplify(text).split()[:how_many])


def pair_scores(hand, model):
    """How likely two rows are the same listing. Returns
    (best score, raw_text start score, name score) so ties can be broken."""
    # Name against name, trying every alternate name
    name_score = max([similarity(h, m) for h in names_of(hand) for m in names_of(model)] + [0])

    # A name against the first words of the other row's raw_text. This catches
    # hand names that are fallbacks the listing never prints (e.g. "Four Women")
    for name in names_of(hand):
        name_score = max(name_score, similarity(name, first_words(model["raw_text"], len(name.split()))))
    for name in names_of(model):
        name_score = max(name_score, similarity(name, first_words(hand["raw_text"], len(name.split()))))

    # The start of each raw_text against the other
    raw_score = similarity(simplify(hand["raw_text"])[:RAW_START_LENGTH],
                           simplify(model["raw_text"])[:RAW_START_LENGTH])
    return max(name_score, raw_score), raw_score, name_score


def pair_rows(hand_rows, model_rows):
    """Within each issue, take the most similar pair first, then the next most
    similar of the rows still left, and so on, down to MATCH_THRESHOLD.
    Returns (pairs, hand rows left over, model rows left over)."""
    candidates = []
    for h, hand in enumerate(hand_rows):
        for m, model in enumerate(model_rows):
            if hand["issue"] != model["issue"]:
                continue
            score, raw_score, name_score = pair_scores(hand, model)
            if score >= MATCH_THRESHOLD:
                same_page = hand["page"] == model["page"]
                same_address = sum(clean(hand[f]) == clean(model[f]) for f in TEXT_FIELDS)
                candidates.append(((score, raw_score, name_score, same_page, same_address), h, m))

    # Several rows can share a name (OWLT twice in one issue) or a raw_text
    # (two land trusts in one paragraph), so ties are broken by the raw_text
    # start, then the name, then being on the same page, then how many of the
    # address and other text fields agree
    candidates.sort(key=lambda c: c[0], reverse=True)
    used_hand, used_model, pairs = set(), set(), []
    for _, h, m in candidates:
        if h not in used_hand and m not in used_model:
            used_hand.add(h)
            used_model.add(m)
            pairs.append((hand_rows[h], model_rows[m]))

    hand_left = [r for i, r in enumerate(hand_rows) if i not in used_hand]
    model_left = [r for i, r in enumerate(model_rows) if i not in used_model]
    return pairs, hand_left, model_left


# --- Step 4: scoring --------------------------------------------------------

def clean(text):
    return " ".join(text.split()).casefold()


def as_number(text):
    """'145' -> 145.0, '' -> None, anything unreadable stays as text."""
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return text


def as_set(text):
    return {clean(item) for item in text.split(";") if clean(item)}


def compare_field(field, hand_value, model_value):
    """Returns (agrees?, a short explanation for lists and raw_text)."""
    if field in TEXT_FIELDS:
        return clean(hand_value) == clean(model_value), ""
    if field in NUMBER_FIELDS:
        return as_number(hand_value) == as_number(model_value), ""
    if field in LIST_FIELDS:
        hand_set, model_set = as_set(hand_value), as_set(model_value)
        missing = sorted(hand_set - model_set)
        extra = sorted(model_set - hand_set)
        explain = []
        if missing:
            explain.append("model missed: " + "; ".join(missing))
        if extra:
            explain.append("model added: " + "; ".join(extra))
        return hand_set == model_set, " | ".join(explain)
    if field == "raw_text":
        ratio = similarity(" ".join(hand_value.split()), " ".join(model_value.split()))
        if not hand_value and not model_value:
            ratio = 1.0
        return ratio >= RAW_TEXT_THRESHOLD, f"similarity {ratio:.3f}"
    raise ValueError(f"No comparison rule for {field}")


def raw_text_ratio(hand, model):
    if not hand["raw_text"] and not model["raw_text"]:
        return 1.0
    return similarity(" ".join(hand["raw_text"].split()), " ".join(model["raw_text"].split()))


def first_name(row):
    return row["community_name"].split("; ")[0]


# --- The comparison itself --------------------------------------------------

def compare(hand_rows, model_rows):
    """Do steps 2 to 4. Returns everything the reports need."""
    # Step 2: scope. Only the (issue, page) pairs that were hand-checked
    checked_pages = {(r["issue"], str(r["page"])) for r in hand_rows}
    model_in_scope = [r for r in model_rows if (r["issue"], str(r["page"])) in checked_pages]
    model_outside = len(model_rows) - len(model_in_scope)

    # Classified-ad rows still take part in pairing, so the model's copy of a
    # classified ad isn't counted as "extra", but they are never scored
    pairs, hand_left, model_left = pair_rows(hand_rows, model_in_scope)
    scored_pairs = [(h, m) for h, m in pairs if not is_out_of_scope(h)]
    out_of_scope_pairs = [(h, m) for h, m in pairs if is_out_of_scope(h)]
    missed = [h for h in hand_left if not is_out_of_scope(h)]
    out_of_scope = [h for h in hand_rows if is_out_of_scope(h)]

    # Step 4: score each field on the matched pairs
    agree_counts = {field: 0 for field in SCORED_FIELDS}
    details = []
    for hand, model in scored_pairs:
        for field in SCORED_FIELDS:
            agrees, explain = compare_field(field, hand[field], model[field])
            if agrees:
                agree_counts[field] += 1
            else:
                details.append({
                    "issue": hand["issue"], "page": hand["page"],
                    "community": first_name(hand), "field": field,
                    "hand_value": hand[field], "model_value": model[field],
                    "explanation": explain,
                })
    # Rows only one side has go in the details too, so nothing is hidden
    for hand in missed:
        details.append({"issue": hand["issue"], "page": hand["page"], "community": first_name(hand),
                        "field": "MISSED ROW (only in hand-checked data)",
                        "hand_value": hand["raw_text"], "model_value": "", "explanation": ""})
    for model in model_left:
        details.append({"issue": model["issue"], "page": model["page"],
                        "community": model["community_name"],
                        "field": "EXTRA ROW (only in model output)",
                        "hand_value": "", "model_value": model["raw_text"], "explanation": ""})

    ratios = [raw_text_ratio(h, m) for h, m in scored_pairs]
    return {
        "hand_in_scope": len(hand_rows) - len(out_of_scope),
        "model_in_scope": len(model_in_scope),
        "model_outside": model_outside,
        "scored_pairs": scored_pairs,
        "out_of_scope_pairs": out_of_scope_pairs,
        "missed": missed,
        "extra": model_left,
        "out_of_scope": out_of_scope,
        "agree_counts": agree_counts,
        "raw_text_mean": statistics.mean(ratios) if ratios else 0.0,
        "details": details,
    }


# --- Step 5: reports --------------------------------------------------------

def failed_pages(run_folder):
    """Pages listed as failed in the latest entry of the run's settings.json
    log (each run retries earlier failures, so the latest entry is current)."""
    settings_file = run_folder / "settings.json"
    if not settings_file.exists():
        return []
    log = json.loads(settings_file.read_text(encoding="utf-8")).get("log", [])
    return log[-1].get("failed", []) if log else []


def summary_text(result, run_name, failed):
    pairs = result["scored_pairs"]
    lines = [
        f"Comparison of run '{run_name}' with the Project 1 hand-checked rows",
        "",
        f"Hand-checked rows in scope:   {result['hand_in_scope']}",
        f"Model rows on checked pages:  {result['model_in_scope']}"
        f"  ({result['model_outside']} model rows on other pages were left out)",
        f"Matched pairs (scored):       {len(pairs)}",
        f"Missed (hand-checked only):   {len(result['missed'])}",
        f"Extra (model only):           {len(result['extra'])}",
        "",
        "Field accuracy on matched pairs:",
    ]
    for field in SCORED_FIELDS:
        count = result["agree_counts"][field]
        percent = 100 * count / len(pairs) if pairs else 0
        lines.append(f"  {field:<26} {percent:6.1f}%  ({count}/{len(pairs)})")
    lines.append(f"  raw_text mean similarity:  {result['raw_text_mean']:.3f}"
                 f"  (a match is {RAW_TEXT_THRESHOLD} or above)")

    lines += ["", "Missed rows (only in hand-checked data):"]
    lines += [f"  {r['issue']} p.{r['page']}: {first_name(r)}" for r in result["missed"]] or ["  none"]
    lines += ["", "Extra rows (only in model output):"]
    lines += [f"  {r['issue']} p.{r['page']}: {r['community_name'] or '(no name)'}"
              for r in result["extra"]] or ["  none"]

    lines += ["", "Out of scope, not scored (classified ads):"]
    for row in result["out_of_scope"]:
        paired = any(h is row for h, _ in result["out_of_scope_pairs"])
        found = "  [the model also extracted it]" if paired else ""
        lines.append(f"  {row['issue']} p.{row['page']}: {first_name(row)}"
                     f" (observation {row['observation_id']}){found}")

    lines += ["", "Pages that failed in this run (from settings.json):"]
    lines += [f"  {page}" for page in failed] or ["  none"]
    return "\n".join(lines) + "\n"


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_reports(result, run_folder, run_name):
    summary = summary_text(result, run_name, failed_pages(run_folder))
    (run_folder / "comparison_summary.txt").write_text(summary, encoding="utf-8")

    write_csv(run_folder / "comparison_details.csv", result["details"],
              ["issue", "page", "community", "field", "hand_value", "model_value", "explanation"])

    side_by_side = [{
        "issue": hand["issue"], "page": hand["page"],
        "hand_community": first_name(hand), "model_community": model["community_name"],
        "raw_text_similarity": f"{raw_text_ratio(hand, model):.3f}",
        "hand_description": hand["description"], "model_description": model["description"],
        "hand_notes": hand["notes"], "model_notes": model["notes"],
    } for hand, model in result["scored_pairs"]]
    write_csv(run_folder / "review_side_by_side.csv", side_by_side, list(side_by_side[0]) if side_by_side else ["issue"])
    return summary


# --- Self-test --------------------------------------------------------------

def self_test():
    """Write the hand-checked rows out in the model's flat format, compare
    them with themselves, and check every field scores 100%."""
    # A throwaway folder outside the project, so git doesn't pick it up
    test_folder = Path(tempfile.mkdtemp(prefix="lc_compare_self_test_"))
    hand_rows = load_hand_rows()
    write_csv(test_folder / "land_directory.csv", hand_rows, COLUMNS)

    result = compare(hand_rows, load_model_rows(test_folder / "land_directory.csv"))
    print(write_reports(result, test_folder, "_self_test (hand-checked rows as model output)"))

    problems = []
    pairs = result["scored_pairs"]
    if len(pairs) != result["hand_in_scope"]:
        problems.append(f"{len(pairs)} pairs for {result['hand_in_scope']} rows")
    if result["missed"] or result["extra"]:
        problems.append(f"{len(result['missed'])} missed, {len(result['extra'])} extra")
    # Each row should be paired with its own copy: same name, page and raw_text
    for hand, model in pairs:
        if [hand[c] for c in ("community_name", "page", "raw_text")] != \
           [model[c] for c in ("community_name", "page", "raw_text")]:
            problems.append(f"observation {hand['observation_id']} ({first_name(hand)}) "
                            f"was paired with {model['community_name']}")
    for field, count in result["agree_counts"].items():
        if count != len(pairs):
            problems.append(f"{field} scored {count}/{len(pairs)}")
    if problems:
        print("SELF-TEST FAILED:")
        for problem in problems:
            print("  " + problem)
        return False
    print(f"SELF-TEST PASSED: every field 100%, no missed or extra rows "
          f"(files in {test_folder})")
    return True


def main():
    if "--self-test" in sys.argv:
        sys.exit(0 if self_test() else 1)

    model_file = RUN_FOLDER / "land_directory.csv"
    if not model_file.exists():
        print(f"No model output found at {model_file}")
        return
    result = compare(load_hand_rows(), load_model_rows(model_file))
    print(write_reports(result, RUN_FOLDER, RUN_NAME))
    print(f"Saved comparison_summary.txt, comparison_details.csv and "
          f"review_side_by_side.csv in {RUN_FOLDER}")


if __name__ == "__main__":
    main()
