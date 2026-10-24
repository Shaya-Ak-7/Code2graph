import json
from pathlib import Path

OUT = Path("report_build/out")
front = json.loads((OUT / "front.json").read_text())
MARK_IDX = {"TOC": 4487, "LOT": 4510, "LOF": 4534, "ABBR": 4564}

def batch(name):
    text = (OUT / f"front_{name}.txt").read_text(encoding="utf-8")
    s = MARK_IDX[name]
    L = len(text)
    marker_len = len(f"\u00a7\u00a7{name}\u00a7\u00a7")
    reqs = [
        {"insertText": {"location": {"index": s}, "text": text}},
        {"deleteContentRange": {"range": {"startIndex": s + L, "endIndex": s + L + marker_len}}},
        {"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": s + L},
            "paragraphStyle": {"alignment": "START", "lineSpacing": 100,
                               "spaceAbove": {"magnitude": 0, "unit": "PT"},
                               "spaceBelow": {"magnitude": 2, "unit": "PT"}},
            "fields": "alignment,lineSpacing,spaceAbove,spaceBelow"}},
        {"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": s + L - 1},
            "textStyle": {"fontSize": {"magnitude": 12, "unit": "PT"}},
            "fields": "fontSize"}},
    ]
    meta = json.loads((OUT / "front_meta.json").read_text())
    if name == "TOC":
        for a, b in meta["TOC"][1]:
            reqs.append({"updateTextStyle": {
                "range": {"startIndex": s + a, "endIndex": s + b},
                "textStyle": {"bold": True}, "fields": "bold"}})
    return {"name": name, "index": s, "length": L, "requests": reqs}

for n in ("ABBR", "LOF", "LOT", "TOC"):
    b = batch(n)
    (OUT / f"call_{n}.json").write_text(json.dumps(b["requests"], ensure_ascii=False), encoding="utf-8")
    print(n, "start", b["index"], "len", b["length"], "requests", len(b["requests"]))
