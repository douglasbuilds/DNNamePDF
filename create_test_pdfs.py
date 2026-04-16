#!/usr/bin/env python3
"""
create_test_pdfs.py — Generate two sample PDFs that mimic the Chargeurs PCC
document templates, so you can test rename_pdf.py without real files.

Usage:
    python create_test_pdfs.py
"""

import fitz  # PyMuPDF


def make_delivery_note(path: str) -> None:
    """Template 1: Delivery Note with 'D/O NO.: PIF-26208058' in top-right."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 portrait

    # --- top-left: company block ---
    page.insert_text((40, 50), "CHARGEURS PCC", fontsize=16, fontname="helv")
    page.insert_text((40, 70), "FASHION TECHNOLOGIES", fontsize=9, fontname="helv")
    page.insert_text((40, 100), "CHARGEURS PCC ASIA LIMITED", fontsize=10, fontname="helv")

    # --- top-right: document type ---
    page.insert_text((400, 50), "Delivery Note", fontsize=18, fontname="helv")

    # --- top-right: reference fields ---
    fields = [
        ("D/O NO.:",        "PIF-26208058"),
        ("CUSTOMER P/O NO.:", "88256GK(YP)"),
        ("CONTRACT NO.:",    "SOP-26105100"),
        ("DELIVERY DATE:",   "31/Mar/2026"),
        ("PICKING LIST NO:", "PIF-26208058 (2)"),
        ("PAGE:",            "1/1"),
    ]
    y = 100
    for label, value in fields:
        page.insert_text((330, y), label, fontsize=9, fontname="helv")
        page.insert_text((460, y), value, fontsize=9, fontname="helv")
        y += 16

    doc.save(path)
    doc.close()
    print(f"Created: {path}")


def make_packing_list(path: str) -> None:
    """Template 2: Supplier Packing List with 'PIF-26207464' top-right."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    # --- centre: title ---
    page.insert_text((220, 60), "Supplier Packing List", fontsize=13, fontname="helv")

    # --- top-right: PIF number (large, prominent) ---
    page.insert_text((400, 60), "PIF-26207464", fontsize=18, fontname="helv")

    # --- left: ship details ---
    page.insert_text((40, 100), "Ship To (Factory):", fontsize=10, fontname="helv")
    page.insert_text((40, 130), "Ship From (Supplier):", fontsize=10, fontname="helv")
    page.insert_text((40, 148), "CHARGEURS PCC ASIA LIMITED", fontsize=9, fontname="helv")
    page.insert_text((40, 163), "7/F, CONTEMPO PLACE, 81 HUNG TO ROAD", fontsize=9, fontname="helv")

    # --- right: dates ---
    page.insert_text((330, 100), "Print Date:", fontsize=9, fontname="helv")
    page.insert_text((420, 100), "03/17/2026", fontsize=9, fontname="helv")
    page.insert_text((330, 116), "Issue Date:", fontsize=9, fontname="helv")
    page.insert_text((420, 116), "03/17/2026", fontsize=9, fontname="helv")
    page.insert_text((330, 132), "Send Date (ETD Date):", fontsize=9, fontname="helv")
    page.insert_text((460, 132), "03/18/2026", fontsize=9, fontname="helv")

    doc.save(path)
    doc.close()
    print(f"Created: {path}")


if __name__ == "__main__":
    make_delivery_note("test_delivery_note.pdf")
    make_packing_list("test_packing_list.pdf")
    print("\nDone. Now run:")
    print("  python rename_pdf.py --dry-run test_delivery_note.pdf test_packing_list.pdf")
