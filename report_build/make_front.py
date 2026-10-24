"""Build the batch requests that fill the contents lists with dot leaders."""
import json
from pathlib import Path
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT = Path("report_build/out")
front = json.loads((OUT / "front.json").read_text())
TEXT_W = 451.28
SIZE = 12.0
FONT = "Times-Roman"

def leader(label: str, page, width=TEXT_W - 4):
    page_s = str(page)
    target = width - stringWidth(page_s, FONT, SIZE)
    base = stringWidth(label, FONT, SIZE) + stringWidth(" ", FONT, SIZE)
    dot = stringWidth(".", FONT, SIZE)
    n = max(3, int((target - base - stringWidth(" ", FONT, SIZE)) / dot))
    return f"{label} " + "." * n + " " + page_s

def abbr_line(k, v):
    base = k + " "
    dots = int((110 - stringWidth(base, FONT, SIZE)) / stringWidth(".", FONT, SIZE))
    return f"{k} " + "." * max(3, dots) + " " + v

blocks = {}
# TOC
lines, bold_lines = [], []
for e in front["toc"]:
    idx = len("\n".join(lines)) + (1 if lines else 0)
    lines.append(leader(e["label"], e["page"]))
    if e["level"] == 1:
        bold_lines.append((idx, idx + len(lines[-1])))
blocks["TOC"] = ("\n".join(lines) + "\n", bold_lines)

lines, bold = [], []
for e in front["lot"]:
    lines.append(leader(e["label"], e["page"]))
    blocks["LOT"] = ("\n".join(lines) + "\n", [])

lines = []
for e in front["lof"]:
    lines.append(leader(e["label"], e["page"]))
blocks["LOF"] = ("\n".join(lines) + "\n", [])

lines = [abbr_line(a["k"], a["v"]) for a in front["abbr"]]
blocks["ABBR"] = ("\n".join(lines) + "\n", [])

for name, (text, bold) in blocks.items():
    (OUT / f"front_{name}.txt").write_text(text, encoding="utf-8")
    print("==", name, len(text), "chars", len(text.splitlines()), "lines", len(bold), "bold")
print(blocks["TOC"][0][:200])
print(blocks["LOT"][0][:120])
print(blocks["ABBR"][0][:120])
json.dump({k: [v[0], v[1]] for k, v in blocks.items()}, open(OUT / "front_meta.json", "w"))
