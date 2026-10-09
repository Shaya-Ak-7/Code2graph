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

## For native AGENTS.md integration

Run once per project to make code2graph always-on in Amp sessions:

```bash
code2graph amp install
```

This writes a `## code2graph` section to the local `AGENTS.md` that instructs Amp to check the graph before answering codebase questions and rebuild it after code changes. No manual `/code2graph` needed in future sessions.

```bash
code2graph amp uninstall  # remove the section
```
