"""Convert every page of a PDF in a folder into a high resolution PNG using ImageMagick."""

import shutil
import subprocess
from pathlib import Path

# ---Settings---
INPUT_DIR = Path("pdfs") 
OUTPUT_DIR = Path("images")
DPI = 300
# ----- 

def convert_pdf(pdf_path: Path, output_dir: Path, dpi: int) -> None:
    """Turn one PDF into one PNG per page: name-oo1.png, name-002.png,..."""
    output_pattern = output_dir / f"{pdf_path.stem}-%03d.png"

    command = [
        "magick",
        "-density", str(dpi),
        str(pdf_path),
        "-alpha", "remove",
        "-background", "white",
        "-scene", "1",
        str(output_pattern),
    ]

    subprocess.run(command, check=True)

def main() -> None:
    if shutil.which("magick") is None:
        raise SystemExit("ImageMagick's 'magick' command wasn't found on your PATH.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {INPUT_DIR.resolve()}")
        return

    for pdf in pdfs:
        print(f"Converting {pdf.name}...")
        try:
            convert_pdf(pdf, OUTPUT_DIR, DPI)
        except subprocess.CalledProcessError as err:
            print(f" Failed on {pdf.name} (exit code {err.returncode}); skipping.")

        print(f"Done. Images are in {OUTPUT_DIR.resolve()}")

    if __name__ == "__main__":
        main()