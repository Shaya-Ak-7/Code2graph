# Reference report analysis (template to align to)

Source: Google Doc `Code2Graph_Project_Report (2)`
(`1PmcVA8wdzbPN-DXWXLZlr0_TEueLqgP0FoHQtAvLD-E`) — 48 pages, one tab, K.L.N. College
of Engineering / B.Tech AI&DS format. This file records the spec we must match and
the places the reference must be corrected for our mini-project version.

## 1. Page format (measured from the document)

| Property | Value |
| --- | --- |
| Page size | A4 — 595.28 × 841.89 pt |
| Margins | 72 pt (1 in) top / bottom / left / right |
| Header / footer margin | 36 pt (0.5 in) |
| Body font | Times New Roman, **14 pt** |
| Body line spacing | 150 % (1.5) — applied per paragraph |
| Heading font | Times New Roman 14 pt **bold** (H1 = H2 = H3 = 14 pt; hierarchy is by caps + numbering, not size) |
| Headings alignment | START (left) |
| Code / listing blocks | 1×1 table, monospaced, line spacing 100 % |
| Data tables | Grid tables, header row bold, caption **above** the table ("Table 3.4 Tools exposed by the MCP server") |
| Figures | Caption **below** the image, centred ("Figure 3.1 Code2Graph processing pipeline") |
| Section titles | ALL CAPS for H1 and H2 ("## 1.4 SCOPE OF THE PROJECT") |
| Chapter start | `# CHAPTER n` on a new page, then the chapter title as a second line |
| Numbering | `n.m` for sections, `n.m.k` for sub-sections; tables/figures `n.m`; listings `4.1`… |

## 2. Document skeleton (what the template contains)

**Front matter**
1. Cover page — title, "A PROJECT REPORT", "Submitted by", 2 students with reg. no.,
   "in partial fulfillment for the award of the degree of", "BACHELOR OF TECHNOLOGY",
   "ARTIFICIAL INTELLIGENCE & DATA SCIENCE", logo, college name + "(An Autonomous
   Institution, Affiliated to Anna University, Chennai)", "[MONTH YEAR]", repeated
   college block.
2. BONAFIDE CERTIFICATE — certified text + 2 signature blocks (HOD, Supervisor) +
   viva-voce line + INTERNAL / EXTERNAL EXAMINER row.
3. ACKNOWLEDGEMENT — 4 paragraphs (almighty, President + Principal, HOD, guide +
   staff).
4. ABSTRACT — one paragraph, ~210 words, ends with the SDG sentence.
5. TABLE OF CONTENTS — chapter/section/ subsection with page numbers.
6. LIST OF TABLES (17 tables), LIST OF FIGURES (15 figures).
7. LIST OF ABBREVIATIONS — 2-column table, 24 entries.

**Chapters**
- **1 INTRODUCTION** — 1.1 Overview · 1.2 Problem Statement · 1.3 Project Objective ·
  1.4 Scope (1.4.1 Existing System, 1.4.2 Proposed System + Table 1.1 comparison) ·
  1.5 Relevance to the Society · 1.6 SDG mapping (1.6.1…1.6.5 five SDGs + Table 1.2
  all 17 goals) · 1.7 Organization of the Report.
- **2 LITERATURE REVIEW** — 9 sections: graph representations of code (3 works),
  parsing/tooling (tree-sitter, LSP, NetworkX), community detection, retrieval for
  LLM agents (RAG, RepoCoder, SWE-bench), agent memory (MemGPT, LOCOMO/LongMemEval),
  lexical/dense/fused retrieval, MCP, summary table 2.1, research gap 2.9.
- **3 DESIGN** — 3.1 System Architecture (Figures 3.1, 3.2 + five design
  principles) · 3.2 Hardware/Software (Tables 3.1, 3.2) · 3.3 Module Specification
  (Table 3.3 + ten module sub-sections) · 3.4 Data Design (schema, confidence
  labels, edge direction, broken-edge metadata; Figures 3.3, 3.4) · 3.5 Design
  Decisions (Table 3.6) · 3.6 Functional + Non-functional Requirements (Table 3.7) ·
  3.7 Use Cases (Table 3.8).
- **4 IMPLEMENTATION** — 4.1 Environment & layout (Table 4.1) · 4.2 Install/run
  (Listings 4.1, 4.2) · 4.3 pipeline stages (Listings 4.3, 4.4) · 4.4 Adding a
  language extractor (5 steps) · 4.5 MCP server (Listing 4.5) · 4.6 Algorithms
  (three pseudocode listings 4.6–4.8) · 4.7 Security (Table 4.2) · 4.8 Testing
  strategy (Listing 4.9) · 4.9 Packaging/containers · 4.10 Source code listings.
