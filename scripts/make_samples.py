"""Generate fake fax samples (PDF with text layer + PNG with embedded 'ghost-ocr' text for no-tesseract demos)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, PngImagePlugin
from reportlab.pdfgen import canvas
import random

FAX = """FAX TRANSMISSION  ---  PAGE 1/1
From: Haunted Hollow Furniture GmbH (FICTIONAL)
Tel: +49 000 0000   Fax: +49 000 0001
To: Topcent Hardware Sales Dept.
Ref: HH-RFQ-1313

Please offer best price for:
- 26mm mini cup hinge  4000 pcs
- 16 inch ball bearing drawer slide 45mm  900 pairs
- Edge pull 160mm matte black  1500 pcs
- Adjustable cabinet leg 100mm  8000 pcs
- Soft close door damper buffer  5000 pcs

Regards, K. Schmidt"""
out = Path(__file__).resolve().parent.parent / "samples"

def png():
    img = Image.new("L", (1240, 900), 245); d = ImageDraw.Draw(img); random.seed(13)
    for i, line in enumerate(FAX.splitlines()): d.text((60, 50 + i * 40), line, fill=20)
    for _ in range(4000): d.point((random.randrange(1240), random.randrange(900)), fill=random.randrange(80))
    img = img.filter(ImageFilter.GaussianBlur(0.6)).rotate(0.8, fillcolor=245)
    meta = PngImagePlugin.PngInfo(); meta.add_text("ghost-ocr", FAX)
    img.save(out / "rfq_fax.png", pnginfo=meta)

def pdf():
    c = canvas.Canvas(str(out / "rfq_fax.pdf")); c.setFont("Courier", 11)
    for i, line in enumerate(FAX.splitlines()): c.drawString(50, 780 - i * 18, line)
    c.save()

if __name__ == "__main__":
    png(); pdf(); print("samples written")
