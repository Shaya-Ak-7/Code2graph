# Changelog

## Unreleased

- Established Code2Graph as a temporary project name; the final name remains TBD.
- Added per-project background watching to the MCP server and incremental handling for code and locally parseable Markdown changes, including deletions and renames.
- Persisted unresolved graph relationships as `BROKEN` references with reasons, and added automatic restoration plus the `broken_references` and `heal_status` MCP tools.
- Rewrote the project overview around code intelligence and real-time graph healing.