- **5 RESULTS AND SCREENSHOTS** — 5.1 nine screenshots (Fig 5.1–5.9) · 5.2
  evaluation set-up (Table 5.1, fairness + grading rules) · 5.3 conversational
  memory (5.3.1 LOCOMO Table 5.2 + 3 charts, 5.3.2 LongMemEval-S Table 5.3 + chart) ·
  5.4 code intelligence (5.4.1 ERPNext coverage + chart, 5.4.2 INFERRED precision,
  5.4.3 temporal Table 5.4 + chart) · 5.5 cost/token economics · 5.6 functional
  testing summary (Table 5.5) · 5.7 Discussion (3 findings + limitations).
- **6 CONCLUSION** — 6.1 Conclusion (4 paragraphs) · 6.2 Future Enhancement
  (7 bullets).
- **APPENDICES** — A.1 Command reference (Table A.1), A.2 schema recap, A.3
  benchmark reproduction (Listing A.1).
- **REFERENCES** — 21 entries, **Harvard/author-date style**, numbered, journals
  with Vol./No./pp., web sources with URLs.

## 3. Gaps to fix in our version (alignment checklist)

| # | Reference says | Must become |
| --- | --- | --- |
| 1 | "A PROJECT REPORT" | **"A MINI PROJECT REPORT"** — and "mini project" in certificate, declaration, abstract, acknowledgement, chapter 1, conclusion |
| 2 | `[STUDENT NAME 1] ([REG. NO.])`, `[STUDENT NAME 2] ...` (2 students) | 3 students: AKSHaya KUMAR R S (910623108002), SENTHIL PANDIAN G S (910623108044), SACHIN J (910623108041) |
| 3 | `[MONTH YEAR]` | **NOVEMBER 2026** |
| 4 | "Submitted for the project work viva-voce examination" | "Submitted for the **mini project** work viva-voce examination" |
| 5 | Cover has logo placeholder | K.L.N. College logo (needs the image file) |
| 6 | "structural extraction ... tree-sitter and a local embedder" | tree-sitter only; no embedder is used to build the code graph (repo fact) |
| 7 | Chapter 5 figures are `[ INSERT SCREENSHOT: ... ]` placeholders | real figures: architecture/flow diagrams, generated charts, captured CLI output |
| 8 | 1.7 says "Chapter 7 lists the references" | references are unnumbered back matter |
| 9 | Benchmark numbers are repository-reported (LOCOMO/ERPNext) | keep only if labelled "repository-reported"; add our own measured results (test suite, coverage, self-extraction) as primary evidence |
| 10 | Abstract ~210 words, no mini-project wording | abstract rewritten for the mini project, with our measured numbers |
| 11 | ToC/List of Tables/Figures page numbers 1–48 | recomputed for the new document |
| 12 | 4.10 "Paste the final source code ... here" (author note left in) | real source listings, no author notes |
| 13 | References: Harvard, 21 entries | same style, extend to any added sources |
| 14 | No declaration page | add DECLARATION page (3 signatures) if the college format requires it |

## 4. Verified repo facts available for the new report

- 902 tracked files · 52,935 LOC package (55 modules + 36 extractors + 4 exporters) ·
  113,210 LOC tests (347 files) · test:source ratio 2.14:1
- Suite: **6,542 passed / 174 skipped / 0 failed** (119 s, 2 vCPU) · coverage **80 %**
  (core path 85–99 %)
- Self-extraction on this repo: **15,217 nodes / 35,451 edges in 23 s, 0 LLM calls**;
  clustering → **615 communities in 9 s**
- Edge confidence: **97 % EXTRACTED / 3 % INFERRED / 0 % AMBIGUOUS**
- Relations observed: calls 15,037 · contains 9,145 · rationale_for 4,575 ·
  imports 2,626 · references 1,958 · imports_from 1,131 · indirect_call 464 +
  19 rarer relation types
- 112 recognised extensions; 36 extractor modules; graceful degradation when an
  optional grammar is absent (7 warnings, 0 crashes)
- MCP server: 12 tools, 6 resources, stdio + Streamable HTTP, session reaper
- Skill bundles: 134 generated artifacts, `tools.skillgen --check` passes
- Known defects to disclose honestly in 5.7 (limitations): missing LICENSE files,
  undeclared PyYAML, 32 terraform tests need `tree-sitter-hcl`, CLI at 56 % coverage
