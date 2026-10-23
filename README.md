# Project 2 - Structured Data Extraction on Lesbian Connection Land Directories 


_Lesbian Connection_ is a publication that began in the 1970s. It is by and for lesbian women and shares stories, art, news, resources, events, and advertisements across the community. 

For Project 2, I am starting with the code I used for our inital introduction to structured data extraction to attempt to use Gemini to create a csv from LC's land directories. 

DECISIONS.md tracks decisions made throughout this project, as well as notes for each run and what changed in between them. 


## What's in this folder

| File or folder | What it is |
|---|---|
| `convert_pdfs.py` | Turns every PDF in `pdfs/` into one PNG per page, saved in `images/all_pages/` |
| `01_directory_to_csv.py` | Sends land directory page images to Gemini and saves one row per listing to a CSV |
| `02_compare_to_handchecked.py` | Scores a run's CSV field by field against my hand-checked Project 1 data |
| `codebook.md` | The coding rules, adapted from Project 1. The extraction script puts this whole file into the prompt |
| `reference/` | Copies of the Project 1 vocabularies (types, accepted groups, focuses) and sources table |
| `DECISIONS.md` | Decisions, notes on each run, and what changed between runs |
| `images/` | The land directory page images the extraction script reads (not in git) |
| `pdfs/` | The original LC PDFs (not in git) |
| `output/runs/` | One folder per run, with its results and the exact settings used |


## Setup (once)

1. Open the `Project2-StructuredExtraction-LCLand` folder in the terminal:

   ```bash
   cd ~/Desktop/Project2-StructuredExtraction-LCLand
   ```

2. If there is no `venv` folder yet, create the virtual environment:

   ```bash
   python3 -m venv venv
   ```

3. Activate it (see below), then install the packages:

   ```bash
   pip install google-genai python-dotenv
   ```

   `convert_pdfs.py` also needs ImageMagick (the `magick` command), which is
   installed separately, e.g. with `brew install imagemagick`.

4. Create a file named `.env` in this folder with your Gemini API key:

   ```
   GEMINI_API_KEY=your-key-here
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
- `MODEL`: which Gemini model to use (its price must be listed in `PRICES`).
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

Set `RUN_NAME` at the top to the same run name as in `01_directory_to_csv.py`,
then:

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


## After a run

Add notes on the run to `DECISIONS.md` (what changed, the results, what to
try next), then commit the scripts, `codebook.md`, `DECISIONS.md`, and the
run's folder.
