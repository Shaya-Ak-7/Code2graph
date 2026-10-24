# Code2Graph — full repository analysis

Static + dynamic analysis of this checkout: structure, architecture, data model,
quality evidence, measured numbers, and a ranked list of issues.

- Analyzed commit: `d1d38cc9` ("Initial commit") on `main`
- Environment: Python 3.11.2, 2 vCPU, deps installed from `pyproject.toml` (`[mcp]` extra)
- Method: full source read-through of the core modules, own AST/import/duplication
  metrics, the project's own extractor run on itself, and the complete test suite
  with coverage.

---

## 1. TL;DR

Code2Graph is a **local, deterministic code-intelligence graph builder** with three
faces on one engine:

| Face | Entry point | Purpose |
| --- | --- | --- |
| Library | `code2graph/{extract,build,cluster,analyze,report,export}.py` | files → graph → communities → report/exports |
| CLI | `code2graph <cmd>` (~30 subcommands) | extract, update, query, export, install skill bundles |
| MCP server | `code2graph-mcp` | live graph queries + a background watcher that heals references |

Verdict: **unusually mature for a "temporary-named" experimental project.** The
core invariant set (deterministic AST extraction, no phantom nodes, broken-edge
metadata instead of silent loss, incremental rebuild that never shrinks the graph
by accident) is real and is test-enforced. The weak spots are *packaging hygiene*
and *the size of two functions*, not the architecture.

---

## 2. Repository anatomy

| Area | Files | Size | Notes |
| --- | --- | --- | --- |
| Tracked files | 902 | — | single commit, 259,909 insertions |
| `code2graph/` package | 325 | 8.9 MB | 55 top-level modules + `extractors/` (36) + `exporters/` (4) |
| `tests/` | 817 | 20.6 MB | 347 `test_*.py`, 113,210 LOC, 88 fixture dirs |
| `tools/skillgen/` | 178 | 1.7 MB | build-time generator for the committed agent-skill bundles |
| `docs/` | 6 | 40 KB | thin: how-it-works, node-summaries RFC, Docker/MCP-SQLite |
| Generated skill artifacts | 134 | 2.6 MB | 16 `skill*.md` + 112 `skills/<host>/references/*.md` + 6 `always_on/*.md` |
| `uv.lock` | 1 | 1.0 MB | pinned resolution, used by CI (`--frozen`) |

Language mix: the repository is pure Python (no JS/TS app layer) — its polyglot
machinery is *input* parsers, not shipped code.

Source vs tests (Python LOC):

```
code2graph/*.py (top level)   52,935
tests/test_*.py              113,210   → test:source ratio 2.14 : 1
```

That ratio is high and matches the repo's own claim that behavior (not structure)
is what is tested.

---

## 3. Architecture

### 3.1 Pipeline

```
detect() → extract() → build() → cluster() → analyze helpers → report.generate() → export.to_*()
```

- `detect.py` (2,946 LOC): scanning, ignore rules, category/size/word stats, manifest.
- `extract.py` (9,375 LOC) + `extractors/` (36 modules, ~11k LOC): tree-sitter
  parsers per language plus shared `engine.py` config-driven core.
- `build.py` (2,687 LOC): dedupe, id canonicalization, external-stub minting,
  shrink guard, prune logic, `build_from_json` / `build_merge` / `prefix_graph_for_global`.
- `cluster.py` (453), `analyze.py` (814), `report.py` (392), `export.py` (1,411).
- `watch.py` (2,738) + `healing.py` (471): incremental rebuild and broken-reference
  lifecycle.
- `serve.py` (2,974): MCP stdio + Streamable HTTP, 12 tools, 6 resources.

The pipeline talks in plain dicts (`{nodes, edges, hyperedges}`) and NetworkX
graphs — no ORM, no DB, no service dependency. That is why the tool installs and
runs with `pip install networkx watchdog numpy rapidfuzz tree-sitter*`.

### 3.2 Data model (`code2graph-out/graph.json`)

A self-run on this repo produced:

```
nodes 15,217   edges 34,632   hyperedges 0   communities 615
```

Edge relations (before clustering): `calls` 15,037 · `contains` 9,145 ·
`rationale_for` 4,575 · `imports` 2,626 · `references` 1,958 · `imports_from` 1,131 ·
`indirect_call` 464 · `method` 270 · `inherits` 30 · `implements` 8 · + 15 rarer ones.

Confidence: **97% EXTRACTED / 3% INFERRED / 0% AMBIGUOUS** — the honesty split is
tracked per edge, and `AMBIGUOUS` is surfaced in `GRAPH_REPORT.md`.

Two details worth knowing before writing anything against the file:

1. `graph.json` is written with `"directed": false`, but arc order *is* the
   direction. Loading it with plain `node_link_graph()` re-orders endpoints and
   silently loses direction. Load through `paths.load_node_link_graph()`.
