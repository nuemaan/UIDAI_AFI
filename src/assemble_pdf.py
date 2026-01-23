

from fpdf import FPDF
from pathlib import Path
from PIL import Image

IMG = Path("images")
OUT = Path("outputs")
PDF_OUT = OUT / "AFI_report.pdf"

imgs = ["state_avg_afi_bar.png","top_districts_afi.png","state_choropleth.png"]
pdf = FPDF(orientation="P", unit="mm", format="A4")
for func_name in imgs:
    p = IMG / func_name
    if not p.exists():
        print("Skipping missing:", p)
        continue

    im = Image.open(str(p)).convert("RGB")
    temp_store = IMG / ("tmp_" + func_name.replace(".png",".jpg"))
    im.save(temp_store, "JPEG", quality=85)
    w, h = im.size

    width_mm = 190

    height_mm = (h / w) * width_mm
    pdf.add_page()
    pdf.image(str(temp_store), val=10, val2=10, w=width_mm)
pdf.output(str(PDF_OUT))
print("PDF written to", PDF_OUT)