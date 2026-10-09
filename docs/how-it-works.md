# Code2Graph architecture overview

Code2Graph builds a local graph of source files, symbols, and relationships, then exposes that graph to agents through an MCP server. The project name is temporary; the final name is TBD.

Code files are not sent to the LLM semantic extractor for structural indexing. When a corpus contains only code files, the semantic extraction pass is skipped entirely.

## Extraction pipeline

1. **Discover files.** The scanner applies language, ignore, and safety rules before extraction.
2. **Parse code locally.** Tree-sitter-backed extractors build file and symbol nodes and relationships such as imports, calls, containment, and inheritance. Source code is not sent to a model for this structural pass.
3. **Resolve relationships.** Cross-file resolvers use the current parse results plus read-only symbol data from unchanged files. This lets incremental parsing stay scoped to changed files without losing links to unchanged symbols.
4. **Build and validate the graph.** The builder deduplicates nodes, normalizes relationships, and refuses to leave dangling endpoints in the active graph.
5. **Persist outputs.** `code2graph-out/graph.json` is the queryable graph; cache and manifest files support incremental work.

Some document formats use local structural extraction, including Markdown-family files. Other content—such as PDFs and images—needs semantic extraction from a configured model or agent workflow. The watcher detects those changes and flags pending semantic work rather than claiming to have parsed them locally.

## Live updates

When `code2graph-mcp` starts, it starts a background watcher for the project that contains the configured graph. A short debounce groups editor save events, and a move event contributes both the old and new paths.

For changed code and locally parseable Markdown files, the watcher:

- parses only changed files that still exist;
- reuses stored AST data for unchanged files as a resolution context;
- removes stale nodes from deleted or renamed-away files;
- reconciles changed nodes and edges with the previous graph; and
- atomically writes the updated graph.

Updates are serialized per project so concurrent hook or watcher rebuilds do not overwrite each other's change sets. Files excluded by the corpus rules are not accidentally indexed by the watcher.

## Broken references and healing

If removing or changing a node leaves an existing relationship without an endpoint, that relationship is not inserted into the active NetworkX graph. Instead, the graph JSON records it under `graph.broken_references` with status `BROKEN`, a reason, edge attributes, missing-node snapshots, affected paths, and source location when available. This prevents dangling edges and phantom endpoint nodes while retaining enough evidence to diagnose and recover the relationship.

On each incremental rebuild, the healer compares the previous graph and the new node set. If the referenced node returns, it restores the edge and marks the historical record `HEALED`. A uniquely identifiable replacement in the same file and source location can heal a same-file symbol rename. Per-file summaries are stored under `graph.healing_status`.

The MCP tools `broken_references` and `heal_status` expose this state to agents. They are read-only diagnostics; normal graph edits and automatic healing happen in the watcher/rebuild pipeline.

## Graph cache

The MCP process keeps a bounded in-memory context for each graph it serves. A context is reused while the graph file's identity and modification state are unchanged; after a write, the next query reloads the updated graph. This avoids repeated JSON parsing while allowing the watcher and external graph writers to make changes visible.

## Important constraints

- The source tree and graph remain local unless an optional model-backed workflow is explicitly used.
- Deterministic extraction is kept separate from semantic inference.
- A failed or partial parse must not silently destroy valid graph state.
- Broken edges are recoverable metadata, not active traversable edges.
- Semantic-only files cannot be fully refreshed without a semantic extraction provider.

See the project [README](../README.md) for install and MCP usage instructions.
