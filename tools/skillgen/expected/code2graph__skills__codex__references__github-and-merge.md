# code2graph reference: GitHub clone and cross-repo merge

Load this when the user passed one or more `https://github.com/...` URLs, or named several local subfolders to merge into one graph.

### Step 0 - Clone GitHub repo(s) (only if a GitHub URL was given)

**Single repo:**
```bash
LOCAL_PATH=$(code2graph clone <github-url> [--branch <branch>])
# Use LOCAL_PATH as the target for all subsequent steps
```

**Multiple repos (cross-repo graph):**
```bash
# Clone each repo, run the full pipeline on each, then merge
code2graph clone <url1>   # → ~/.code2graph/repos/<owner1>/<repo1>
code2graph clone <url2>   # → ~/.code2graph/repos/<owner2>/<repo2>
# Run /code2graph on each local path to produce their graph.json files
# Then merge:
code2graph merge-graphs \
  ~/.code2graph/repos/<owner1>/<repo1>/code2graph-out/graph.json \
  ~/.code2graph/repos/<owner2>/<repo2>/code2graph-out/graph.json \
  --out code2graph-out/cross-repo-graph.json
```

Code2Graph clones into `~/.code2graph/repos/<owner>/<repo>` and reuses existing clones on repeat runs. Each node in the merged graph carries a `repo` attribute so you can filter by origin.

**Multiple local subfolders (monorepo or multi-service layout):**

The skill pipeline writes all intermediate and final outputs to `code2graph-out/` in the current working directory. Running the skill on each subfolder separately will clobber the same output dir. Instead, use the CLI directly for each subfolder — it places `code2graph-out/` *inside* the scanned path:

```bash
code2graph extract ./core/     # → ./core/code2graph-out/graph.json
code2graph extract ./service/  # → ./service/code2graph-out/graph.json
code2graph extract ./platform/ # → ./platform/code2graph-out/graph.json
# Add --backend gemini|kimi|openai|deepseek|claude-cli depending on which API key you have set

# Then merge at the project root:
code2graph merge-graphs \
  ./core/code2graph-out/graph.json \
  ./service/code2graph-out/graph.json \
  ./platform/code2graph-out/graph.json \
  --out code2graph-out/graph.json
```

Once `code2graph-out/graph.json` exists, the fast path above takes over: any codebase question runs `code2graph query` directly on the merged graph — no re-extraction, no size gate.
