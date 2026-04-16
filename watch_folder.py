#!/usr/bin/env python3
"""
watch_folder.py — Hotfolder watcher for DNNamePDF.

Monitors ./input for new PDF files, runs OCR to extract the PIF number,
then moves each file to ./output renamed to PIF-XXXXXXXX.pdf.

PDFs for which no PIF number could be read (or that error during OCR)
are moved to ./failed so the input folder stays clean and the user
can see at a glance which files need attention.

Usage:
    python watch_folder.py

Press Ctrl+C to stop.
"""

import shutil
import sys
import time
from pathlib import Path

try:
    import pytesseract
except ImportError:
    sys.exit("Missing dependency: run  pip install pytesseract")

from rename_pdf import _configure_tesseract, extract_pif_from_pdf


# ---------------------------------------------------------------------------
# Folder layout (resolved relative to this script, so it works from any CWD)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
FAILED_DIR = BASE_DIR / "failed"


# ---------------------------------------------------------------------------
# Polling behaviour
# ---------------------------------------------------------------------------

POLL_INTERVAL_SECONDS = 2       # how often to scan the input folder
STABILITY_POLLS_REQUIRED = 2    # file size must be unchanged this many polls
                                # before we consider the file ready to process
                                # (prevents reading a half-copied PDF)


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def process_pdf(pdf_path: Path) -> None:
    """Extract the PIF number and move the file to output/ (or failed/)."""
    try:
        pif = extract_pif_from_pdf(pdf_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR]    {pdf_path.name}: {exc}")
        _move(pdf_path, _unique_destination(FAILED_DIR, pdf_path.name))
        return

    if pif is None:
        print(f"[WARN]     {pdf_path.name}: could not read PIF number")
        _move(pdf_path, _unique_destination(FAILED_DIR, pdf_path.name))
        return

    destination = _unique_destination(OUTPUT_DIR, pif + ".pdf")
    _move(pdf_path, destination)

    if destination.name == pif + ".pdf":
        print(f"[OK]       {pdf_path.name} -> {destination.name}")
    else:
        print(f"[CONFLICT] {pdf_path.name} -> {destination.name} "
              "(target name already existed, saved with suffix)")


def _unique_destination(folder: Path, filename: str) -> Path:
    """Return a path in *folder* that doesn't yet exist; append (n) if needed."""
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / filename
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    n = 2
    while (folder / f"{stem} ({n}){suffix}").exists():
        n += 1
    return folder / f"{stem} ({n}){suffix}"


def _move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


# ---------------------------------------------------------------------------
# Watch loop
# ---------------------------------------------------------------------------

def watch_loop() -> None:
    """Poll INPUT_DIR and process each PDF once its size has been stable."""
    # Tracks pending files: {Path: (last_size_seen, consecutive_stable_polls)}
    pending: dict[Path, tuple[int, int]] = {}

    while True:
        current_pdfs = {
            p for p in INPUT_DIR.glob("*.pdf")
            if p.is_file() and not p.name.startswith(".")
        }

        # Drop tracking for files that disappeared
        for gone in set(pending) - current_pdfs:
            pending.pop(gone, None)

        for pdf in sorted(current_pdfs):
            try:
                size = pdf.stat().st_size
            except FileNotFoundError:
                pending.pop(pdf, None)
                continue

            last_size, stable = pending.get(pdf, (-1, 0))

            if size != last_size:
                # Still being written — reset the stability counter.
                pending[pdf] = (size, 0)
                continue

            stable += 1
            if stable >= STABILITY_POLLS_REQUIRED and size > 0:
                pending.pop(pdf, None)
                process_pdf(pdf)
            else:
                pending[pdf] = (size, stable)

        time.sleep(POLL_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _configure_tesseract()
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        sys.exit(
            "Tesseract OCR not found. "
            "See readme.txt section 1 for install instructions."
        )

    for d in (INPUT_DIR, OUTPUT_DIR, FAILED_DIR):
        d.mkdir(exist_ok=True)

    print("DNNamePDF — hotfolder mode")
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Output : {OUTPUT_DIR}")
    print(f"  Failed : {FAILED_DIR}")
    print("\nDrop PDF files into the input folder. Press Ctrl+C to stop.\n")

    try:
        watch_loop()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
