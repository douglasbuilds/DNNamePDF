===============================================================================
 DNNamePDF — PDF OCR Renamer for Chargeurs PCC Documents
===============================================================================

WHAT THIS TOOL DOES
-------------------
This tool automatically renames Chargeurs PCC PDF files (Delivery Notes and
Supplier Packing Lists) using the PIF reference number printed in the
top-right corner of the first page.

Example:
    Before:  scan_001.pdf
    After:   PIF-26208058.pdf

It works by:
  1. Rendering the first page of each PDF as an image.
  2. Cropping the top-right corner where the PIF number appears.
  3. Running Tesseract OCR on that region.
  4. Finding the "PIF-XXXXXXXX" pattern and renaming the file.


-------------------------------------------------------------------------------
 1. SYSTEM REQUIREMENTS
-------------------------------------------------------------------------------

 * Python 3.10 or newer
 * Tesseract OCR engine (installed separately from Python)

Install Tesseract OCR:

  macOS:
      brew install tesseract

  Windows:
      Download and run the installer from:
      https://github.com/UB-Mannheim/tesseract/wiki
      (The installer adds Tesseract to PATH automatically.)

  Linux (Debian / Ubuntu):
      sudo apt install tesseract-ocr


-------------------------------------------------------------------------------
 2. INSTALLATION
-------------------------------------------------------------------------------

Step 1: Open a terminal in the project folder.

Step 2: (Recommended) Create and activate a Python virtual environment.

  macOS / Linux:
      python3 -m venv .venv
      source .venv/bin/activate

  Windows (PowerShell):
      python -m venv .venv
      .venv\Scripts\Activate.ps1

Step 3: Install the Python dependencies.

      pip install -r requirements.txt

The required packages are:
  - PyMuPDF     (renders PDF pages to images)
  - Pillow      (image handling)
  - pytesseract (Python wrapper around Tesseract OCR)


-------------------------------------------------------------------------------
 3. QUICK START — HOTFOLDER MODE (RECOMMENDED FOR EVERYDAY USE)
-------------------------------------------------------------------------------

The easiest way to use this tool is the hotfolder watcher. You start it
once, and from then on you simply drag-and-drop PDFs into the "input"
folder. The tool will automatically rename each PDF and move it to
the "output" folder. Files it cannot read land in "failed".

Folder layout (all three are auto-created the first time you run it):

      DNNamePDF/
        input/     <- drop your PDFs here
        output/    <- successfully renamed PDFs appear here
        failed/    <- PDFs where no PIF number could be read

Start the watcher:

      python watch_folder.py

You will see something like:

      DNNamePDF - hotfolder mode
        Input  : .../DNNamePDF/input
        Output : .../DNNamePDF/output
        Failed : .../DNNamePDF/failed

      Drop PDF files into the input folder. Press Ctrl+C to stop.

Now drop (or copy, or scan-to) PDF files into the "input" folder.
Each file prints one of these results as it is processed:

      [OK]       scan_001.pdf -> PIF-26208058.pdf
      [WARN]     scan_002.pdf: could not read PIF number
      [CONFLICT] scan_003.pdf -> PIF-26208058 (2).pdf  (target name already existed)
      [ERROR]    scan_004.pdf: <error message>

Notes on how the watcher behaves:

  * It waits until a file has stopped growing before processing it,
    so it's safe to drop large files or let your scanner write directly
    into the input folder.
  * If a PIF number already exists in output, the new file is saved
    with "(2)", "(3)", etc. appended - nothing is ever overwritten.
  * Any PDFs already sitting in input when you start the watcher are
    processed automatically.
  * Press Ctrl+C to stop.


-------------------------------------------------------------------------------
 4. BASIC USAGE (MANUAL / ONE-OFF MODE)
-------------------------------------------------------------------------------

General syntax:

      python rename_pdf.py [--dry-run] [--recursive] path [path ...]

A "path" can be a single PDF file or a folder that contains PDFs.

----- Example A: Rename a single PDF -----

      python rename_pdf.py "C:\Documents\scan_001.pdf"

----- Example B: Rename every PDF in a folder -----

      python rename_pdf.py "C:\Documents\Chargeurs"

----- Example C: Include sub-folders too -----

      python rename_pdf.py --recursive "C:\Documents\Chargeurs"

----- Example D: Preview only, do NOT actually rename -----

      python rename_pdf.py --dry-run "C:\Documents\Chargeurs"

----- Example E: Multiple files / folders in one run -----

      python rename_pdf.py file1.pdf file2.pdf "C:\Folder\Sub"


-------------------------------------------------------------------------------
 5. COMMAND-LINE OPTIONS (rename_pdf.py)
-------------------------------------------------------------------------------

  --dry-run      Show what the tool WOULD rename without changing any files.
                 Use this first whenever you are unsure.

  --recursive    When a folder is given, also scan sub-folders for PDFs.

  -h, --help     Show usage help.


-------------------------------------------------------------------------------
 6. UNDERSTANDING THE OUTPUT
-------------------------------------------------------------------------------

