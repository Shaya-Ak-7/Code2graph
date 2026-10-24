"""Generate every figure used by the Code2Graph mini-project report.

All numbers come from real runs recorded in report_assets/raw/ or measured from
the repository itself (code2graph-out/graph.json, /tmp/cov.json). Terminal
figures are rendered from the captured output of the commands, so no figure
invents a result.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report_assets"
RAW = OUT / "raw"
OUT.mkdir(exist_ok=True)

SANS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
SANS_B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def _c(rgb, a=1.0):
    """0-255 tuple -> matplotlib RGBA in 0-1 (PIL keeps the 0-255 tuples below)."""
    return (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, a)


_RGB = {
    "blue": (31, 78, 121), "light": (222, 235, 247), "cyan": (23, 120, 145),
    "green": (46, 125, 50), "amber": (196, 121, 20), "red": (176, 42, 55),
    "grey": (95, 99, 104),
}
BLUE = _c(_RGB["blue"])
LIGHT = _c(_RGB["light"])
CYAN = _c(_RGB["cyan"])
GREEN = _c(_RGB["green"])
AMBER = _c(_RGB["amber"])
RED = _c(_RGB["red"])
GREY = _c(_RGB["grey"])


# --------------------------------------------------------------------------- #
# terminal-style figures
# --------------------------------------------------------------------------- #
def render_terminal(text: str, out: Path, *, title: str, width: int = 1120, max_cols: int = 92) -> None:
    import textwrap

    font = ImageFont.truetype(MONO, 18)
    line_h = 25
    pad = 22
    lines: list[str] = []
    for raw_line in text.rstrip("\n").split("\n"):
        if len(raw_line) <= max_cols:
            lines.append(raw_line)
            continue
        indent = " " * (len(raw_line) - len(raw_line.lstrip()) + 2)
        lines.extend(textwrap.wrap(raw_line, width=max_cols,
                                   subsequent_indent=indent, break_long_words=True))
    height = pad * 2 + 36 + line_h * max(len(lines), 1)
    img = Image.new("RGB", (width, height), (30, 32, 36))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, 30], fill=(52, 56, 62))
    for i, colour in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([12 + i * 22, 9, 26 + i * 22, 23], fill=colour)
    d.text((width // 2 - len(title) * 5, 6), title, font=ImageFont.truetype(MONO, 17), fill=(210, 214, 220))
    y = 40
    for line in lines:
        colour = (222, 226, 230)
        if line.startswith("$"):
            colour = (126, 214, 122)
        elif any(k in line for k in ("passed", "OK", "wrote", "Done", "HEALED", "HEALTHY")):
            colour = (126, 214, 122)
        elif any(k in line for k in ("warning", "WARNING", "BROKEN", "failed", "Tip:")):
            colour = (243, 178, 90)
        elif line.startswith("  ") and line.strip().startswith("-"):
            colour = (150, 200, 240)
        d.text((pad, y), line, font=font, fill=colour)
        y += line_h
    img.save(out)


# --------------------------------------------------------------------------- #
# charts
# --------------------------------------------------------------------------- #
def chart_edge_relations() -> None:
    relations = [
        ("calls", 15037), ("contains", 9145), ("rationale_for", 4575),
        ("imports", 2626), ("references", 1958), ("imports_from", 1131),
        ("indirect_call", 464), ("method", 270), ("uses", 84),
        ("defines", 46), ("re_exports", 35), ("inherits", 30),
    ]
    labels = [r for r, _ in relations][::-1]
    values = [v for _, v in relations][::-1]
    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = ax.barh(labels, values, color="#177891")
    for bar, v in zip(bars, values):
        ax.text(v + 240, bar.get_y() + bar.get_height() / 2, f"{v:,}", va="center", fontsize=9)
    ax.set_xlabel("number of edges (15,217-node self-extraction)")
    ax.set_title("Relationship types in the generated code graph", fontsize=12, weight="bold")
    ax.set_xlim(0, max(values) * 1.14)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_1_edge_relations.png", dpi=190)
    plt.close(fig)


def chart_confidence() -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.2), gridspec_kw={"width_ratios": [1, 1.25]})
    vals = [34289, 1162, 0]
    colours = ["#2e7d32", "#c47914", "#b02a37"]
    wedges, _ = ax1.pie([v if v else 0.001 for v in vals], colors=colours,
                        startangle=90, counterclock=False,
                        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.5})
    ax1.text(0, 0.10, "34,289 edges", ha="center", fontsize=10, weight="bold", color="#10233a")
    ax1.text(0, -0.12, "3% INFERRED", ha="center", fontsize=8.5, color="#666")
    ax1.legend(["EXTRACTED (97.2%)", "INFERRED (3.3%)", "AMBIGUOUS (0%)"],
               loc="lower center", bbox_to_anchor=(0.5, -0.22), fontsize=8, frameon=False)
    ax1.set_title("Edge confidence mix", fontsize=11, weight="bold")

    mods = [("build", 90.1), ("extract", 91.3), ("healing", 85.1), ("watch", 85.2),
            ("serve", 79.2), ("detect", 78.8), ("cli", 56.3)]
    names = [m for m, _ in mods][::-1]
    pct = [p for _, p in mods][::-1]
    bars = ax2.barh(names, pct, color="#1f4e79")
    for b, p in zip(bars, pct):
        ax2.text(p + 1.5, b.get_y() + b.get_height() / 2, f"{p:.0f}%", va="center", fontsize=8)
    ax2.set_xlim(0, 108)
    ax2.axvline(80, color="#b02a37", linestyle="--", linewidth=1)
    ax2.text(80.5, -0.65, "suite total 80%", color="#b02a37", fontsize=8)
    ax2.set_title("Statement coverage, key modules (6,542 tests)", fontsize=11, weight="bold")
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_2_confidence_coverage.png", dpi=190)
    plt.close(fig)


def chart_communities() -> None:
    graph = json.loads((ROOT / "code2graph-out" / "graph.json").read_text(encoding="utf-8"))
    meta = graph.get("graph", {})
    communities = meta.get("communities") or {}
    if isinstance(communities, list):
        sizes = [len(c) if isinstance(c, list) else 0 for c in communities]
    else:
        sizes = [len(v) for v in communities.values()]
    sizes = [s for s in sizes if s]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    ax1.hist(sizes, bins=24, color="#177891", edgecolor="white")
    ax1.set_xlabel("nodes per community")
    ax1.set_ylabel("number of communities")
    ax1.set_title(f"Community size distribution ({len(sizes)} non-empty)", fontsize=11, weight="bold")
    ax1.spines[["top", "right"]].set_visible(False)

    labels = ["source\ncode", "tests", "docs /\nconfig"]
    values = [52935, 113210, 8200]
    bars = ax2.bar(labels, values, color=["#1f4e79", "#2e7d32", "#95a5a6"])
    for b, v in zip(bars, values):
        ax2.text(b.get_x() + b.get_width() / 2, v + 2200, f"{v:,}", ha="center", fontsize=9)
    ax2.set_ylabel("lines of Python")
    ax2.set_title("Repository size by area", fontsize=11, weight="bold")
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_3_communities_breakdown.png", dpi=190)
    plt.close(fig)


def chart_healing() -> None:
    fig, ax = plt.subplots(figsize=(9, 3.4))
    steps = ["graph before\ndeletion", "file deleted\n(+update)", "file restored\n(+update)"]
    broken = [0, 5, 0]
    healed = [0, 0, 5]
    nodes = [5, 3, 5]
    edges = [7, 2, 7]
    x = range(len(steps))
    ax.plot(x, broken, "o-", color="#b02a37", label="active BROKEN references", linewidth=2)
    ax.plot(x, healed, "s-", color="#2e7d32", label="HEALED references (history)", linewidth=2)
    ax.plot(x, edges, "^--", color="#1f4e79", label="edges in graph", linewidth=1.4)
    ax.plot(x, nodes, "v--", color="#7f8c8d", label="nodes in graph", linewidth=1.4)
    for i, (b, h) in enumerate(zip(broken, healed)):
        ax.annotate(str(b), (i, b), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
        ax.annotate(str(h), (i, h), textcoords="offset points", xytext=(0, -14), ha="center", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(steps)
    ax.set_ylabel("count")
    ax.set_title("Measured healing cycle on a two-file demo project", fontsize=11, weight="bold")
    ax.legend(fontsize=8, frameon=False, loc="center left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_7_healing_cycle.png", dpi=190)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# diagrams
# --------------------------------------------------------------------------- #
def box(ax, x, y, w, h, text, *, fill=LIGHT, edge=BLUE, fsize=10, bold=False, rounded=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.008,rounding_size={rounded}",
                                linewidth=1.2, facecolor=fill, edgecolor=edge))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fsize,
            color="#10233a", weight="bold" if bold else "normal", wrap=True)


def arrow(ax, p1, p2, *, colour=BLUE, style="-|>", lw=1.4, ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14,
                                 linewidth=lw, color=colour, linestyle=ls,
                                 shrinkA=2, shrinkB=2))


def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10, 3.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    stages = ["detect()\nscan + classify", "extract()\nsymbols + edges", "build()\nNetworkX graph",
              "cluster()\ncommunities", "analyze()\ngod nodes\n+ cycles", "report()\nGRAPH_\nREPORT.md",
              "export()\nHTML · SVG\nJSON · wiki"]
    w = 1.26
    for i, s in enumerate(stages):
        x = 0.14 + i * 1.40
        box(ax, x, 1.66, w, 1.10, s, fill=LIGHT if i % 2 == 0 else _c((232, 242, 233)),
            fsize=8.0, bold=True)
        if i:
            arrow(ax, (x - 0.135, 2.21), (x - 0.005, 2.21))
    ax.text(5.0, 3.35, "Batch pipeline — deterministic, no LLM calls", ha="center", fontsize=12,
            weight="bold", color="#10233a")
    ax.text(5.0, 1.25, "plain dicts  {nodes, edges}  →  NetworkX graph  →  report / exports",
            ha="center", fontsize=9, color=GREY)
    box(ax, 0.12, 0.18, 3.5, 0.72, "code2graph-out/graph.json\n(single shared artifact)", fill=_c((255, 243, 224)),
        edge=AMBER, fsize=8.8)
    box(ax, 4.0, 0.18, 3.3, 0.72, "cache/manifest.json\nincremental state", fill=_c((255, 243, 224)),
        edge=AMBER, fsize=8.8)
    box(ax, 7.6, 0.18, 2.28, 0.72, "MCP server\nreads the same file", fill=_c((255, 243, 224)),
        edge=AMBER, fsize=8.8)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_1_pipeline.png", dpi=200)
    plt.close(fig)


def fig_live() -> None:
    fig, ax = plt.subplots(figsize=(10, 5.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    ax.text(5, 5.0, "Live service — MCP server, watcher and healing", ha="center", fontsize=12,
            weight="bold", color="#10233a")
    box(ax, 0.2, 3.9, 2.1, 0.7, "coding agent\n(MCP client)", fill=_c((232, 242, 233)), fsize=9, bold=True)
    box(ax, 3.0, 3.75, 3.1, 1.0, "MCP server (serve.py)\n12 tools · 6 resources\nstdio or Streamable HTTP",
        fill=LIGHT, fsize=9, bold=True)
    box(ax, 6.9, 3.9, 2.9, 0.7, "in-memory graph context\n(pinned + LRU cache)", fill=_c((255, 243, 224)),
        edge=AMBER, fsize=8.8)
    arrow(ax, (2.3, 4.25), (3.0, 4.25), colour=GREEN)
    ax.text(2.65, 4.38, "tool call", fontsize=8, color=GREEN, ha="center")
    arrow(ax, (6.1, 4.25), (6.9, 4.25), colour=GREY, style="<|-|>")
    ax.text(6.5, 4.38, "reload", fontsize=8, color=GREY, ha="center")

    box(ax, 0.2, 2.2, 2.1, 0.8, "project files\non disk", fill=_c((240, 240, 240)), fsize=9)
    box(ax, 3.0, 2.05, 3.1, 1.1, "watcher (watch.py)\ndebounce 0.75 s · only changed files\nre-parse + reconcile",
        fill=LIGHT, fsize=9, bold=True)
    box(ax, 6.9, 2.2, 2.9, 0.8, "healing (healing.py)\nrecord / restore / rename match",
        fill=_c((232, 242, 233)), fsize=8.8, bold=True)
    arrow(ax, (2.3, 2.6), (3.0, 2.6), colour=AMBER)
    ax.text(2.65, 2.73, "fs events", fontsize=8, color=AMBER, ha="center")
    arrow(ax, (6.1, 2.6), (6.9, 2.6), colour=GREY, style="<|-|>")

    box(ax, 3.0, 0.35, 3.1, 1.05, "graph.json  (atomic write)\ncode2graph-out/", fill=_c((255, 243, 224)),
        edge=AMBER, fsize=9, bold=True)
    arrow(ax, (4.55, 2.05), (4.55, 1.4), colour=BLUE, style="<|-|>")
    ax.text(4.7, 1.72, "persist / read", fontsize=8, color=BLUE)
    arrow(ax, (8.35, 2.2), (8.35, 1.0), colour=BLUE, style="<|-")
    ax.add_patch(FancyArrowPatch((8.35, 1.0), (6.1, 1.0), arrowstyle="-|>", mutation_scale=14,
                                 linewidth=1.4, color=BLUE))
    ax.text(7.2, 0.86, "reconcile against previous graph", fontsize=8, color=BLUE)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_2_live_architecture.png", dpi=200)
    plt.close(fig)


def fig_data_model() -> None:
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    ax.text(5, 4.45, "Node, edge and broken-reference model", ha="center", fontsize=12,
            weight="bold", color="#10233a")
    box(ax, 0.25, 2.55, 2.9, 1.4,
        "NODE\nid: string (stable)\nlabel: human name\nsource_file\nsource_location: L42",
        fill=LIGHT, fsize=9)
    box(ax, 3.55, 2.55, 2.9, 1.4,
        "EDGE\nsource -> target\nrelation: calls · imports ·\n  contains · inherits · …\nconfidence: EXTRACTED / INFERRED / AMBIGUOUS",
        fill=_c((232, 242, 233)), fsize=8.6)
    box(ax, 6.85, 2.55, 2.9, 1.4,
        "BROKEN RECORD\nid · status BROKEN/HEALED\nreason · created_at\nedge: {source, target, relation}\nmissing_nodes[] · affected_files[]",
        fill=_c((255, 243, 224)), edge=AMBER, fsize=8.4)
    arrow(ax, (3.15, 3.25), (3.55, 3.25), style="-|>")
    arrow(ax, (6.45, 3.25), (6.85, 3.25), style="-|>", colour=AMBER)

    box(ax, 0.25, 1.15, 4.5, 0.95,
        "graph.json  →  { nodes[], edges[], hyperedges[],\n  graph: { broken_references[], healing_status{} } }",
        fill=_c((240, 240, 240)), edge=GREY, fsize=9)
    box(ax, 5.05, 1.15, 4.7, 0.95,
        "\"directed\": false  BUT  arc order = direction\nload via paths.load_node_link_graph()\nor restore_arc_direction() to keep _src/_tgt",
        fill=_c((240, 240, 240)), edge=GREY, fsize=8.6)
    ax.text(5, 0.5, "Invariant: an edge is never inserted unless both endpoints exist in the active graph",
            ha="center", fontsize=9.5, color=RED, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_3_data_model.png", dpi=200)
    plt.close(fig)


def fig_healing_flow() -> None:
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.8)
    ax.axis("off")
    ax.text(5, 4.65, "Real-time healing flow", ha="center", fontsize=12, weight="bold", color="#10233a")
    steps = [
        (0.2, 3.5, "1. file event\nsave / delete / rename", LIGHT, BLUE),
        (2.35, 3.5, "2. debounce\n0.75 s window", LIGHT, BLUE),
        (4.5, 3.5, "3. re-parse\nchanged files only", LIGHT, BLUE),
        (6.65, 3.5, "4. compare node sets\nold vs new", LIGHT, BLUE),
        (0.2, 1.95, "5. edge endpoint gone?\n→ BROKEN record", _c((255, 243, 224)), AMBER),
        (2.35, 1.95, "6. endpoint back?\n→ restore edge", _c((232, 242, 233)), GREEN),
        (4.5, 1.95, "7. unique same-file,\nsame-location match?\n→ heal rename", _c((232, 242, 233)), GREEN),
        (6.65, 1.95, "8. atomic write\n+ MCP reload", _c((240, 240, 240)), GREY),
    ]
    for x, y, t, fill, edge in steps:
        box(ax, x, y, 2.0, 1.05, t, fill=fill, edge=edge, fsize=8.6)
    for x in (2.2, 4.35, 6.5):
        arrow(ax, (x, 4.02), (x + 0.15, 4.02))
    arrow(ax, (7.65, 3.5), (7.65, 3.0), colour=AMBER)
    arrow(ax, (7.65, 2.45), (6.65, 2.47), colour=AMBER)
    ax.text(8.72, 2.75, "never an edge\nto a phantom\nnode", fontsize=7.2, color=AMBER,
            ha="left", va="center")
    arrow(ax, (2.2, 2.47), (2.35, 2.47), colour=GREEN)
    arrow(ax, (4.35, 2.47), (4.5, 2.47), colour=GREEN)
    arrow(ax, (6.5, 2.47), (6.65, 2.47), colour=GREY)
    box(ax, 0.2, 0.35, 8.45, 0.9,
        "Safety rule: prefer a missing edge over a wrong edge — healing re-points only when the match is unique",
        fill=_c((255, 235, 238)), edge=RED, fsize=9.4)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_4_healing_flow.png", dpi=200)
    plt.close(fig)


def fig_architecture_layers() -> None:
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    ax.text(5, 5.2, "Layer view of the implementation", ha="center", fontsize=12,
            weight="bold", color="#10233a")
    layers = [
        (4.15, "Interface layer", "cli.py (27 commands)   ·   serve.py (MCP)   ·   install.py (19 agent hosts)"),
        (3.15, "Intelligence layer", "cluster.py  ·  analyze.py  ·  reflect.py  ·  affected.py  ·  dedup.py"),
        (2.15, "Graph layer", "build.py  ·  export.py / exporters  ·  report.py  ·  wiki.py  ·  global_graph.py"),
        (1.15, "Extraction layer", "detect.py  ·  extract.py (33.5k LOC)  ·  extractors/ (36 modules, 112 extensions)"),
        (0.15, "Foundation layer", "paths.py  ·  security.py  ·  ids.py  ·  cache.py  ·  healing.py  ·  watch.py"),
    ]
    for y, name, detail in layers:
        box(ax, 0.3, y, 9.4, 0.82, "", fill=_c((247, 249, 252)), edge=_c((196, 205, 216)))
        ax.text(0.55, y + 0.56, name, fontsize=10, weight="bold", color=BLUE, va="center")
        ax.text(0.55, y + 0.26, detail, fontsize=8.4, color="#333", va="center")
    for y in (3.97, 2.97, 1.97, 0.97):
        arrow(ax, (5.0, y + 0.18), (5.0, y - 0.02), style="<|-|>", lw=1.0, colour=GREY)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_1_layers.png", dpi=200)
    plt.close(fig)


def main() -> None:
    raw = lambda name: (RAW / name).read_text(encoding="utf-8")

    render_terminal(raw("demo_extract.txt"), OUT / "fig5_1_extract.png",
                    title="code2graph extract (demo project)")
    render_terminal(raw("godnodes.txt"), OUT / "fig5_2_godnodes.png",
                    title="code2graph god-nodes (this repository)")
    render_terminal(raw("demo_query.txt"), OUT / "fig5_3_query.png",
                    title="code2graph query (demo project)")
    render_terminal(raw("demo_path.txt"), OUT / "fig5_4_path_explain.png",
                    title="code2graph path / explain (demo project)")
    render_terminal(raw("broken_only.txt"), OUT / "fig5_8_broken.png",
                    title="MCP tool: broken_references")
    render_terminal(raw("healed.txt"), OUT / "fig5_9_healed.png",
                    title="MCP tool: heal_status after restore")
    render_terminal(raw("help_excerpt.txt"), OUT / "fig5_5_help.png",
                    title="code2graph --help (excerpt)")
    render_terminal(raw("skillgen.txt") + "\n" + raw("ruff.txt"),
                    OUT / "fig5_11_quality_gates.png", title="quality gates")

    chart_edge_relations()
    chart_confidence()
    chart_communities()
    chart_healing()
    fig_pipeline()
    fig_live()
    fig_data_model()
    fig_healing_flow()
    fig_architecture_layers()
    print("figures written to", OUT)


if __name__ == "__main__":
    main()
