#!/usr/bin/env python3
"""
create_test_pdfs.py — Generate two sample PDFs that mimic the Chargeurs PCC
document templates, so you can test rename_pdf.py without real files.

Usage:
    python create_test_pdfs.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4  # 595.27 x 841.89 points


def _y(top_y: float) -> float:
    """
    Convert a 'distance from top of page' coordinate to reportlab's
    bottom-origin coordinate system.
    """
    return PAGE_H - top_y


def make_delivery_note(path: str) -> None:
    """Template 1: Delivery Note with 'D/O NO.: PIF-26208058' in top-right."""
    c = canvas.Canvas(path, pagesize=A4)

    # --- top-left: company block ---
    c.setFont("Helvetica", 16)
    c.drawString(40, _y(50), "CHARGEURS PCC")
    c.setFont("Helvetica", 9)
    c.drawString(40, _y(70), "FASHION TECHNOLOGIES")
    c.setFont("Helvetica", 10)
    c.drawString(40, _y(100), "CHARGEURS PCC ASIA LIMITED")

    # --- top-right: document type ---
    c.setFont("Helvetica", 18)
    c.drawString(400, _y(50), "Delivery Note")

    # --- top-right: reference fields ---
    fields = [
        ("D/O NO.:",         "PIF-26208058"),
        ("CUSTOMER P/O NO.:", "88256GK(YP)"),
        ("CONTRACT NO.:",    "SOP-26105100"),
        ("DELIVERY DATE:",   "31/Mar/2026"),
        ("PICKING LIST NO:", "PIF-26208058 (2)"),
        ("PAGE:",            "1/1"),
    ]
    c.setFont("Helvetica", 9)
    y = 100
    for label, value in fields:
        c.drawString(330, _y(y), label)
        c.drawString(460, _y(y), value)
        y += 16

    c.save()
    print(f"Created: {path}")


def make_packing_list(path: str) -> None:
    """Template 2: Supplier Packing List with 'PIF-26207464' top-right."""
    c = canvas.Canvas(path, pagesize=A4)

    # --- centre: title ---
    c.setFont("Helvetica", 13)
    c.drawString(220, _y(60), "Supplier Packing List")

    # --- top-right: PIF number (large, prominent) ---
    c.setFont("Helvetica", 18)
    c.drawString(400, _y(60), "PIF-26207464")

    # --- left: ship details ---
    c.setFont("Helvetica", 10)
    c.drawString(40, _y(100), "Ship To (Factory):")
    c.drawString(40, _y(130), "Ship From (Supplier):")
    c.setFont("Helvetica", 9)
    c.drawString(40, _y(148), "CHARGEURS PCC ASIA LIMITED")
    c.drawString(40, _y(163), "7/F, CONTEMPO PLACE, 81 HUNG TO ROAD")

    # --- right: dates ---
    c.drawString(330, _y(100), "Print Date:")
    c.drawString(420, _y(100), "03/17/2026")
    c.drawString(330, _y(116), "Issue Date:")
    c.drawString(420, _y(116), "03/17/2026")
    c.drawString(330, _y(132), "Send Date (ETD Date):")
    c.drawString(460, _y(132), "03/18/2026")

    c.save()
    print(f"Created: {path}")


if __name__ == "__main__":
    make_delivery_note("test_delivery_note.pdf")
    make_packing_list("test_packing_list.pdf")
    print("\nDone. Now run:")
    print("  python rename_pdf.py --dry-run test_delivery_note.pdf test_packing_list.pdf")