For every PDF the tool prints a status tag followed by a message:

  [OK]         File was renamed (or would be renamed, in --dry-run mode).
  [SKIP]       File already has the correct PIF-XXXXXXXX.pdf name.
  [WARN]       No PIF number could be read from the page. File is untouched.
  [CONFLICT]   A file with the target name already exists. File is untouched.
  [ERROR]      Something went wrong (e.g. PDF is corrupt). File is untouched.

At the end of a folder run you will see a summary, e.g.:

      Done: 12 renamed, 3 skipped, 1 warnings, 0 conflicts, 0 errors.


-------------------------------------------------------------------------------
 7. RECOMMENDED WORKFLOW (MANUAL MODE)
-------------------------------------------------------------------------------

  1) Put all the PDFs you want to rename in a single folder.

  2) Run a PREVIEW first to confirm the tool will do the right thing:

         python rename_pdf.py --dry-run "path/to/folder"

  3) Review the [OK], [WARN] and [CONFLICT] lines.
     - Any [WARN] items will need to be renamed manually.
     - Any [CONFLICT] items mean a file with that name already exists;
       decide which copy to keep before rerunning.

  4) Run the command again WITHOUT --dry-run to perform the rename:

         python rename_pdf.py "path/to/folder"


-------------------------------------------------------------------------------
 8. TESTING WITH SAMPLE PDFs
-------------------------------------------------------------------------------

If you do not have any real PDFs handy, you can generate two sample
Chargeurs-style test files:

      python create_test_pdfs.py

This creates:
      test_delivery_note.pdf   (should be renamed to PIF-26208058.pdf)
      test_packing_list.pdf    (should be renamed to PIF-26207464.pdf)

Then try:

      python rename_pdf.py --dry-run test_delivery_note.pdf test_packing_list.pdf


-------------------------------------------------------------------------------
 9. TROUBLESHOOTING
-------------------------------------------------------------------------------

Problem:  "Tesseract OCR not found."
Fix:      Install Tesseract for your OS (see Section 1) and reopen the
          terminal so PATH is refreshed. On Windows, the script also checks
          the default install locations:
              C:\Program Files\Tesseract-OCR\tesseract.exe
              C:\Program Files (x86)\Tesseract-OCR\tesseract.exe

Problem:  "Missing dependency: run pip install ..."
Fix:      Run:  pip install -r requirements.txt
          Make sure your virtual environment is activated first.

Problem:  Many [WARN] "could not find PIF number" results.
Possible causes and fixes:
    - The PIF number is not in the top-right 45% x 20% of page 1.
      Adjust the CROP_* constants near the top of rename_pdf.py.
    - The scan resolution is low. Increase RENDER_DPI (e.g. from 150 to 300)
      in rename_pdf.py. Higher DPI = slower but more accurate OCR.
    - The PDF is image-only with very poor contrast. Re-scan at higher
      quality or pre-process the image.

Problem:  [CONFLICT] messages.
Fix:      Two different PDFs resolved to the same PIF number. Open both
          files to decide which to keep, then delete or move one before
          running the tool again.

Problem:  I want to undo a rename.
Note:     The tool renames in place and does NOT keep a backup. Always run
          with --dry-run first, and ideally work on a COPY of your files.


-------------------------------------------------------------------------------
 10. FILES IN THIS PROJECT
-------------------------------------------------------------------------------

  watch_folder.py      Hotfolder watcher — run this for drag-and-drop mode.
  rename_pdf.py        Manual / command-line renamer (single files, folders).
  create_test_pdfs.py  Generates two sample PDFs for testing.
  requirements.txt     Python dependencies.
  readme.txt           This file.
  input/               Drop PDFs here (auto-created on first run).
  output/              Renamed PDFs appear here.
  failed/              PDFs where no PIF number could be read.


-------------------------------------------------------------------------------
 11. LICENSING OF BUNDLED LIBRARIES
-------------------------------------------------------------------------------

All libraries used by this tool are open source AND licensed for
commercial use with no royalties and no copyleft obligations:

  pypdfium2    Apache 2.0 / BSD-3-Clause   (PDF page rendering)
  pytesseract  Apache 2.0                  (Python wrapper for Tesseract)
  Tesseract    Apache 2.0                  (the OCR engine itself)
  Pillow       MIT-CMU (HPND)              (image handling)
  reportlab    BSD-3-Clause                (sample PDF generator; test only)
  Python       Python Software Foundation License

You are free to install and run this tool inside your organisation,
redistribute it, or ship it as part of a commercial product, subject
only to the attribution requirements of each license (keep the
LICENSE/NOTICE files that come with each package).


-------------------------------------------------------------------------------
 12. QUICK REFERENCE
-------------------------------------------------------------------------------

  Install deps:       pip install -r requirements.txt
  Hotfolder mode:     python watch_folder.py     (then drop PDFs into input/)
  Preview folder:     python rename_pdf.py --dry-run  "folder"
  Rename folder:      python rename_pdf.py            "folder"
  Include sub-dirs:   python rename_pdf.py --recursive "folder"
  Generate samples:   python create_test_pdfs.py
  Get CLI help:       python rename_pdf.py --help

===============================================================================
