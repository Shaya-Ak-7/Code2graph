"""Turn report_src/*.txt markup into a Google-Docs build plan.

The script does four things:

1. parse the line-prefix markup into paragraph blocks,
2. lay the blocks out into the final document text and record the exact
   character range of every block (the document is built by appending, so the
   offsets are deterministic),
3. emit the styling / image / table requests that must be sent to the Google
   Docs API, as compact JSON,
4. estimate the pagination of the finished document so that the table of
   contents, list of tables and list of figures can be filled with page
   numbers.

Outputs land in report_build/out/.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "report_src"
OUT = ROOT / "report_build" / "out"

FILES = [
    "00_front.txt",
    "01_intro.txt",
    "02_literature.txt",
    "03_design.txt",
    "04_impl.txt",
    "05_results.txt",
    "06_conclusion.txt",
]

# page geometry (A4, 72 pt margins)
PAGE_W, PAGE_H, MARGIN = 595.28, 841.89, 72.0
TEXT_W = PAGE_W - 2 * MARGIN
TEXT_H = PAGE_H - 2 * MARGIN

IMG_W = 430.0          # rendered width of a terminal screenshot / diagram
LOGO_W = 90.0

# table id -> (rows, columns); kept in one place so the estimates, the build
# script and the checks agree.
TABLES = {
    "1.1": (7, 3),
    "1.2": (18, 3),
    "2.1": (9, 4),
    "3.1": (6, 3),
    "3.2": (8, 3),
    "3.3": (12, 3),
    "3.4": (13, 2),
    "3.5": (4, 3),
    "3.6": (8, 3),
    "3.7": (7, 3),
    "3.8": (8, 4),
    "4.1": (10, 2),
    "4.2": (7, 3),
    "5.1": (6, 2),
    "5.2": (9, 3),
    "5.3": (6, 4),
    "5.4": (7, 4),
    "5.5": (9, 3),
    "5.6": (6, 3),
    "A.1": (12, 3),
}

ABBREVIATIONS = [
    ("AI", "Artificial Intelligence"),
    ("API", "Application Programming Interface"),
    ("AST", "Abstract Syntax Tree"),
    ("BFS", "Breadth-First Search"),
    ("CI", "Continuous Integration"),
    ("CLI", "Command-Line Interface"),
    ("HTML", "HyperText Markup Language"),
    ("HTTP", "HyperText Transfer Protocol"),
    ("IDE", "Integrated Development Environment"),
    ("JSON", "JavaScript Object Notation"),
    ("LLM", "Large Language Model"),
    ("LOC", "Lines of Code"),
    ("MCP", "Model Context Protocol"),
    ("NFR", "Non-Functional Requirement"),
    ("PR", "Pull Request"),
    ("RAG", "Retrieval-Augmented Generation"),
    ("SDG", "Sustainable Development Goal"),
    ("SVG", "Scalable Vector Graphics"),
    ("TNR", "Times New Roman"),
    ("UI", "User Interface"),
    ("URL", "Uniform Resource Locator"),
    ("YAML", "YAML Ain't Markup Language"),
]

ACRONYMS = {
    "SDG", "SDGS", "AI", "API", "AST", "BFS", "CI", "CLI", "HTML", "HTTP",
    "IDE", "JSON", "LLM", "LOC", "MCP", "NFR", "PR", "RAG", "SVG", "TNR",
    "UI", "URL", "YAML", "CODE2GRAPH", "MCP", "CSV", "NEO4J", "FALKORDB",
    "LSP", "BM25", "BGE", "LOCOMO", "SWE-BENCH", "GRAPHML", "MD",
}


SMALL = {"a", "an", "the", "of", "for", "and", "or", "to", "in", "on", "with", "by", "as"}


def title_case(text: str) -> str:
    words = []
    for i, w in enumerate(text.split()):
        core = w.strip("()[],.:;")
        if core.upper() in ACRONYMS or any(ch.isdigit() for ch in w):
            words.append(w)
        elif i > 0 and w.lower() in SMALL:
            words.append(w.lower())
        else:
            words.append(w[:1].upper() + w[1:].lower())
    return " ".join(words)


def smart_title(text: str) -> str:
    """Title-case a heading while keeping acronyms and identifiers intact."""
    small = {"a", "an", "the", "of", "for", "and", "or", "to", "in", "on", "with", "by", "as"}
    words = text.split()
    out = []
    for i, word in enumerate(words):
        core = word.strip("()[],.:;")
        if core.upper() in ACRONYMS or any(ch.isdigit() for ch in word) and "." in word:
            out.append(word)
        elif word.isupper() and len(core) > 1:
            out.append(word.capitalize() if core not in ACRONYMS else word)
        elif i > 0 and word.lower() in small:
            out.append(word.lower())
        else:
            out.append(word[:1].upper() + word[1:].lower() if word.isupper() else word)
    return " ".join(out)


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #
def parse() -> list[dict]:
    blocks: list[dict] = []
    pending_break = False
    for name in FILES:
        for raw in (SRC / name).read_text(encoding="utf-8").split("\n"):
            line = raw.rstrip()
            if not line:
                continue
            if not line.startswith("\u00ab"):
                blocks.append({"kind": "BODY", "text": line, "src": name})
                continue
            end = line.index("\u00bb")
            tag = line[1:end]
            body = line[end + 1:]
            if tag == "PAGEBREAK":
                pending_break = True
                continue
            kind = {"COVER_TITLE": "TITLE"}.get(tag, tag)
            meta: dict = {"src": name}
            if tag == "FIG":
                path, _, caption = body.partition("|")
                blocks.append({"kind": "FIG", "text": path.strip(), "meta": meta})
                blocks.append({"kind": "CAP", "text": caption.strip(), "meta": {"fig": path.strip()}})
                continue
            if tag == "TBL":
                blocks.append({"kind": "TBL", "text": body.strip(), "meta": meta})
                continue
            if tag == "LOGO":
                blocks.append({"kind": "LOGO", "text": "", "meta": meta})
                continue
            if tag in {"TOC", "LOT", "LOF", "ABBR"}:
                blocks.append({"kind": "MARK", "text": f"\u00a7\u00a7{tag}\u00a7\u00a7", "meta": {"mark": tag}})
                continue
            if tag == "SIGBLOCK":
                blocks.append({"kind": "SPACER", "text": "", "meta": meta})
                continue
            if tag == "SIGBLOCK2":
                blocks.append({"kind": "BODY", "text": "Signature of the Guide", "meta": meta})
                blocks.append({"kind": "END", "text": "Signature of the Head of the Department",
                               "meta": meta})
                continue
            # code blocks keep their indentation verbatim
            text = body if kind == "CODE" else body.strip()
            b = {"kind": kind, "text": text, "meta": meta}
            if pending_break:
                b["page_break"] = True
                pending_break = False
            blocks.append(b)
    return blocks


PLACEHOLDER = {
    "FIG": "[figure]",
    "LOGO": "[logo]",
}


def emit_text(blocks: list[dict]) -> None:
    """Assign text and absolute start offsets; returns nothing, mutates."""
    pos = 1  # index 1 is the first character of an empty document
    for b in blocks:
        kind = b["kind"]
        if kind == "TBL":
            text = f"[TABLE {b['text']}]"
        elif kind == "MARK":
            text = b["text"]
        elif kind == "SPACER" or kind == "END":
            text = b["text"]
        elif kind in PLACEHOLDER:
            text = PLACEHOLDER[kind]
        else:
            text = b["text"]
        b["start"] = pos
        b["raw"] = text + "\n"
        b["end"] = pos + len(text) + 1
        pos = b["end"]


# --------------------------------------------------------------------------- #
# styling requests
# --------------------------------------------------------------------------- #
def para_style(b: dict, **style) -> dict:
    return {
        "updateParagraphStyle": {
            "range": {"startIndex": b["start"], "endIndex": b["end"]},
            "paragraphStyle": style,
            "fields": ",".join(style),
        }
    }


def text_style(b: dict, start_off: int = 0, end_off: int = 0, **style) -> dict:
    return {
        "updateTextStyle": {
            "range": {"startIndex": b["start"] + start_off, "endIndex": b["end"] - 1 - end_off},
            "textStyle": style,
            "fields": ",".join(style),
        }
    }


def style_requests(blocks: list[dict]) -> list[dict]:
    reqs: list[dict] = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        kind = b["kind"]
        pb = b.get("page_break", False)
        if kind == "H1":
            st = {"namedStyleType": "HEADING_1"}
            if pb:
                st["pageBreakBefore"] = True
            reqs.append(para_style(b, **st))
        elif kind == "H2":
            st = {"namedStyleType": "HEADING_2"}
            if pb:
                st["pageBreakBefore"] = True
            reqs.append(para_style(b, **st))
        elif kind == "H3":
            reqs.append(para_style(b, namedStyleType="HEADING_3"))
        elif kind == "CAP":
            reqs.append(para_style(b, alignment="CENTER", spaceAbove={"magnitude": 8, "unit": "PT"},
                                   spaceBelow={"magnitude": 3, "unit": "PT"}, keepWithNext=True))
            reqs.append(text_style(b, bold=True, fontSize={"magnitude": 11, "unit": "PT"}))
        elif kind == "CODE":
            j = i
            while j + 1 < len(blocks) and blocks[j + 1]["kind"] == "CODE":
                j += 1
            run = {"startIndex": b["start"], "endIndex": blocks[j]["end"]}
            reqs.append({
                "updateParagraphStyle": {
                    "range": run,
                    "paragraphStyle": {
                        "alignment": "START",
                        "lineSpacing": 100,
                        "spaceAbove": {"magnitude": 0, "unit": "PT"},
                        "spaceBelow": {"magnitude": 0, "unit": "PT"},
                    },
                    "fields": "alignment,lineSpacing,spaceAbove,spaceBelow",
                }
            })
            reqs.append({
                "updateTextStyle": {
                    "range": {"startIndex": run["startIndex"], "endIndex": run["endIndex"] - 1},
                    "textStyle": {
                        "weightedFontFamily": {"fontFamily": "Courier New"},
                        "fontSize": {"magnitude": 9, "unit": "PT"},
                        "bold": False,
                    },
                    "fields": "weightedFontFamily,fontSize,bold",
                }
            })
            i = j + 1
            continue
        elif kind == "BULLET":
            j = i
            while j + 1 < len(blocks) and blocks[j + 1]["kind"] == "BULLET":
                j += 1
            reqs.append({
                "createParagraphBullets": {
                    "range": {"startIndex": b["start"], "endIndex": blocks[j]["end"]},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })
            i = j + 1
            continue
        elif kind == "REF":
            j = i
            while j + 1 < len(blocks) and blocks[j + 1]["kind"] == "REF":
                j += 1
            reqs.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": b["start"], "endIndex": blocks[j]["end"]},
                    "paragraphStyle": {
                        "alignment": "START",
                        "indentStart": {"magnitude": 18, "unit": "PT"},
                        "indentFirstLine": {"magnitude": -18, "unit": "PT"},
                        "spaceBelow": {"magnitude": 4, "unit": "PT"},
                    },
                    "fields": "alignment,indentStart,indentFirstLine,spaceBelow",
                }
            })
            i = j + 1
            continue
        elif kind == "TITLE":
            reqs.append(para_style(b, alignment="CENTER", spaceAbove={"magnitude": 60, "unit": "PT"},
                                   spaceBelow={"magnitude": 12, "unit": "PT"}))
            reqs.append(text_style(b, bold=True, fontSize={"magnitude": 18, "unit": "PT"}))
        elif kind == "BOLD":
            reqs.append(para_style(b, alignment="CENTER"))
            reqs.append(text_style(b, bold=True))
        elif kind == "C":
            reqs.append(para_style(b, alignment="CENTER"))
        elif kind == "END":
            reqs.append(para_style(b, alignment="END"))
        i += 1
    return reqs


# --------------------------------------------------------------------------- #
# rough pagination, used only for the contents lists
# --------------------------------------------------------------------------- #
LINE = 1.15  # single spacing, to match the reference report


def pheight(kind: str, size: float, text: str, width: float, spacing: float) -> float:
    font = "Courier" if kind == "CODE" else "Times-Roman"
    size = 9 if kind == "CODE" else size
    if not text:
        return size * spacing + (1.0 if kind != "CODE" else 0)
    words = text.split()
    lines, cur = 1, ""
    for w in words:
        probe = (cur + " " + w).strip()
        if stringWidth(probe, font, size) <= width:
            cur = probe
        else:
            lines += 1
            cur = w
    return lines * size * spacing


def paginate(blocks: list[dict], images: dict[str, tuple[float, float]],
             front_pages: dict[str, int], toc_entries: int) -> dict:
    """Return {block_index: page} plus the page count."""
    page = 1
    y = 0.0  # consumed height on the current page
    pages: dict[int, int] = {}
    toc_lines = toc_entries + 8

    def advance(h: float) -> None:
        nonlocal page, y
        if y + h > TEXT_H and y > 0:
            page += 1
            y = 0.0
        y += h

    # front matter: cover, bonafide, acknowledgement, abstract, toc, lot, lof, abbr.
    # Those pages are accounted for here, so the front-matter blocks themselves are
    # skipped in the flow; the first chapter then starts on the next page.
    front_total = sum(front_pages.values())
    first_chapter = next(
        (i for i, b in enumerate(blocks)
         if b["kind"] == "H1" and b["text"].upper().startswith("CHAPTER")),
        len(blocks),
    )
    page = front_total
    y = 0.0

    for idx, b in enumerate(blocks):
        if idx < first_chapter:
            pages[idx] = 1
            continue
        kind = b["kind"]
        if b.get("page_break"):
            page += 1
            y = 0.0
        pages[idx] = page
        if kind in {"H1", "H2", "H3"}:
            h = pheight(kind, 12, b["text"], TEXT_W, LINE)
            h += 12 if kind == "H1" else 10 if kind == "H2" else 8
            advance(h + 4)
        elif kind == "CAP":
            advance(pheight(kind, 11, b["text"], TEXT_W, LINE) + 3)
        elif kind == "CODE":
            advance(pheight(kind, 9, b["text"], TEXT_W - 6, 1.15) + 0.5)
        elif kind in {"FIG", "LOGO"}:
            w, h = images[b["text"]]
            advance(h + 10)
        elif kind == "TBL":
            rows, _cols = TABLES[b["text"]]
            advance(rows * 18 + 8)
        elif kind == "MARK":
            advance(24)
        else:
            advance(pheight(kind, 11, b["text"], TEXT_W, LINE))
    return {"pages": pages, "total": page}


def main() -> None:
    from PIL import Image

    blocks = parse()
    emit_text(blocks)

    images: dict[str, tuple[float, float]] = {}
    for b in blocks:
        if b["kind"] in {"FIG", "LOGO"}:
            name = "logo.png" if b["kind"] == "LOGO" else b["text"]
            im = Image.open(ROOT / "report_assets" / name)
            w = LOGO_W if b["kind"] == "LOGO" else IMG_W
            images[b["text"]] = (w, w * im.size[1] / im.size[0])

    # contents entries ------------------------------------------------------ #
    toc: list[dict] = []
    lot: list[dict] = []
    lof: list[dict] = []
    idx_of_heading: list[tuple[str, int]] = []

    front_titles = {
        "BONAFIDE CERTIFICATE", "ACKNOWLEDGEMENT", "ABSTRACT", "TABLE OF CONTENTS",
        "LIST OF TABLES", "LIST OF FIGURES", "LIST OF ABBREVIATIONS",
    }
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b["kind"] == "H1" and b["text"].upper() in front_titles:
            i += 1
            continue
        if b["kind"] == "H1" and b["text"].upper().startswith("CHAPTER"):
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            label = b["text"] + "  " + (nxt["text"] if nxt and nxt["kind"] == "H1" else "")
            toc.append({"label": label, "level": 1, "block": i})
            idx_of_heading.append(("h1", i))
            i += 2
            continue
        if b["kind"] == "H1":
            toc.append({"label": b["text"].upper(), "level": 1, "block": i})
            idx_of_heading.append(("h1", i))
        elif b["kind"] == "H2":
            toc.append({"label": title_case(b["text"]), "level": 2, "block": i})
            idx_of_heading.append(("h2", i))
        elif b["kind"] == "TBL":
            cap = blocks[i - 1]["text"] if i and blocks[i - 1]["kind"] == "CAP" else b["text"]
            lot.append({"label": cap, "block": i})
        elif b["kind"] == "CAP" and b["meta"].get("fig"):
            lof.append({"label": b["text"], "block": i})
        i += 1

    # two-pass pagination: the size of the contents pages affects the body
    front = {"cover": 1, "bonafide": 1, "ack": 1, "abstract": 1, "TOC": 2, "LOT": 1, "LOF": 1, "ABBR": 1}
    for _ in range(6):
        res = paginate(blocks, images, front, len(toc))
        toc_pages = max(1, math.ceil((len(toc) + 8) / 45))
        lot_pages = max(1, math.ceil((len(lot) + 6) / 45))
        lof_pages = max(1, math.ceil((len(lof) + 6) / 45))
        new = dict(front, TOC=toc_pages, LOT=lot_pages, LOF=lof_pages)
        if new == front:
            break
        front = new
    pages = res["pages"]

    # body page numbers in the contents must refer to the estimated page,
    # not to the block index
    for entry in toc + lot + lof:
        entry["page"] = pages.get(entry["block"], 0)

    OUT.mkdir(parents=True, exist_ok=True)

    # 1. text segments ------------------------------------------------------ #
    segs, cur, cur_start = [], [], None
    for b in blocks:
        if cur_start is None:
            cur_start = b["start"]
        cur.append(b)
        if b["end"] - cur_start >= 14000:
            segs.append((cur_start, cur))
            cur, cur_start = [], None
    if cur:
        segs.append((cur_start, cur))

    meta_segments = []
    for n, (start, seg) in enumerate(segs, 1):
        text = "".join(b["raw"] for b in seg)
        (OUT / f"seg_{n:02d}.txt").write_text(text, encoding="utf-8")
        meta_segments.append({
            "n": n, "file": f"seg_{n:02d}.txt", "base": start,
            "chars": len(text), "first": seg[0]["kind"], "last": seg[-1]["kind"],
            "end": seg[-1]["end"],
        })

    # 2. styling batches ---------------------------------------------------- #
    reqs = style_requests(blocks)
    batches = [reqs[i:i + 60] for i in range(0, len(reqs), 60)]
    for n, batch in enumerate(batches, 1):
        payload = "[\n" + ",\n".join(json.dumps(r, separators=(",", ":")) for r in batch) + "\n]"
        (OUT / f"style_{n:02d}.json").write_text(payload, encoding="utf-8")

    # 3. structural pass: images then tables, both in descending order ------ #
    img_struct = []
    for b in blocks:
        if b["kind"] in {"FIG", "LOGO"}:
            name = "logo.png" if b["kind"] == "LOGO" else b["text"]
            w, h = images[b["text"]]
            img_struct.append({
                "path": f"report_assets/{name}", "name": name,
                "index": b["start"], "del": len(b["raw"]) - 1,
                "width": round(w, 1), "height": round(h, 1),
            })
    tbl_struct = []
    for b in blocks:
        if b["kind"] == "TBL":
            rows, cols = TABLES[b["text"]]
            tbl_struct.append({"id": b["text"], "index": b["start"],
                               "del": len(b["raw"]) - 1, "rows": rows, "cols": cols})

    (OUT / "structure.json").write_text(json.dumps({
        "images": sorted(img_struct, key=lambda d: -d["index"]),
        "tables": sorted(tbl_struct, key=lambda d: -d["index"]),
    }, indent=1), encoding="utf-8")

    # 4. contents ----------------------------------------------------------- #
    (OUT / "front.json").write_text(json.dumps({
        "toc": toc, "lot": lot, "lof": lof,
        "abbr": [{"k": k, "v": v} for k, v in ABBREVIATIONS],
        "pages_total": res["total"], "front": front,
    }, indent=1), encoding="utf-8")

    (OUT / "build_log.txt").write_text(
        "\n".join([
            f"blocks: {len(blocks)}",
            f"segments: {len(segs)} -> {sum(len(b['raw']) for b in blocks)} chars",
            f"style requests: {len(reqs)} in {len(batches)} batches",
            f"images: {len(img_struct)}  tables: {len(tbl_struct)}",
            f"toc entries: {len(toc)}  lot: {len(lot)}  lof: {len(lof)}",
            f"estimated pages: {res['total']}  front: {front}",
        ]), encoding="utf-8")
    print((OUT / "build_log.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
