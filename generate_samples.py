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

    path = os.path.join(OUTPUT_DIR, "po_acme_medical.pdf")
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

    path = os.path.join(OUTPUT_DIR, "po_bioflow_systems.pdf")
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

    path = os.path.join(OUTPUT_DIR, "spec_sheet_stopcock.pdf")
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

    path = os.path.join(OUTPUT_DIR, "spec_sheet_filter_euroflex.pdf")
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

    path = os.path.join(OUTPUT_DIR, "po_handwritten_summit_surgical.png")
    img.save(path)
    print(f"Generated: {path}")


if __name__ == "__main__":
    generate_po_acme()
    generate_po_bioflow()
    generate_spec_sheet_stopcock()
    generate_spec_sheet_filter()
    generate_handwritten_po()
    print(f"\nAll samples generated in {OUTPUT_DIR}/")
