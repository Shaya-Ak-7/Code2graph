## code2graph

This project has a knowledge graph at code2graph-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `code2graph query "<question>"` when code2graph-out/graph.json exists. Use `code2graph path "<A>" "<B>"` for relationships and `code2graph explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If code2graph-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read code2graph-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `code2graph update .` to keep the graph current (AST-only, no API cost).
