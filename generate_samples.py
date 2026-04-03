"""Generate sample PDF purchase orders, spec sheets, and a handwritten PO image."""

import os

# --- PDF Generation using fpdf2 ---
from fpdf import FPDF

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sample_docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_po_acme():
    """Clean, professional PDF purchase order from a known customer."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "PURCHASE ORDER", ln=True, align="C")
    pdf.ln(4)

    # Company info
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 6, "FROM:", ln=False)
    pdf.cell(95, 6, "SHIP TO:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 5, "Acme Medical Devices", ln=False)
    pdf.cell(95, 5, "Acme Medical Devices", ln=True)
    pdf.cell(95, 5, "1200 Innovation Drive", ln=False)
    pdf.cell(95, 5, "Warehouse Receiving Dock B", ln=True)
    pdf.cell(95, 5, "Boston, MA 02101", ln=False)
    pdf.cell(95, 5, "1200 Innovation Drive", ln=True)
    pdf.cell(95, 5, "Contact: Sarah Chen", ln=False)
    pdf.cell(95, 5, "Boston, MA 02101", ln=True)
    pdf.cell(95, 5, "schen@acmemedical.com", ln=False)
    pdf.cell(95, 5, "", ln=True)
    pdf.cell(95, 5, "(617) 555-0142", ln=True)
    pdf.ln(6)

    # PO Details
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 240, 250)
    pdf.cell(47, 7, "PO Number", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Date", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Payment Terms", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Delivery Date", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(47, 7, "ACME-PO-2026-0412", border=1, align="C")
    pdf.cell(47, 7, "March 28, 2026", border=1, align="C")
    pdf.cell(47, 7, "Net 30", border=1, align="C")
    pdf.cell(47, 7, "April 15, 2026", border=1, align="C", ln=True)
    pdf.ln(8)

    # Line items header
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 240, 250)
    pdf.cell(15, 7, "Line", border=1, fill=True, align="C")
    pdf.cell(25, 7, "Part #", border=1, fill=True, align="C")
    pdf.cell(70, 7, "Description", border=1, fill=True)
    pdf.cell(20, 7, "Qty", border=1, fill=True, align="C")
    pdf.cell(25, 7, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Total", border=1, fill=True, align="R", ln=True)

    # Line items
    items = [
        ("1", "11195", "1-Way Stopcock, Female Luer Lock", "500", "$2.57", "$1,285.00"),
        ("2", "99720", "2-Way Stopcock, 2 Female Luer Locks", "200", "$3.11", "$622.00"),
        ("3", "11455", "Luer Lock Connector, Gamma Stable", "300", "$1.08", "$324.00"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for item in items:
        pdf.cell(15, 7, item[0], border=1, align="C")
        pdf.cell(25, 7, item[1], border=1, align="C")
        pdf.cell(70, 7, item[2], border=1)
        pdf.cell(20, 7, item[3], border=1, align="C")
        pdf.cell(25, 7, item[4], border=1, align="R")
        pdf.cell(30, 7, item[5], border=1, align="R", ln=True)

    # Total
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(130, 7, "", border=0)
    pdf.cell(25, 7, "TOTAL:", border=1, align="R")
    pdf.cell(30, 7, "$2,231.00", border=1, align="R", ln=True)
    pdf.ln(8)

    # Notes
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Notes:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Please include Certificate of Compliance with shipment.", ln=True)
    pdf.cell(0, 5, "All parts must comply with ISO 80369-7.", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc1_sales_orders", "po_acme_medical.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_po_bioflow():
    """PO with vague descriptions — no part numbers, just product descriptions."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "BioFlow Systems Inc.", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "2500 Research Parkway, Atlanta, GA 30301", ln=True)
    pdf.cell(0, 5, "Contact: James Rodriguez | jrodriguez@bioflowsys.com", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Purchase Order #BFS-7891", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Date: March 30, 2026    |    Terms: Net 30    |    Deliver by: April 20, 2026", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Items Requested:", ln=True)
    pdf.ln(2)

    items = [
        "25 coils of 1/4 inch silicone tubing (50 ft each) ................. $65.00/coil",
        "100 units barbed check valve for 1/4 inch tubing ................ $4.50/unit",
        "200 hydrophilic filters with luer lock connections ............... $3.50/unit",
        "500 ratchet-style pinch clamps (white) .......................... $0.65/unit",
    ]
    pdf.set_font("Helvetica", "", 10)
    for item in items:
        pdf.cell(0, 6, item, ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Shipping: Standard Ground", ln=True)
    pdf.cell(0, 6, "Special Instructions: None", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc1_sales_orders", "po_bioflow_systems.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_spec_sheet_stopcock():
    """Supplier spec sheet with wrong Qosina terminology — tests constitutional framework."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SUPPLIER SPECIFICATION SHEET", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Precision Plastics Corp", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Supplier Part Number: SP-NEW-4401", ln=True)
    pdf.cell(0, 5, "Description: 3-way valve, luer type, PC material", ln=True)
    pdf.ln(6)

    # Specs table
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 7, "Parameter", border=1, fill=True)
    pdf.cell(120, 7, "Value", border=1, fill=True, ln=True)

    specs = [
        ("Type", "Three-way valve with luer connections"),
        ("Material (Body)", "PC plastic"),
        ("Material (Handle)", "HDPE, white"),
        ("Material (Seal)", "Silicone O-ring"),
        ("Connection 1", "M Luer Lock"),
        ("Connection 2", "F Luer Lock"),
        ("Connection 3", "F Luer Lock"),
        ("Bore Size", '0.106" (2.69mm)'),
        ("Max Pressure", "29 psi"),
        ("Overall Length", '1.5" (38.1mm)'),
        ("OD", '0.19" (4.83mm)'),
        ("ID", '0.106" (2.69mm)'),
        ("Weight", "8.5g"),
        ("Manufacturing", "Clean room (ISO Class 8)"),
        ("Sterilization", "Gamma and EtO compatible"),
        ("Shelf Life", "60 months (36 months post-irradiation)"),
        ("Compliance", "ISO 80369-7"),
        ("Country of Origin", "China"),
        ("Lead Time", "45 days"),
        ("MOQ", "5,000 units"),
        ("Unit Cost", "$1.85"),
        ("Units per Case", "100"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for label, value in specs:
        pdf.cell(60, 6, label, border=1)
        pdf.cell(120, 6, value, border=1, ln=True)

    path = os.path.join(OUTPUT_DIR, "uc3_product_data", "spec_sheet_stopcock.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_spec_sheet_filter():
    """European supplier spec sheet — metric, bilingual header."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "TECHNISCHES DATENBLATT / TECHNICAL DATA SHEET", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "EuroFlex Medical GmbH", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Product: Hydrophilic Membrane Filter", ln=True)
    pdf.cell(0, 5, "Model: EFM-HF-022-LL", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(70, 7, "Specification", border=1, fill=True)
    pdf.cell(110, 7, "Value", border=1, fill=True, ln=True)

    specs = [
        ("Filter Media", "Polyethersulfone (PES)"),
        ("Pore Size", "0.22 micron"),
        ("Housing Material", "ABS"),
        ("Inlet Connection", "Female Luer Lock"),
        ("Outlet Connection", "Male Luer Lock"),
        ("Effective Filtration Area", "4.5 cm2"),
        ("Maximum Pressure", "4.0 bar (58 psi)"),
        ("Priming Volume", "0.5 mL"),
        ("Flow Rate (water)", ">40 mL/min at 1 bar"),
        ("Overall Length", "58.0mm"),
        ("Maximum Diameter", "22.0mm"),
        ("Weight", "16.0g"),
        ("ISO Compliance", "ISO 80369-7"),
        ("Manufacturing QMS", "ISO 13485"),
        ("CE Marking", "MDR 2017/745"),
        ("Biocompatibility", "ISO 10993-1"),
        ("Sterilization", "Gamma irradiation, EtO"),
        ("Shelf Life", "60 months"),
        ("Country of Origin", "Germany"),
        ("MOQ", "500 units"),
        ("Unit Price", "EUR 2.80"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for label, value in specs:
        pdf.cell(70, 6, label, border=1)
        pdf.cell(110, 6, value, border=1, ln=True)

    path = os.path.join(OUTPUT_DIR, "uc3_product_data", "spec_sheet_filter_euroflex.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_handwritten_po():
    """Generate an image that looks like a messy handwritten purchase order."""
    from PIL import Image, ImageDraw, ImageFont
    import random

    width, height = 800, 600
    img = Image.new("RGB", (width, height), "#f5f0e8")  # Yellowish paper
    draw = ImageDraw.Draw(img)

    # Try to use a decent font, fall back to default
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    ink = "#1a1a3a"  # Dark blue ink

    def wobbly_text(draw, x, y, text, f, color=ink):
        """Draw text with slight random offsets to look hand-written."""
        for i, char in enumerate(text):
            ox = random.randint(-1, 1)
            oy = random.randint(-2, 2)
            draw.text((x + ox, y + oy), char, fill=color, font=f)
            bbox = draw.textbbox((x, y), char, font=f)
            x += bbox[2] - bbox[0] + random.randint(-1, 1)

    # Add some ruled lines
    for y_line in range(80, height, 32):
        draw.line([(40, y_line), (width - 40, y_line)], fill="#c0b8a8", width=1)

    # Header
    wobbly_text(draw, 60, 30, "PURCHASE ORDER", font_large, "#1a1a3a")
    draw.line([(60, 58), (310, 58)], fill=ink, width=2)

    # Date and info
    wobbly_text(draw, 500, 30, "3/29/2026", font)
    wobbly_text(draw, 60, 85, "Summit Surgical Supply", font)
    wobbly_text(draw, 60, 115, "David Park - purchasing", font_small)
    wobbly_text(draw, 60, 140, "PO# SS-2026-088", font)

    # Items
    wobbly_text(draw, 60, 185, "Please send:", font)

    items = [
        "50x  Tuohy Borst adapter  #80330  @$8.50",
        "75x  flow control switch (blue, luer lock) @$5.90",
        "200x  roller clamps  @$0.95",
        "100x  slide clamps (white)  @$0.35",
    ]
    y = 220
    for item in items:
        wobbly_text(draw, 80, y, item, font)
        y += 35

    # Footer
    wobbly_text(draw, 60, y + 20, "Ship to: 445 Medical Center Dr", font_small)
    wobbly_text(draw, 60, y + 42, "        Charleston, SC 29403", font_small)
    wobbly_text(draw, 60, y + 72, "Need by April 25 - RUSH", font, "#8b0000")

    # Signature scribble
    points = [(60, y + 110)]
    x_pos = 60
    for _ in range(40):
        x_pos += random.randint(2, 6)
        points.append((x_pos, y + 110 + random.randint(-8, 8)))
    draw.line(points, fill=ink, width=2)
    wobbly_text(draw, x_pos + 10, y + 102, "- D. Park", font_small)

    path = os.path.join(OUTPUT_DIR, "uc1_sales_orders", "po_handwritten_summit_surgical.png")
    img.save(path)
    print(f"Generated: {path}")


def generate_handwritten_po_clean():
    """Generate a cleaner handwritten PO — readable enough for Claude to match products."""
    from PIL import Image, ImageDraw, ImageFont
    import random

    width, height = 850, 650
    img = Image.new("RGB", (width, height), "#f8f5ee")
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    ink = "#1a1a3a"

    def neat_text(draw, x, y, text, f, color=ink):
        """Draw text with very slight offset — neat handwriting."""
        for char in text:
            oy = random.randint(-1, 1)
            draw.text((x, y + oy), char, fill=color, font=f)
            bbox = draw.textbbox((x, y), char, font=f)
            x += bbox[2] - bbox[0]

    # Ruled lines
    for y_line in range(75, height, 34):
        draw.line([(50, y_line), (width - 50, y_line)], fill="#d0c8b8", width=1)

    neat_text(draw, 60, 25, "PURCHASE ORDER", font_large, ink)
    draw.line([(60, 55), (280, 55)], fill=ink, width=2)
    neat_text(draw, 550, 28, "3/29/2026", font)

    neat_text(draw, 60, 80, "Summit Surgical Supply", font)
    neat_text(draw, 60, 110, "David Park - Purchasing Dept", font_small)
    neat_text(draw, 60, 135, "PO# SS-2026-088", font)

    neat_text(draw, 60, 180, "Please ship the following:", font)

    items = [
        "50x  Tuohy Borst Adapter  #80330   @ $8.50 ea",
        "75x  Flow Control Switch (blue)  #97337  @ $5.90",
        "200x  Roller Clamps  #14054   @ $0.95 ea",
        "100x  Slide Clamps (white)  #11498  @ $0.35",
    ]
    y = 220
    for item in items:
        neat_text(draw, 80, y, item, font)
        y += 38

    neat_text(draw, 60, y + 25, "Ship to: 445 Medical Center Dr", font_small)
    neat_text(draw, 60, y + 48, "         Charleston, SC 29403", font_small)
    neat_text(draw, 60, y + 80, "RUSH - Need by April 25", font, "#8b0000")
    neat_text(draw, 60, y + 110, "Terms: Net 30", font_small)

    # Signature
    points = [(60, y + 145)]
    xp = 60
    for _ in range(30):
        xp += random.randint(3, 7)
        points.append((xp, y + 145 + random.randint(-5, 5)))
    draw.line(points, fill=ink, width=2)
    neat_text(draw, xp + 10, y + 137, "- D. Park", font_small)

    path = os.path.join(OUTPUT_DIR, "uc1_sales_orders", "po_handwritten_clean.png")
    img.save(path)
    print(f"Generated: {path}")


def generate_vendor_invoice_perfect():
    """Vendor invoice that matches PO-2026-001 perfectly. Should auto-approve."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Precision Plastics Corp", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "8200 Industrial Blvd, Suite 400, Charlotte, NC 28273", ln=True)
    pdf.cell(0, 5, "Phone: (704) 555-0188  |  AP@precisionplastics.com", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "INVOICE", ln=True)
    pdf.ln(2)

    # Invoice details
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(47, 7, "Invoice #", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Date", border=1, fill=True, align="C")
    pdf.cell(47, 7, "PO Reference", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Terms", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(47, 7, "VINV-2026-001", border=1, align="C")
    pdf.cell(47, 7, "March 16, 2026", border=1, align="C")
    pdf.cell(47, 7, "PO-2026-001", border=1, align="C")
    pdf.cell(47, 7, "Net 30", border=1, align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, "Bill To:", ln=False)
    pdf.cell(95, 6, "Due Date: April 15, 2026", ln=True)
    pdf.cell(95, 5, "Qosina Corp", ln=True)
    pdf.cell(95, 5, "150-Q Executive Drive", ln=True)
    pdf.cell(95, 5, "Ronkonkoma, NY 11779", ln=True)
    pdf.ln(4)

    # Line items
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(25, 7, "Part #", border=1, fill=True, align="C")
    pdf.cell(70, 7, "Description", border=1, fill=True)
    pdf.cell(20, 7, "Qty", border=1, fill=True, align="C")
    pdf.cell(30, 7, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(35, 7, "Line Total", border=1, fill=True, align="R", ln=True)

    items = [
        ("11195", "1-Way Stopcock, Female Luer Lock", "1,000", "$2.85", "$2,850.00"),
        ("99720", "2-Way Stopcock, 2 Female Luer Locks", "500", "$3.45", "$1,725.00"),
        ("99740", "1-Way Stopcock, Female Luer Lock", "400", "$2.81", "$1,125.00"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for item in items:
        pdf.cell(25, 7, item[0], border=1, align="C")
        pdf.cell(70, 7, item[1], border=1)
        pdf.cell(20, 7, item[2], border=1, align="C")
        pdf.cell(30, 7, item[3], border=1, align="R")
        pdf.cell(35, 7, item[4], border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(115, 8, "", border=0)
    pdf.cell(30, 8, "TOTAL:", border=1, align="R")
    pdf.cell(35, 8, "$5,700.00", border=1, align="R", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Please remit payment to: Precision Plastics Corp, Account #4412-8890, Routing #053100300", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc2_ap_processing", "vendor_invoice_precision_plastics.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_vendor_invoice_discrepancy():
    """Vendor invoice for PO-2026-005 — bills for 500 units but only 480 were received."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "TechValve International", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "12 Orchard Road, #08-01, Singapore 238826", ln=True)
    pdf.cell(0, 5, "billing@techvalveintl.com  |  +65 6555 0142", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "INVOICE", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(47, 7, "Invoice #", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Date", border=1, fill=True, align="C")
    pdf.cell(47, 7, "PO Reference", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Terms", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(47, 7, "VINV-2026-005", border=1, align="C")
    pdf.cell(47, 7, "April 16, 2026", border=1, align="C")
    pdf.cell(47, 7, "PO-2026-005", border=1, align="C")
    pdf.cell(47, 7, "Net 30", border=1, align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, "Bill To: Qosina Corp", ln=True)
    pdf.cell(95, 5, "150-Q Executive Drive, Ronkonkoma, NY 11779", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(25, 7, "Part #", border=1, fill=True, align="C")
    pdf.cell(80, 7, "Description", border=1, fill=True)
    pdf.cell(20, 7, "Qty", border=1, fill=True, align="C")
    pdf.cell(25, 7, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Total", border=1, fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(25, 7, "80071", border=1, align="C")
    pdf.cell(80, 7, "Check Valve, Female Luer Lock / Male Luer Lock", border=1)
    pdf.cell(20, 7, "500", border=1, align="C")
    pdf.cell(25, 7, "$3.95", border=1, align="R")
    pdf.cell(30, 7, "$1,975.00", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(125, 8, "", border=0)
    pdf.cell(25, 8, "TOTAL:", border=1, align="R")
    pdf.cell(30, 8, "$1,975.00", border=1, align="R", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Note: Shipped 500 units per PO-2026-005. Please verify receipt and remit.", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc2_ap_processing", "vendor_invoice_techvalve_discrepancy.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_vendor_invoice_penny():
    """Vendor invoice for PO-2026-002 — $0.03 penny discrepancy from rounding."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SinoMed Components Ltd", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Building 8, Zhangjiang Hi-Tech Park, Shanghai 201203, China", ln=True)
    pdf.cell(0, 5, "accounts@sinomed-components.cn  |  +86 21 5555 0288", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "COMMERCIAL INVOICE", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(47, 7, "Invoice #", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Date", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Your PO #", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Payment", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(47, 7, "VINV-2026-002", border=1, align="C")
    pdf.cell(47, 7, "March 26, 2026", border=1, align="C")
    pdf.cell(47, 7, "PO-2026-002", border=1, align="C")
    pdf.cell(47, 7, "Net 60", border=1, align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Ship To: Qosina Corp, 150-Q Executive Drive, Ronkonkoma, NY 11779", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(25, 7, "Item", border=1, fill=True, align="C")
    pdf.cell(80, 7, "Description", border=1, fill=True)
    pdf.cell(20, 7, "Qty", border=1, fill=True, align="C")
    pdf.cell(25, 7, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Amount", border=1, fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(25, 7, "11096", border=1, align="C")
    pdf.cell(80, 7, "Female Luer Lock, Tubing Port, Clear", border=1)
    pdf.cell(20, 7, "5,000", border=1, align="C")
    pdf.cell(25, 7, "$0.4501", border=1, align="R")
    pdf.cell(30, 7, "$2,250.03", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(125, 8, "", border=0)
    pdf.cell(25, 8, "TOTAL:", border=1, align="R")
    pdf.cell(30, 8, "$2,250.03", border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Wire transfer to: SinoMed Components Ltd, HSBC Shanghai, SWIFT: HSBCSGSG", ln=True)
    pdf.cell(0, 5, "Account: 400-123456-001  |  Reference: VINV-2026-002", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc2_ap_processing", "vendor_invoice_sinomed_penny.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_payment_remittance():
    """Payment remittance from MedLine — $1,345 that doesn't exactly match their invoices."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MedLine Innovations", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "750 Technology Way, Suite 200, Chicago, IL 60601", ln=True)
    pdf.cell(0, 5, "AP Department  |  ap@medlineinnovations.com", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "REMITTANCE ADVICE", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 7, "Payment Date", border=1, fill=True, align="C")
    pdf.cell(60, 7, "Check Number", border=1, fill=True, align="C")
    pdf.cell(60, 7, "Total Payment", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(60, 7, "March 28, 2026", border=1, align="C")
    pdf.cell(60, 7, "#7892", border=1, align="C")
    pdf.cell(60, 7, "$1,345.00", border=1, align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Payee: Qosina Corp", ln=True)
    pdf.cell(0, 6, "Customer Account: CUST-003 / MedLine Innovations", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Invoices covered by this payment:", ln=True)
    pdf.ln(2)

    pdf.set_fill_color(240, 240, 240)
    pdf.cell(50, 7, "Invoice #", border=1, fill=True, align="C")
    pdf.cell(40, 7, "Invoice Date", border=1, fill=True, align="C")
    pdf.cell(40, 7, "Invoice Amount", border=1, fill=True, align="R")
    pdf.cell(40, 7, "Amount Paid", border=1, fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 7, "CINV-2026-006", border=1, align="C")
    pdf.cell(40, 7, "Nov 10, 2025", border=1, align="C")
    pdf.cell(40, 7, "$1,012.50", border=1, align="R")
    pdf.cell(40, 7, "$1,012.50", border=1, align="R", ln=True)

    pdf.cell(50, 7, "CINV-2026-007", border=1, align="C")
    pdf.cell(40, 7, "Jan 12, 2026", border=1, align="C")
    pdf.cell(40, 7, "$337.50", border=1, align="R")
    pdf.cell(40, 7, "$332.50", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(130, 8, "", border=0)
    pdf.cell(40, 8, "$1,345.00", border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Note: Deducted $5.00 from CINV-2026-007 for damaged goods on order ORD-2025-0106.", ln=True)
    pdf.cell(0, 5, "Please apply payment and adjust balance accordingly.", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc2_ap_processing", "payment_remittance_medline.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


    # --- NEW UC1: Email body PO (plain text, no formatting) ---
def generate_po_email_body():
    """PO as a plain email — no PDF structure, informal."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", "", 11)

    lines = [
        "From: jwalsh@pacificcoastmed.com",
        "To: orders@qosina.com",
        "Subject: New Order - Pacific Coast Medical Supplies",
        "Date: April 1, 2026",
        "",
        "Hi Qosina team,",
        "",
        "We'd like to order the following. We're a new customer,",
        "Pacific Coast Medical Supplies in San Diego.",
        "",
        "  - 50 needleless injection sites (swabbable, luer",
        "    lock both ends) at $6.75 each",
        "  - 100 extension lines, 6 inch, female to male luer",
        "    lock, at $2.10 each",
        "  - 25 Y-connectors with spin lock at $4.50 each",
        "  - 500 of the clear female luer lock connectors",
        "    with tubing port, part 11096, at $0.45",
        "",
        "Ship to:",
        "  Pacific Coast Medical Supplies",
        "  8800 Miramar Road Suite 200",
        "  San Diego, CA 92126",
        "",
        "Net 30 terms if possible. Need delivery by end of",
        "April.",
        "",
        "Thanks,",
        "Jennifer Walsh",
        "Purchasing Director",
        "(858) 555-0199",
    ]

    for line in lines:
        pdf.cell(0, 5.5, line, ln=True)

    path = os.path.join(OUTPUT_DIR, "uc1_sales_orders", "po_email_pacific_coast.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_po_wrong_parts():
    """PO with outdated/wrong part numbers — tests error handling."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "PURCHASE ORDER", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Precision Diagnostics Inc", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Robert Taylor | rtaylor@precisiondiag.com", ln=True)
    pdf.cell(0, 5, "PO Number: PD-2026-0055", ln=True)
    pdf.cell(0, 5, "Date: April 2, 2026  |  Terms: Net 30", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(25, 7, "Part #", border=1, fill=True, align="C")
    pdf.cell(80, 7, "Description", border=1, fill=True)
    pdf.cell(20, 7, "Qty", border=1, fill=True, align="C")
    pdf.cell(25, 7, "Price", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Total", border=1, fill=True, align="R", ln=True)

    items = [
        ("28213", "Hydrophilic Filter, Luer Lock", "150", "$3.50", "$525.00"),
        ("99999", "Three-Way Stopcock (DISCONTINUED)", "100", "$5.20", "$520.00"),
        ("33061", "Extension Line 6 inch", "300", "$2.10", "$630.00"),
        ("XXXXZ", "Barbed Y-Connector 1/4 inch", "50", "$4.25", "$212.50"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for item in items:
        pdf.cell(25, 7, item[0], border=1, align="C")
        pdf.cell(80, 7, item[1], border=1)
        pdf.cell(20, 7, item[2], border=1, align="C")
        pdf.cell(25, 7, item[3], border=1, align="R")
        pdf.cell(30, 7, item[4], border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(125, 8, "", border=0)
    pdf.cell(25, 8, "TOTAL:", border=1, align="R")
    pdf.cell(30, 8, "$1,887.50", border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Ship to: 1500 Harbor Blvd, Suite 100, Costa Mesa, CA 92626", ln=True)
    pdf.cell(0, 5, "Delivery by: April 18, 2026", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc1_sales_orders", "po_wrong_parts_precision_diag.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


# --- NEW UC2: Vendor invoice with price discrepancy ---
def generate_vendor_invoice_price_mismatch():
    """Vendor invoice where unit price differs from PO price."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Allied Silicone Products", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "9400 Silicon Drive, Fremont, CA 94538", ln=True)
    pdf.cell(0, 5, "billing@alliedsilicone.com  |  (510) 555-0177", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "INVOICE", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(47, 7, "Invoice #", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Date", border=1, fill=True, align="C")
    pdf.cell(47, 7, "PO Reference", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Terms", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(47, 7, "VINV-2026-004", border=1, align="C")
    pdf.cell(47, 7, "April 10, 2026", border=1, align="C")
    pdf.cell(47, 7, "PO-2026-004", border=1, align="C")
    pdf.cell(47, 7, "Net 45", border=1, align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Bill To: Qosina Corp, 150-Q Executive Drive, Ronkonkoma, NY 11779", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(25, 7, "Part #", border=1, fill=True, align="C")
    pdf.cell(80, 7, "Description", border=1, fill=True)
    pdf.cell(20, 7, "Qty", border=1, fill=True, align="C")
    pdf.cell(25, 7, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Total", border=1, fill=True, align="R", ln=True)

    # PO says $65.00/coil but invoice says $67.50 — price increase
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(25, 7, "T1006", border=1, align="C")
    pdf.cell(80, 7, "Silicone Tubing, 50A, 1/4 ID x 3/8 OD", border=1)
    pdf.cell(20, 7, "100", border=1, align="C")
    pdf.cell(25, 7, "$67.50", border=1, align="R")
    pdf.cell(30, 7, "$6,750.00", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(125, 8, "", border=0)
    pdf.cell(25, 8, "TOTAL:", border=1, align="R")
    pdf.cell(30, 8, "$6,750.00", border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Note: Unit price reflects Q2 2026 price adjustment (+3.8%). See attached price update notice.", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc2_ap_processing", "vendor_invoice_allied_price_mismatch.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_partial_payment_no_remittance():
    """A bank statement line showing a payment with no remittance advice."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "FIRST NATIONAL BANK", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Commercial Account Transaction Detail", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Account: Qosina Corp - Operating Account #4412-00-8890", ln=True)
    pdf.cell(0, 6, "Statement Date: April 3, 2026", ln=True)
    pdf.ln(4)

    pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 7, "Date", border=1, fill=True, align="C")
    pdf.cell(35, 7, "Type", border=1, fill=True, align="C")
    pdf.cell(60, 7, "Description", border=1, fill=True)
    pdf.cell(30, 7, "Amount", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Balance", border=1, fill=True, align="R", ln=True)

    # A few transactions for context, then the mystery payment
    txns = [
        ("04/01", "WIRE OUT", "Precision Plastics Corp - PO", "-$5,700.00", "$142,350.00"),
        ("04/01", "ACH IN", "Atlantic Bioprocess - payment", "+$650.00", "$143,000.00"),
        ("04/02", "CHECK IN", "Unknown - Check #4488", "+$2,800.00", "$145,800.00"),
        ("04/03", "WIRE OUT", "Allied Silicone - PO-2026-004", "-$6,500.00", "$139,300.00"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for txn in txns:
        pdf.cell(30, 7, txn[0], border=1, align="C")
        pdf.cell(35, 7, txn[1], border=1, align="C")
        pdf.cell(60, 7, txn[2], border=1)
        pdf.cell(30, 7, txn[3], border=1, align="R")
        pdf.cell(30, 7, txn[4], border=1, align="R", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "FLAGGED ITEM - Requires Cash Application:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "04/02  CHECK IN  $2,800.00 - Check #4488 - No remittance advice on file.", ln=True)
    pdf.cell(0, 5, "Possible matches: CUST-001 (Acme Medical, open invoice $2,137.50)", ln=True)
    pdf.cell(0, 5, "                  CUST-005 (Atlantic Bioprocess, open invoice $650.00)", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc2_ap_processing", "bank_statement_mystery_payment.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_vendor_invoice_unknown_po():
    """Vendor invoice referencing a PO that doesn't exist in the system."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "MedSupply International", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "22 Commerce Way, Dublin, Ireland  |  accounts@medsupplyintl.ie", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "INVOICE", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(47, 7, "Invoice #", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Date", border=1, fill=True, align="C")
    pdf.cell(47, 7, "PO Reference", border=1, fill=True, align="C")
    pdf.cell(47, 7, "Terms", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(47, 7, "MSI-INV-8842", border=1, align="C")
    pdf.cell(47, 7, "April 5, 2026", border=1, align="C")
    pdf.cell(47, 7, "PO-2025-999", border=1, align="C")
    pdf.cell(47, 7, "Net 30", border=1, align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Bill To: Qosina Corp, Ronkonkoma, NY", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(80, 7, "Description", border=1, fill=True)
    pdf.cell(20, 7, "Qty", border=1, fill=True, align="C")
    pdf.cell(25, 7, "Unit", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Total", border=1, fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(80, 7, "Sterile IV Extension Set, 48 inch", border=1)
    pdf.cell(20, 7, "200", border=1, align="C")
    pdf.cell(25, 7, "$12.50", border=1, align="R")
    pdf.cell(30, 7, "$2,500.00", border=1, align="R", ln=True)

    pdf.cell(80, 7, "Needlefree Connector, 3-Way", border=1)
    pdf.cell(20, 7, "500", border=1, align="C")
    pdf.cell(25, 7, "$4.80", border=1, align="R")
    pdf.cell(30, 7, "$2,400.00", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 8, "", border=0)
    pdf.cell(25, 8, "TOTAL:", border=1, align="R")
    pdf.cell(30, 8, "$4,900.00", border=1, align="R", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc2_ap_processing", "vendor_invoice_unknown_po.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


# --- NEW UC3: Tubing spec with imperial measurements ---
def generate_spec_sheet_tubing():
    """Tubing spec sheet with imperial measurements — tests unit conversion."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "PRODUCT DATA SHEET", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Allied Silicone Products", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Catalog #: ASP-T5050", ln=True)
    pdf.cell(0, 5, "Platinum-Cured Silicone Tubing, 50A Durometer", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(70, 7, "Parameter", border=1, fill=True)
    pdf.cell(110, 7, "Value", border=1, fill=True, ln=True)

    specs = [
        ("Material", "Medical-grade silicone rubber"),
        ("Durometer", "50A Shore"),
        ("Inner Diameter", "3/16 inch"),
        ("Outer Diameter", "5/16 inch"),
        ("Wall Thickness", "1/16 inch"),
        ("Tensile Strength", "1,200 psi"),
        ("Elongation", "400%"),
        ("Color", "Translucent"),
        ("Biocompatibility", "USP Class VI, ISO 10993"),
        ("Sterilization", "Autoclave, Gamma, EtO"),
        ("Temperature Range", "-60C to +200C"),
        ("Coil Length", "50 feet"),
        ("Packaging", "50 ft coils, individually bagged"),
        ("Country of Origin", "United States"),
        ("Lead Time", "14-21 days"),
        ("FDA Status", "FDA compliant, DMF on file"),
        ("Certifications", "USP Class VI, ISO 10993, FDA"),
        ("Tariff Code", "3917.40"),
        ("Units per Case", "10 coils"),
        ("Unit Price", "$48.00/coil"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for label, value in specs:
        pdf.cell(70, 6, label, border=1)
        pdf.cell(110, 6, value, border=1, ln=True)

    path = os.path.join(OUTPUT_DIR, "uc3_product_data", "spec_sheet_tubing_allied.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_certificate_of_analysis():
    """Certificate of Analysis — different doc type with quality test results."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "CERTIFICATE OF ANALYSIS", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Precision Plastics Corp", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "ISO 13485:2016 Certified  |  FDA Registered Facility", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(45, 7, "Product", border=1, fill=True)
    pdf.cell(140, 7, "1-Way Stopcock, Female Luer Lock, Male Luer Lock", border=1, ln=True)
    pdf.cell(45, 7, "Part Number", border=1, fill=True)
    pdf.cell(140, 7, "SP-11195-A (Qosina equivalent: #11195)", border=1, ln=True)
    pdf.cell(45, 7, "Lot Number", border=1, fill=True)
    pdf.cell(140, 7, "LOT-2026-0501", border=1, ln=True)
    pdf.cell(45, 7, "Mfg Date", border=1, fill=True)
    pdf.cell(140, 7, "March 15, 2026", border=1, ln=True)
    pdf.cell(45, 7, "Expiry Date", border=1, fill=True)
    pdf.cell(140, 7, "March 15, 2031 (60 months)", border=1, ln=True)
    pdf.cell(45, 7, "Quantity", border=1, fill=True)
    pdf.cell(140, 7, "10,000 units", border=1, ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "TEST RESULTS", ln=True)
    pdf.ln(2)

    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 7, "Test", border=1, fill=True)
    pdf.cell(40, 7, "Specification", border=1, fill=True, align="C")
    pdf.cell(40, 7, "Result", border=1, fill=True, align="C")
    pdf.cell(30, 7, "Status", border=1, fill=True, align="C", ln=True)

    tests = [
        ("Visual Inspection", "No defects", "No defects", "PASS"),
        ("Thru-Hole Diameter", "2.69mm +/- 0.05", "2.70mm", "PASS"),
        ("Burst Pressure", "> 29 psi", "42 psi", "PASS"),
        ("Handle Torque", "> 3 in-oz", "4.2 in-oz", "PASS"),
        ("Biocompatibility", "ISO 10993-1", "Compliant", "PASS"),
        ("Particulate Matter", "< 50 particles/mL", "12 particles/mL", "PASS"),
        ("Endotoxin", "< 20 EU/device", "< 0.5 EU/device", "PASS"),
        ("Sterility (pre-irrad)", "SAL 10^-6", "SAL 10^-6", "PASS"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for test in tests:
        pdf.cell(60, 6, test[0], border=1)
        pdf.cell(40, 6, test[1], border=1, align="C")
        pdf.cell(40, 6, test[2], border=1, align="C")
        pdf.cell(30, 6, test[3], border=1, align="C", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "MATERIALS:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Body: Polycarbonate (PC)  |  Handle: HDPE  |  Seal: Silicone", ln=True)
    pdf.cell(0, 5, "Connections: Female Luer Lock inlet, Male Luer Lock outlet", ln=True)
    pdf.cell(0, 5, "Compliance: ISO 80369-7", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "This certifies that the above lot has been manufactured and tested in accordance with", ln=True)
    pdf.cell(0, 5, "applicable specifications and is released for distribution.", ln=True)
    pdf.ln(4)
    pdf.cell(0, 5, "QA Manager: Dr. Li Wei  |  Date: March 20, 2026", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc3_product_data", "certificate_of_analysis_stopcock.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


def generate_catalog_page():
    """Multi-product catalog page — multiple products on one page."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "TechValve International - Product Catalog 2026", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Medical Grade Flow Control Components", ln=True, align="C")
    pdf.ln(6)

    products = [
        {
            "name": "TV-CHK-100 High-Flow Check Valve",
            "specs": [
                ("Type", "One-way check valve"),
                ("Connection", "Barbed, fits 1/4 inch ID tubing"),
                ("Material", "Acrylic body, silicone disc"),
                ("Cracking Pressure", "0.075 psi"),
                ("Max Pressure", "25 psi"),
                ("Sterilization", "Gamma, EtO, Autoclave"),
                ("Price", "$3.80/unit  |  MOQ: 100"),
            ],
        },
        {
            "name": "TV-CHK-200 Low-Pressure Check Valve",
            "specs": [
                ("Type", "One-way check valve"),
                ("Connection", "Female Luer Lock inlet, Male Luer Lock outlet"),
                ("Material", "PC body, silicone disc"),
                ("Cracking Pressure", "0.5 psi"),
                ("Max Pressure", "50 psi"),
                ("Compliance", "ISO 80369-7"),
                ("Sterilization", "Gamma, EtO"),
                ("Price", "$3.40/unit  |  MOQ: 100"),
            ],
        },
        {
            "name": "TV-FLO-300 Precision Flow Regulator",
            "specs": [
                ("Type", "Variable flow regulator"),
                ("Connection", "Female Luer Lock inlet, Male Luer Lock outlet"),
                ("Material", "PC, HDPE handle"),
                ("Flow Range", "0-150 mL/min"),
                ("Max Pressure", "30 psi"),
                ("Compliance", "ISO 80369-7"),
                ("Price", "$5.50/unit  |  MOQ: 50"),
            ],
        },
    ]

    for prod in products:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(0, 93, 170)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, "  " + prod["name"], border=0, fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)

        pdf.set_font("Helvetica", "", 9)
        for label, value in prod["specs"]:
            pdf.cell(40, 5, "  " + label + ":", border=0)
            pdf.cell(0, 5, value, border=0, ln=True)
        pdf.ln(4)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "All products manufactured in ISO Class 8 clean room  |  ISO 13485 certified  |  Country of origin: Singapore", ln=True)
    pdf.cell(0, 4, "Contact: sales@techvalveintl.com  |  +65 6555 0142", ln=True)

    path = os.path.join(OUTPUT_DIR, "uc3_product_data", "catalog_page_techvalve.pdf")
    pdf.output(path)
    print(f"Generated: {path}")


if __name__ == "__main__":
    # Ensure subdirs exist
    for d in ["uc1_sales_orders", "uc2_ap_processing", "uc3_product_data"]:
        os.makedirs(os.path.join(OUTPUT_DIR, d), exist_ok=True)

    # UC1
    generate_po_acme()
    generate_po_bioflow()
    generate_handwritten_po()
    generate_handwritten_po_clean()
    generate_po_email_body()
    generate_po_wrong_parts()
    # UC2
    generate_vendor_invoice_perfect()
    generate_vendor_invoice_discrepancy()
    generate_vendor_invoice_penny()
    generate_payment_remittance()
    generate_vendor_invoice_price_mismatch()
    generate_partial_payment_no_remittance()
    generate_vendor_invoice_unknown_po()
    # UC3
    generate_spec_sheet_stopcock()
    generate_spec_sheet_filter()
    generate_spec_sheet_tubing()
    generate_certificate_of_analysis()
    generate_catalog_page()
    print(f"\nAll samples generated in {OUTPUT_DIR}/")
