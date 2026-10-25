# Project 2 - Structured Data Extraction on Lesbian Connection Land Directories 


_Lesbian Connection_ is a publication that began in the 1970s. It is by and for lesbian women and shares stories, art, news, resources, events, and advertisements across the community. 

For Project 2, I am starting with the code I used for our inital introduction to structured data extraction to attempt to use Gemini to create a csv from LC's land directories. 

DECISIONS.md tracks decisions made throughout this project, as well as notes for each run and what changed in between them. 


## What's in this folder

| File or folder | What it is |
|---|---|
| `convert_pdfs.py` | Turns every PDF in `pdfs/` into one PNG per page, saved in `images/all_pages/` |
| `01_directory_to_csv.py` | **Lesbian Connection:** sends land directory page images to Gemini or Claude and saves one row per listing to a CSV |
| `02_compare_to_handchecked.py` | Scores a run's CSV field by field against hand-coded data: my Project 1 data for LC, or `reference/maize_handcoded/maize_handcoded.csv` for Maize (the `HAND_CSV` setting) |
| `03_maize_to_csv.py` | **Maize:** sends one whole issue's transcribed text at a time to Gemini or Claude and saves one row per Country Connections listing, On the Land report, or land announcement. Reads the transcriptions from the `Maize-OCR` project (`~/Desktop/Maize-OCR`) |
| `extraction_common.py` | Code shared by the LC and Maize scripts: the codebook columns, vocabularies, Gemini and Claude calls, prices, checks, and run folders |
| `codebook.md` | The coding rules, adapted from Project 1. Both extraction scripts put this whole file into the prompt |
| `codebook_maize.md` | Maize additions to `codebook.md` (what counts as a row in Maize, and Maize-specific rules), read after it by `03_maize_to_csv.py` |
| `reference/` | Copies of the Project 1 vocabularies (types, accepted groups, focuses) and sources table, with the 29 Maize issues added |
| `reference/maize_handcoded/` | My hand-coded Maize test set (issues 25 and 53), the blank template, and a guide to filling it in |
| `DECISIONS.md` | Decisions, notes on each run, what changed between runs, and reflections for the write-up |
| `requirements.txt` | The Python packages and versions this project uses |
| `images/` | The LC land directory page images the LC script reads (not in git) |
| `pdfs/` | The original LC PDFs (not in git) |
| `output/runs/` | One folder per run (LC or Maize), with its results, the exact settings used, and its comparison with the hand-coded data |


## Setup (once)

1. Open the `Project2-StructuredExtraction-LCLand` folder in the terminal:

   ```bash
   cd ~/Desktop/Project2-StructuredExtraction-LCLand
   ```

2. If there is no `venv` folder yet, create the virtual environment:

   ```bash
   python3 -m venv venv
   ```

3. Activate it (see below), then install the packages listed in
   `requirements.txt`, at the exact versions this project was run with:

   ```bash
   python -m pip install -r requirements.txt
   ```

   Use `python -m pip`, not plain `pip`: this `venv` was copied from another
   project, and its `pip` command still installs into that project's
   environment.

   `convert_pdfs.py` also needs ImageMagick (the `magick` command), which is
   installed separately, e.g. with `brew install imagemagick`.

4. Create a file named `.env` in this folder with your API keys. You only
   need the key for the provider you're using (see `MODEL` below):

   ```
   GEMINI_API_KEY=your-gemini-key
   ANTHROPIC_API_KEY=your-claude-key
   ```

   `.env` is in `.gitignore`, so the key is never committed.


## Every time: open the virtual environment

1. Open the folder in the terminal:

   ```bash
   cd ~/Desktop/Project2-StructuredExtraction-LCLand
   ```

2. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

   `(venv)` appears at the start of the prompt when it is on. Do this again
   in every new terminal window.

3. When you're done:

   ```bash
   deactivate
   ```


## Running the scripts

Run them from this folder with the virtual environment on.

### 1. Convert PDFs to images: `convert_pdfs.py`

Put the PDFs in `pdfs/`, then:

```bash
python convert_pdfs.py
```

Every page of every PDF is saved to `images/all_pages/` as
`lc-<issue>-<page>.png`. The extraction script does not read that folder:
copy the land directory pages you want extracted into `images/` itself.

### 2. Extract listings with Gemini: `01_directory_to_csv.py`

Before running, check the settings near the top of the script:

- `RUN_NAME`: the name of this run's folder in `output/runs/`. **Use a new
  name whenever you change `MODEL`, `codebook.md`, `PROMPT`, or `FIELDS`**;
  the script stops if you reuse a name with different settings. Reuse the
  same name to retry failed pages or add more pages to a run.
