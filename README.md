# Code2Graph

> **Code2Graph is a temporary project name; the final name is still TBD.**

Code2Graph turns a source tree into a navigable code-intelligence graph. Its MCP server keeps that graph current while you work: file saves, deletes, and renames are detected in the background, changed files are re-parsed incrementally, stale references are recorded as broken, and references are restored automatically when their targets return.

## Why a code graph?

A repository is more than a collection of files. Code2Graph models symbols, files, imports, calls, inheritance, and other relationships as a graph that coding agents can query. This makes it easier to follow execution paths, understand dependencies, and identify the impact of a change without repeatedly scanning the entire project.

## Real-time healing

When the MCP server is running, its background watchdog monitors the project. For locally parseable code and Markdown files it:

1. Debounces save, create, delete, and rename events.
2. Re-parses only the affected files and keeps unchanged nodes in the cached graph.
3. Compares the previous and refreshed node sets.
4. Records edges whose endpoints disappeared as `BROKEN`, with the missing node, location, and reason. Broken references are retained as graph metadata rather than silently discarded or represented as phantom nodes.
5. Restores a broken edge when its node reappears. A unique same-file, same-location match can also heal a symbol rename.
6. Updates the in-memory MCP graph when the persisted graph changes.

There is no manual `update` step for normal code edits or deletions. A first extraction is needed to create the initial graph. Files that need an external semantic/LLM extraction pass (for example, PDFs and images) are detected and flagged; this install does not invent semantic content without a configured model.

## Install and start

Python 3.10 or newer is required.

```bash
# From the repository root
python -m pip install -e '.[mcp]'

# Create the initial local code graph once
code2graph extract . --code-only

# Start the MCP server; the project watcher starts with it
code2graph-mcp code2graph-out/graph.json
```

The graph and its incremental extraction cache are stored under `code2graph-out/` by default. Set `CODE2GRAPH_OUT` before starting the process to use another output directory. Set `CODE2GRAPH_WATCH_DEBOUNCE` to adjust the save-event debounce interval (default: 0.75 seconds).

For a one-off CLI help listing:

```bash
code2graph --help
```

## MCP tools

| Tool | What it does |
| --- | --- |
| `query_graph` | Search relevant nodes and neighboring relationships using a natural-language question. |
| `shortest_path` | Find a path between two concepts or symbols. |
| `get_node`, `get_neighbors`, `get_community` | Inspect a node and its local graph context. |
| `broken_references` | List every currently broken edge, including its source, missing endpoint, and reason. |
| `heal_status` | Report broken/healed reference counts and the current healing state for one file. |

Example calls:

```json
{"tool": "broken_references", "arguments": {}}
{"tool": "heal_status", "arguments": {"file_path": "src/auth/session.py"}}
```

The MCP server also caches each project's graph in memory. Queries reuse that graph; a graph reload happens only after the watcher or another writer changes `graph.json`.

## Supported inputs

The local structural pipeline covers a broad set of programming languages and common source formats. It does not need an API key for code indexing. Markdown-family files with local structural extractors are refreshed by the watcher. Some document, paper, and image formats rely on semantic extraction; those require an LLM-capable workflow and are not silently treated as fully parsed when no model is configured.

## Development

```bash
python -m pip install -e '.[mcp]' pytest
pytest
```

The `tests/` directory covers extraction, incremental rebuilds, MCP tools, broken-reference persistence, file deletion, symbol rename healing, and graph-cache reload behavior. The implementation notes are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Project status

Code2Graph is an experimental code-intelligence project. Its name is provisional, and its MCP schemas, graph metadata, and command surface may evolve before the final project name and release plan are decided.

## License

See `LICENSE`, `LICENSE-MIT`, and `NOTICE` for the applicable license terms and required notices.
