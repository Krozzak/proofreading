#!/usr/bin/env python3
"""
Generates the manual-E2E fixtures: a synthetic MNY brief (.xlsx) and sample
litho PDFs (standard, CUBBY, invalid name, near-empty "scanned" one).

Usage:
    python3 scripts/gen_fixtures.py
Writes into tests/fixtures/e2e/.
"""
import os

import fitz  # PyMuPDF
import openpyxl

OUT = os.path.join(os.path.dirname(__file__), '..', 'tests', 'fixtures', 'e2e')
os.makedirs(OUT, exist_ok=True)

COLUMNS = [
    'LITHO', 'DECRIPTION', 'UPC SEQUENCE', 'UPC POSITION', 'UPC',
    'PRODUCT DESCRIPTION', 'SHADE NAME', 'SHADE NUMBER', 'PRODUCT FACING SL', '4 DIGITS',
]

ROWS = [
    # Standard litho YCA12345 (2 products, one will fail)
    ['YCA12345', 'MNY SUPERSTAY DISPLAY', '', 1, '12345678901', 'SUPERSTAY LIPSTICK', 'FOREST BROWN', 110, 2, 4501],
    ['YCA12345', 'MNY SUPERSTAY DISPLAY', '', 2, '12345678902', 'SUPERSTAY LIPSTICK', 'MISSING SHADE', 999, 2, 4502],
    # CUBBY litho YCA12346
    ['YCA12346', 'MNY CUBBY 3F2T FALL', 'UPC.1, UPC.2, UPC.3', 1, 'UPC.1', 'CUBBY PRODUCT', 'SHADE A', 1, 'CUBBY', ''],
    ['YCA12346', 'MNY CUBBY 3F2T FALL', 'UPC.1, UPC.2, UPC.3', 2, 'UPC.2', 'CUBBY PRODUCT', 'SHADE B', 2, 'CUBBY', ''],
    ['YCA12346', 'MNY CUBBY 3F2T FALL', 'UPC.1, UPC.2, UPC.3', 3, 'UPC.3', 'CUBBY PRODUCT', 'SHADE C', 3, 'CUBBY', ''],
    # MIXED litho YCA12347
    ['YCA12347', 'MNY MIXED DISPLAY', '', 1, '22345678901', 'GREAT LASH', 'GREAT LASH WTP', 401, 2, 7801],
    ['YCA12347', 'MNY MIXED DISPLAY', '', 2, '22345678902', 'GREAT LASH', 'CRIMSON RED', 120, 3, 7802],
    # Scanned litho YCA99999 (near-empty PDF)
    ['YCA99999', 'MNY SCANNED DISPLAY', '', 1, '32345678901', 'SCANNED PRODUCT', 'GHOST SHADE', 555, 1, 1111],
]


def make_brief():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'BRIEF'
    ws.append(COLUMNS)
    for row in ROWS:
        ws.append(row)
    path = os.path.join(OUT, 'brief_mny.xlsx')
    wb.save(path)
    print('wrote', path)


def make_pdf(name, lines, pages=1):
    doc = fitz.open()
    for p in range(pages):
        page = doc.new_page(width=595, height=842)
        y = 72
        for line in lines if p == 0 else [f'Page {p + 1}']:
            page.insert_text((72, y), line, fontsize=14)
            y += 24
    path = os.path.join(OUT, name)
    doc.save(path)
    doc.close()
    print('wrote', path)


make_brief()
make_pdf('YCA12345.pdf', [
    'MAYBELLINE NEW YORK - SUPERSTAY DISPLAY',
    'L\'OREAL GROUP - FALL COLLECTION',
    '110 FOREST BROWN shade',
    '4501',
], pages=2)
make_pdf('YCA12346_v2.pdf', [
    'MNY CUBBY DISPLAY 3F2T',
    'SHADE A 1 / SHADE B 2 / SHADE C 3',
])
make_pdf('YCA12347.pdf', [
    'MNY MIXED DISPLAY',
    '401 GREAT LASH WATERPROOF',
    '120 CRIMSON RED',
])
make_pdf('badname.pdf', ['THIS FILE HAS AN INVALID NAME'])
make_pdf('YCA99999.pdf', ['x'])  # < 50 chars → needs manual review
