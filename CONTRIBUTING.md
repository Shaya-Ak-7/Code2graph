# Contributing to Code2Graph

Code2Graph is an experimental code-intelligence graph with an incremental file watcher and broken-reference healing. Its name is temporary; the final name is TBD. Contributions should protect graph correctness, preserve source provenance, and include tests for observable behavior changes.

## Get started

```bash
git clone https://github.com/Shaya-Ak-7/knowledge-graph-7.git
cd knowledge-graph-7
python -m pip install -e '.[mcp]'
python -m pip install pytest
pytest tests/ -q
```

Python 3.10 or newer is required. Optional dependencies are listed in `pyproject.toml`; install the relevant extras only when working on those features.

## Project layout

- `code2graph/` — package, CLI, MCP server, extractors, watcher, and graph healing.
- `tests/` — unit and integration tests.
- `docs/` — design and usage documentation.
- `tools/skillgen/` — source fragments and generator for bundled agent instructions.

Read [ARCHITECTURE.md](ARCHITECTURE.md) before making changes to extraction, persistence, or incremental rebuild behavior. Do not hand-edit generated skill bundles; edit their source fragments and run the generator.

## Development expectations

- Keep extraction deterministic and local unless a feature explicitly opts into a remote model.
- Preserve graph nodes and edges from unchanged files during incremental rebuilds.
- Do not create edges to missing nodes. Keep unresolved references inspectable with their source location and reason.
- Treat deleted and renamed paths as first-class watcher events.
- Add regression tests that fail before the change and pass afterward.
- Document limitations, especially for formats that need semantic/LLM extraction.
- Keep tests independent of ambient credentials and machine-specific environment settings.

## Verification

Run the relevant tests while developing, then run the complete suite:

```bash
pytest tests/ -q
python -m compileall -q code2graph tests
```

If changing generated skills, use the repository's generator and verify the generated output. If changing package metadata or dependencies, validate `pyproject.toml` and refresh `uv.lock` with `uv lock` when `uv` is available.

## Pull requests and reports

Use a focused pull request with a clear problem statement, implementation summary, verification commands, and known limitations. For bug reports, include a small reproducible example and omit secrets or proprietary source files. Use GitHub Discussions for questions and the [issue tracker](https://github.com/Shaya-Ak-7/knowledge-graph-7/issues) for actionable bugs and feature requests.

For security-sensitive reports, follow [SECURITY.md](SECURITY.md) instead of posting details publicly. Please also follow the [Code of Conduct](CODE_OF_CONDUCT.md).