- `MODEL`: which model to use; its price must be listed in `PRICES`. A name
  starting with `claude-` (e.g. `claude-opus-5-5`) is sent to Anthropic's
  Claude API and needs `ANTHROPIC_API_KEY`; anything else goes to Gemini and
  needs `GEMINI_API_KEY`. For Claude, `CLAUDE_EFFORT` sets how hard it thinks.
- `TEST_PAGES`: the images to extract. Right now it is the 18 directory pages
  of the 5 issues hand-checked in Project 1. Set it to `[]` to extract every
  image in `images/`.

Then run:

```bash
python 01_directory_to_csv.py
```

It prints each page's listing count and cost, plus `CHECK:` lines for things
to look at by hand (a missing address, a listing that stops mid-sentence, a
page-break fragment joined onto a listing that already looked complete).
Pages that fail are listed at the end; run the script again to retry them,
since finished pages are saved and not sent again.

Results go to `output/runs/<RUN_NAME>/`:

- `land_directory.csv`: one row per listing
- `settings.json`: the model, prompt and fields used, plus a log of each time
  the script ran (date, pages, failures, cost)
- `pages/`: Gemini's saved answer for each page

### 3. Compare with the hand-checked data: `02_compare_to_handchecked.py`

Set the two settings at the top:

- `RUN_NAME`: the same run name as in `01_directory_to_csv.py` (or
  `03_maize_to_csv.py` for a Maize run).
- `HAND_CSV`: `None` to compare an LC run with my Project 1 data, or
  `SCRIPT_DIR / "reference" / "maize_handcoded" / "maize_handcoded.csv"` to
  compare a Maize run with my hand-coded Maize issues. For Maize, only the
  issues the run covers are scored.

Then:

```bash
python 02_compare_to_handchecked.py
```

It reads the hand-checked rows from `~/Desktop/8510-Project1/source_data/`
(read only), pairs them with the run's rows, and prints the accuracy of each
field, plus missed rows (only in my data) and extra rows (only the model
found). It saves three files in the run's folder:

- `comparison_summary.txt`: the printed summary
- `comparison_details.csv`: one row per disagreement, my value next to the
  model's
- `review_side_by_side.csv`: my description and notes next to the model's

To check that the comparison itself works:

```bash
python 02_compare_to_handchecked.py --self-test
```

It compares the hand-checked rows with themselves and should report 100%.

### 4. Extract Maize listings: `03_maize_to_csv.py`

This reads the Maize transcriptions made in the `Maize-OCR` project
(`~/Desktop/Maize-OCR/output/runs/2026-10-23_all_haiku-5.5/text/`, one folder
per issue, one text file per page), so that project must be done first. It
sends one whole issue at a time, with `codebook.md` and `codebook_maize.md`,
and keeps only Country Connections listings, On the Land reports, and
announcements about a specific land.

Before running, check the settings near the top of the script:

- `RUN_NAME`: as for LC: a new name whenever you change `MODEL`,
  `codebook.md`, or `codebook_maize.md`; the same name to retry failed issues
  or add more issues to a run.
- `MODEL` and `CLAUDE_EFFORT`: as for LC (Gemini or Claude).
- `TEST_ISSUES`: the issues to extract, as folder names (e.g.
  `"maize-53-spring1997"`). Set it to `[]` to extract all 29 issues.
- `MAIZE_TEXT_FOLDER`: where the transcriptions are; change it only if the
  Maize-OCR project moves or uses a new transcription run.

The script won't send anything while `codebook_maize.md` contains the words
"TO DECIDE": those mark rules still to be decided. Open questions it should
flag instead are written as "OPEN QUESTION"; search the output's notes for
that phrase to find cases to decide.

Then run:

```bash
python 03_maize_to_csv.py
```

It prints each issue's row counts (listings, reports, announcements), cost,
and `CHECK:` lines. Results go to `output/runs/<RUN_NAME>/`:

- `land_directory.csv`: one row per listing, report, or announcement, in the
  same columns as the LC sheet
- `settings.json`: the model, prompt and fields used, plus a log of each run
- `issues/`: the model's saved answer for each issue

To score it, run `02_compare_to_handchecked.py` with `HAND_CSV` set to the
Maize hand-coded CSV (step 3).


## After a run

Add notes on the run to `DECISIONS.md` (what changed, the results, what to
try next), then commit the scripts, `codebook.md` (and `codebook_maize.md`
for Maize), `DECISIONS.md`, and the run's folder.