2. Broken edges are **not** in `nodes`/`edges`. They live under
   `graph.broken_references` with a reason, a missing-node snapshot, and
   `HEALED` history; `graph.healing_status` summarises per file.

### 3.3 Watcher + healing (the differentiator)

`serve.py` starts `watch.py` per project. Save/create/delete/rename events are
debounced, only changed files are re-parsed (unchanged AST is replayed as read-only
resolution context via `resolution_context_nodes/edges`), the result is reconciled
against the previous graph, and the write is atomic. If a node disappears, edges
that pointed at it are recorded as `BROKEN` rather than dropped; when the node
returns (or a uniquely-matching replacement appears at the same file+location for a
rename), `healing.reconcile_healing()` restores the edge and marks the record
`HEALED`.

Evidence it actually works: `healing.py` is 85% covered and the linked
`tests/test_healing.py`, `test_watch*.py`, `test_broken_*` suites assert the
delete → broken → restore cycle, not just the happy path.

### 3.4 Language coverage

`detect.CODE_EXTENSIONS` lists **112 extensions**; `_DISPATCH` in `extract.py`
routes them (plus a shebang table for extension-less scripts). Roughly 20 families
are first class and local (python, js/ts/tsx, go, rust, java, c/cpp, c#, kotlin,
scala, php, ruby, swift, lua, bash, json, markdown, yaml-ish configs, …), with
optional grammars for terraform/pascal/ocaml/commonlisp/solidity/vbnet/r/erlang/
robot/dm/sql. Missing optional grammars never crash the run — they emit a
per-extension warning and contribute 0 nodes (verified: 7 `.sql`, 1 `.dm`,
1 `.erl`, 1 `.r`, 1 `.sol`, 1 `.vb`, 2 robot files in this repo's own scan).

### 3.5 CLI and MCP surfaces

- CLI (`cli.py`, 5,039 LOC; 27 dispatch branches): `extract`, `update`, `watch`, `query`, `path`,
  `explain`, `affected`, `god-nodes`, `export {html,svg,graphml,obsidian,wiki,neo4j,falkordb,callflow-html}`,
  `merge-graphs`, `merge-driver`, `global`, `prs`, `reflect`, `save-result`,
  `diagnose`, `tree`, `benchmark`, `cache-check`, `merge-chunks`, `merge-semantic`,
  plus 19 `install <platform>` variants.
- MCP (`serve.py`): tools `query_graph`, `get_node`, `get_neighbors`,
  `get_community`, `god_nodes`, `graph_stats`, `shortest_path`, `broken_references`,
  `heal_status`, `list_prs`, `get_pr_impact`, `triage_prs`; resources
  `code2graph://{report,stats,god-nodes,surprises,audit,questions}`.
  HTTP transport is opt-in, defaults to `127.0.0.1`, warns when binding `0.0.0.0`
  without `--api-key`, and has a session reaper.

---

## 4. Quality evidence (measured, not claimed)

### 4.1 Test suite

```
6542 passed, 174 skipped, 0 failed  in 119 s   (2 vCPU)
coverage: 80%  (40,724 statements, 95 files measured)
```

- Collection: 6,716 tests from 347 files.
- The suite is fast because it avoids network and uses tmp dirs (confirmed: no
  external sockets, `conftest.py` isolates env).
- Skips are optional-dependency / platform gates, not disabled assertions.

Lowest-covered modules (all are optional-grammar or side-feature surfaces):

| Module | Coverage | Why |
| --- | --- | --- |
| `cross_repo_types.py`, `manifest.py` | 0% | no direct test; tiny/passive |
| `extractors/ocaml.py` | 1.8% | grammar not installed here |
| `extractors/commonlisp.py` | 3.1% | grammar not installed here |
| `pg_introspect.py` | 9.1% | needs live PostgreSQL |
| `extractors/{vbnet,solidity,erlang,r}` | 10–12% | optional grammars |
| `extractors/{robot,sql}` | 23–27% | optional parsers |
| `prs.py` | 36% | GitHub API surface, mocked only |
| `cli.py` | 56% | 27 dispatch branches + install variants |

Everything on the core path is 85–99%: `extract` 91, `engine` 91, `build` 90,
`analyze` 95, `watch` 85, `healing` 85, `paths` 86, `report` 96, `wiki` 99,
`scip_ingest` 99. The weakest core modules are `serve` 79 and `detect` 79.

### 4.2 Lint / type / generated-artifact gates

| Gate | Result |
| --- | --- |
| `ruff` with the committed baseline (`E9,F63,F7,F82`) | clean |
| `ruff --select F,E9,B` (broader, not enforced) | 134 findings: 45 `B023` (loop-variable closures), 24 `B905` (`zip` without `strict`), 22 `F401` unused imports, 17 `B007`, 15 `F541`, 4 `F841`, 3 `B904`, 2 `B005`, 1 `F811`, 1 `F402` |
| `python -m tools.skillgen --check` | OK — 134 artifacts match source fragments |
| `pyright` | configured in `pyproject.toml`, **never run in CI** |
| `bandit`, `pip-audit` | in CI but `continue-on-error: true` → non-blocking |

### 4.3 Self-extraction (the tool on its own source)

```
566 code files → 15,217 nodes / 35,451 edges, 23 s, 0 API calls
615 communities after clustering, 9 s
```

God nodes (highest degree) — a good map of the hot path:

```
extract() 863 · build_from_json() 264 · _make_id() 231 · _read_text() 227
_rebuild_code() 220 · detect() 148 · dispatch_command() 141 · _file_stem() 127
deduplicate_entities() 116 · build_merge() 106 · main() 103 · extract_js() 96
```

Internal import fan-in: `paths` (20), `security` (19), `build` (11), `extractors`
(10), `detect` (9), `ids` (6). Fan-out: `cli` (32), `watch` (14), `serve` (9).
`paths.py` and `security.py` being the two most-imported modules is the sign of a
healthy "shared primitives, not shared state" layout.

---

## 5. Findings (ranked)

### P0 — packaging/licensing defects

1. **`LICENSE`, `LICENSE-MIT`, `NOTICE` do not exist**, yet `pyproject.toml`
   declares `license-files = ["LICENSE", "LICENSE-MIT", "NOTICE"]` and README says
   "See LICENSE, LICENSE-MIT, and NOTICE". `python -m build --wheel` succeeds but
   prints `Pattern 'NOTICE' did not match any files`, and the wheel ships **no
   license text**. Declaring `Apache-2.0` while referencing an MIT license file is
   also legally ambiguous.
2. **`pyyaml` is an undeclared runtime dependency.** `extractors/markdown.py` does
   `import yaml` and silently falls back to a flat parser when it is missing
   (`_parse_frontmatter_fallback` drops nested keys). In a clean
   `pip install -e '.[mcp]'` — exactly what the README instructs — this fails
   `tests/test_languages.py::test_markdown_nested_frontmatter_survives` and quietly
   degrades frontmatter in graphs. Verified: fails without PyYAML, passes with it.

### P1 — test/CI environment gaps

3. **Full suite needs optional extras that the docs do not mention.** First run in a
   clean `[mcp]` venv: `32 failed` — *all* in `test_terraform*.py`, because
   `tree-sitter-hcl` lives only in the `dev` group / `terraform` extra. Installing
   it turned 41/41 green. Same class of gap: `tree-sitter-ocaml`,
   `tree-sitter-commonlisp`, `tree-sitter-language-pack` (r, erlang),
   `tree-sitter-solidity`, `tree-sitter-vb-dotnet`, `tree-sitter-dm`,
   `robotframework`. CI hides this by using `uv sync --all-extras`.
4. **CI does not gate quality.** `bandit` and `pip-audit` are `continue-on-error`;
   there is no ruff run, no pyright run, no coverage floor, no build-wheel smoke
   test. The only hard gates are pytest and the skillgen drift check — both strong,
   but they cannot catch the licensing/packaging defects above.

### P2 — drift and versioning

5. **Version inconsistency:** `pyproject.toml` says `0.1.0`; `SECURITY.md` says
   "Latest 0.9.x"; `CHANGELOG.md` has only "Unreleased"; no tags in this checkout.
   There is no visible release procedure.
6. **Name/URL drift:** `pyproject.toml` URLs, `CONTRIBUTING.md` clone instructions,
   the CLI `--help` banner, the installer banner and the wiki footer all still point
   at `Shaya-Ak-7/knowledge-graph-7`, while the package, repo and docs say
   Code2Graph. README explicitly calls the name temporary — the URLs were not
   migrated with the rename.
7. **Single-commit history.** 259k insertions in one commit with no review trail.
   >1,200 `#NNNN` comments reference an upstream issue numbering that does not
   exist in this repository's history, so the design rationale in code is
   unverifiable from here (the comments themselves are excellent, though).

### P3 — maintainability hot spots

8. **Two functions are effectively modules:**
   - `extractors/engine.py:4451 _extract_generic()` — **3,944 lines**
   - `cli.py:1138 dispatch_command()` — **3,902 lines**
   - then `engine.py:4692 walk()` 2,155, `extract.py:7596 extract()` 1,692,
     `engine.py:7120 walk_calls()` 1,039, `watch.py:1561 _rebuild_code()` 942,
     `serve.py:1961 _build_server()` 723, `build.py:1029 build_from_json()` 695.
   - 63 functions > 200 lines, 139 > 100; mean 43.5; 1,916 functions total.
   These are branch-dense dispatch tables; a bug fix inside them is hard to review
   and hard to unit-test (hence `cli.py` at 56% coverage).
9. **Extractor scaffolding is copy-pasted by policy.** `add_node` is defined 32
   times, `add_edge` 31, `walk` 24, `walk_calls` 14; 11 groups of *byte-identical*
   bodies (`add_node()` ×10, `add_edge()` ×4, `ensure_named_node()` ×4). This is
   deliberate — `extractors/MIGRATION.md` mandates byte-identical moves to prove
   behavior preservation while splitting `extract.py` — but it should be
   de-duplicated once the migration finishes.
10. **231 `except Exception` blocks** (no bare `except:`). Correct instinct for a
    parser that must never crash a scan, but there is no marker convention to
    distinguish "resilience" from "swallowed bug" — `# noqa` is used 54 times and
    `type: ignore` 10 times, both without rationale tags.
11. **Documentation thin spots:** `docs/` has only 3 real documents;
    `ARCHITECTURE.md` is good and is *test-enforced* (`tests/test_architecture_doc.py`
    imports every symbol it names — a genuinely nice pattern).

### 5.1 What is genuinely strong

- **Determinism:** code is never sent to a model for structural indexing; LLM use is
  opt-in and separate. The graph is reproducible offline in ~23 s for 566 files.
- **No phantom nodes / no silent loss:** unresolved edges become `BROKEN` records
  with reason + missing-node snapshot + location, and are healed on return.
- **Incremental correctness:** unchanged files are replayed as resolution context,
  so a changed caller still binds to unchanged callees; rebuilds are serialized per
  project and atomic; a shrink guard refuses a rebuild that loses too much.
- **Security model is written down and implemented:** SSRF-guarded HTTP (scheme,
  private IP, metadata endpoints, redirect re-validation), 50 MB fetch cap,
  `validate_graph_path()` confinement, `sanitize_label()`, and
  `<untrusted_source sha256=…>` delimiters + prompt-injection sentinel defanging
  for the semantic pass.
- **Agent-surface discipline:** skill bundles are generated from one source and a
  drift check makes hand-edits fail CI.

---

## 6. Recommendations (in order)

| # | Action | Effort | Payoff |
| --- | --- | --- | --- |
| 1 | Add `LICENSE`, `LICENSE-MIT`, `NOTICE` (or drop `license-files` and the MIT reference); add a wheel-content test | S | fixes a legal/packaging defect; removes build warnings |
| 2 | Declare `pyyaml` (or make the fallback parse nested YAML); add it to `dev` | S | fixes 1 failing test for end users + no silent frontmatter loss |
| 3 | Add a `test` extra (or `docs` note) listing the grammars the suite needs; have CI do a second `pip install -e '.[mcp]'` matrix leg so the lean install is tested | S | catches P0/P1 class drift automatically |
| 4 | Turn on ruff (`F,E9,B` minus the noisy codes you choose) and pyright, and a `--cov-fail-under=75` gate; make `pip-audit` fail on HIGH | M | stops the 134-finding backlog from growing |
| 5 | Split `dispatch_command()` into one function per command (mechanical, testable, no behavior change) and `_extract_generic()` into parse/collect/edge phases | L | reviewability, coverage of the CLI, easier contribution |
| 6 | Migrate URLs to the Code2Graph repo, pick a version story (tags + CHANGELOG on release), align `SECURITY.md` supported versions | S | stops contributor confusion |
| 7 | After the extractor migration completes, consolidate the 32 `add_node`/31 `add_edge` copies into a shared builder mixin | M | −1k lines, one place to fix |
| 8 | Tag resilience catches (`except Exception:  # resilience: scan continues`) or narrow them | M | keeps parsers robust without hiding regressions |

---

## 7. Reproduce this analysis

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[mcp]' pytest pytest-cov ruff            # lean install
pytest tests/ -q                                           # → 32 terraform failures (missing grammar)
pip install tree-sitter-hcl pyyaml                         # → 6542 passed, 0 failed
pytest tests/ -q --cov=code2graph                          # → 80%
python -m tools.skillgen --check                           # → OK, 134 artifacts
ruff check code2graph                                      # → clean (baseline rules)
ruff check --select F,E9,B code2graph                      # → 134 findings
code2graph extract . --code-only --no-cluster              # → 15,217 nodes / 35,451 edges in 23 s
code2graph cluster-only . --no-label --no-viz              # → 615 communities
code2graph query "how does the watcher heal broken references?" --budget 700
python -m build --wheel --no-isolation                     # → wheel OK, missing-license warnings
```

Environment note: the repo's own `code2graph-out/` artifacts produced by the runs
above are gitignored, so they never enter the commit.
