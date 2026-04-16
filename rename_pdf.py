#!/usr/bin/env python3
"""
rename_pdf.py — OCR the PIF number from Chargeurs PCC PDFs and rename the file.

Usage:
    python rename_pdf.py [--dry-run] [--recursive] path [path ...]

System requirements:
    macOS:   brew install tesseract
    Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
             then ensure Tesseract is on PATH, or set TESSDATA_PREFIX /
             pytesseract.pytesseract.tesseract_cmd (see _configure_tesseract below)
    Linux:   sudo apt install tesseract-ocr
"""

import argparse
import os
import platform
import re
import sys
from pathlib import Path

try:
    import pypdfium2 as pdfium
except ImportError:
    sys.exit("Missing dependency: run  pip install pypdfium2")

try:
    from PIL import Image  # noqa: F401  (pypdfium2 returns PIL images)
except ImportError:
    sys.exit("Missing dependency: run  pip install Pillow")

try:
    import pytesseract
except ImportError:
    sys.exit("Missing dependency: run  pip install pytesseract")


def _configure_tesseract() -> None:
    """Auto-detect Tesseract on Windows if it is not already on PATH."""
    if platform.system() != "Windows":
        return
    # Common install locations from the UB Mannheim installer
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    # Only set if not already discoverable on PATH
    if pytesseract.pytesseract.tesseract_cmd == "tesseract":
        for path in candidates:
            if os.path.isfile(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break


# ---------------------------------------------------------------------------
# Tuneable constants
# ---------------------------------------------------------------------------

RENDER_DPI = 150  # Higher = slower but more accurate; 150 is plenty for print

# Fractional crop region within the first page (0.0 – 1.0).
# Both document templates have the PIF number in the top-right corner.
CROP_LEFT_FRAC = 0.55   # start at 55 % from left  → right 45 % of page
CROP_TOP_FRAC = 0.00    # top of page
CROP_RIGHT_FRAC = 1.00  # right edge
CROP_BOTTOM_FRAC = 0.20  # bottom of top-20 % strip

# Tesseract options:
#   --psm 6  → assume a uniform block of text (suits the narrow header crop)
#   --oem 3  → LSTM neural-net engine (best accuracy on Tesseract 4+)
TESS_CONFIG = "--psm 6 --oem 3"

# Pattern to match e.g. PIF-26208058
PIF_PATTERN = re.compile(r"PIF-\d+")


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def extract_pif_from_pdf(pdf_path: Path) -> str | None:
    """
    Render the first page of *pdf_path*, crop the top-right region, run
    Tesseract OCR and return the first PIF-XXXXXXXX match, or None.
    """
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        page = pdf[0]
        # pypdfium2's `scale` is relative to 72 DPI
        img = page.render(scale=RENDER_DPI / 72).to_pil()
    finally:
        pdf.close()

    # Make sure we have an RGB PIL image (pypdfium2 may return RGBA/BGR etc.)
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size

    # Crop to the top-right region
    left = int(width * CROP_LEFT_FRAC)
    top = int(height * CROP_TOP_FRAC)
    right = int(width * CROP_RIGHT_FRAC)
    bottom = int(height * CROP_BOTTOM_FRAC)
    cropped = img.crop((left, top, right, bottom))

    # OCR
    raw_text = pytesseract.image_to_string(cropped, config=TESS_CONFIG)

    # Normalise common Tesseract mis-reads before searching
    # (em-dash / en-dash / underscore → ASCII hyphen)
    normalised = raw_text.replace("\u2014", "-").replace("\u2013", "-").replace("_", "-")

    match = PIF_PATTERN.search(normalised)
    return match.group(0) if match else None


# ---------------------------------------------------------------------------
# Rename logic
# ---------------------------------------------------------------------------

def rename_pdf(pdf_path: Path, dry_run: bool) -> tuple[str, str]:
    """
    Attempt to rename *pdf_path* to its PIF number.

    Returns (status_code, human_readable_message) where status_code is one of:
      'OK', 'SKIP', 'CONFLICT', 'WARN', 'ERROR'
    """
    try:
        pif = extract_pif_from_pdf(pdf_path)
    except Exception as exc:  # noqa: BLE001
        return "ERROR", f"{pdf_path.name}: {exc}"

    if pif is None:
        return "WARN", f"could not find PIF number in  {pdf_path.name}"

    new_name = pif + ".pdf"

    # Already correctly named
    if pdf_path.name == new_name:
        return "SKIP", f"{pdf_path.name}  (already correct)"

    destination = pdf_path.parent / new_name

    # Target name already exists
    if destination.exists():
        return (
            "CONFLICT",
            f"{pdf_path.name}  →  {new_name}  (destination already exists: {destination})",
        )

    if dry_run:
        return "OK", f"{pdf_path.name}  →  {new_name}  [dry-run]"

    pdf_path.rename(destination)
    return "OK", f"{pdf_path.name}  →  {new_name}"


# ---------------------------------------------------------------------------
# Path processing
# ---------------------------------------------------------------------------

def process_path(target: Path, dry_run: bool, recursive: bool) -> None:
    """Process a single file or a directory of PDFs."""
    if target.is_file():
        _handle_one(target, dry_run)
        return

    if target.is_dir():
        glob_fn = target.rglob if recursive else target.glob
        pdf_files = sorted(glob_fn("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in {target}")
            return

        counts: dict[str, int] = {"OK": 0, "SKIP": 0, "WARN": 0, "CONFLICT": 0, "ERROR": 0}
        for pdf in pdf_files:
            status = _handle_one(pdf, dry_run)
            counts[status] = counts.get(status, 0) + 1

        print(
            f"\nDone: {counts['OK']} renamed, {counts['SKIP']} skipped, "
            f"{counts['WARN']} warnings, {counts['CONFLICT']} conflicts, "
            f"{counts['ERROR']} errors."
        )
        return

    print(f"[ERROR] {target} is not a file or directory.", file=sys.stderr)


def _handle_one(pdf_path: Path, dry_run: bool) -> str:
    """Rename one file and print the result. Returns the status code."""
    status, message = rename_pdf(pdf_path, dry_run)
    prefix = f"[{status}]"
    print(f"{prefix:<12} {message}")
    return status


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rename_pdf.py",
        description="Rename Chargeurs PCC PDF files to their PIF reference number.",
    )
    parser.add_argument(
        "paths",
        metavar="path",
        nargs="+",
        help="One or more PDF files or directories containing PDFs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be renamed without making any changes.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="When a directory is given, search subdirectories too.",
    )
    return parser.parse_args()


def main() -> None:
    _configure_tesseract()

    # Fail fast with a helpful message if Tesseract is not installed
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        msg = "Tesseract OCR not found.\n"
        system = platform.system()
        if system == "Darwin":
            msg += "Install it with:  brew install tesseract"
        elif system == "Windows":
            msg += (
                "Download and install from:\n"
                "  https://github.com/UB-Mannheim/tesseract/wiki\n"
                "Then re-run this script (the installer adds it to PATH automatically)."
            )
        else:
            msg += "Install it with:  sudo apt install tesseract-ocr"
        sys.exit(msg)

    args = parse_args()

    for raw_path in args.paths:
        target = Path(raw_path)
        if not target.exists():
            print(f"[ERROR]      {raw_path}: path does not exist", file=sys.stderr)
            continue
        process_path(target, dry_run=args.dry_run, recursive=args.recursive)


if __name__ == "__main__":
    main()
