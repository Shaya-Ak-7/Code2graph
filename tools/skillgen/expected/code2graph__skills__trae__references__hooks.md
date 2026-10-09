# code2graph reference: commit hook and native AGENTS.md integration

Load this when the user asked to install the post-commit hook or wire code2graph into a project's AGENTS.md.

## For git commit hook

Install a post-commit hook that auto-rebuilds the graph after every commit. No background process needed - triggers once per commit, works with any editor.

```bash
code2graph hook install    # install
code2graph hook uninstall  # remove
code2graph hook status     # check
```

After every `git commit`, the hook detects which code files changed (via `git diff HEAD~1`), re-runs AST extraction on those files, and rebuilds `graph.json` and `GRAPH_REPORT.md`. Doc/image changes are ignored by the hook - run `/code2graph --update` manually for those.

If a post-commit hook already exists, code2graph appends to it rather than replacing it.

---

## For native AGENTS.md integration (Trae)

Run once per project to make code2graph always-on in Trae sessions:

```bash
code2graph trae install       # or: code2graph trae-cn install
```

This writes a `## code2graph` section to the local `AGENTS.md` that instructs Trae to check the graph before answering codebase questions and rebuild it after code changes. No manual `/code2graph` needed in future sessions.

> **Note:** Unlike Claude Code, Trae does NOT support PreToolUse hooks. The AGENTS.md rules are the always-on mechanism — there is no automatic graph rebuild on tool use. Run `/code2graph --update` manually after code changes if the graph needs refreshing.

```bash
code2graph trae uninstall     # or: code2graph trae-cn uninstall   # remove the section
```
