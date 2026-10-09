```bash
# Detect the correct Python interpreter (handles uv tool, pipx, venv, system installs)
PYTHON=""
CODE2GRAPH_BIN=$(which code2graph 2>/dev/null)
# 1. uv tool installs — most reliable on modern Mac/Linux
if [ -z "$PYTHON" ] && command -v uv >/dev/null 2>&1; then
    _UV_PY=$(uv tool run --from code2graph python -c "import sys; print(sys.executable)" 2>/dev/null)
    if [ -n "$_UV_PY" ]; then PYTHON="$_UV_PY"; fi
fi
# 2. Read shebang from code2graph binary (pipx and direct pip installs)
if [ -z "$PYTHON" ] && [ -n "$CODE2GRAPH_BIN" ]; then
    _SHEBANG=$(head -1 "$CODE2GRAPH_BIN" | tr -d '#!')
    case "$_SHEBANG" in
        *[!a-zA-Z0-9/_.@-]*) ;;
        *) "$_SHEBANG" -c "import code2graph" 2>/dev/null && PYTHON="$_SHEBANG" ;;
    esac
fi
# 3. Fall back to python3
if [ -z "$PYTHON" ]; then PYTHON="python3"; fi
if ! "$PYTHON" -c "import code2graph" 2>/dev/null; then
    if command -v uv >/dev/null 2>&1; then
        uv tool install --upgrade code2graph -q 2>&1 | tail -3
        _UV_PY=$(uv tool run --from code2graph python -c "import sys; print(sys.executable)" 2>/dev/null)
        if [ -n "$_UV_PY" ]; then PYTHON="$_UV_PY"; fi
    else
        "$PYTHON" -m pip install code2graph -q 2>/dev/null \
          || "$PYTHON" -m pip install code2graph -q --break-system-packages 2>&1 | tail -3
    fi
fi
# Write interpreter path for all subsequent steps (persists across invocations)
mkdir -p code2graph-out
"$PYTHON" -c "import sys; open('code2graph-out/.code2graph_python', 'w', encoding='utf-8').write(sys.executable)"
# Save scan root so `code2graph update` (no args) knows where to look next time.
# The scan path is passed through a quoted heredoc, never substituted into the
# command line itself: a bare `cd <path>` (or an unquoted heredoc, which
# still expands $()/backticks in its body) would let a malicious path execute
# as shell code the moment this line runs.
"$PYTHON" -c "import os, sys; out_path = os.path.abspath('code2graph-out/.code2graph_root'); os.chdir(sys.stdin.readline().rstrip('\n')); open(out_path, 'w', encoding='utf-8').write(os.getcwd())" <<'CODE2GRAPH_ROOT_EOF'
INPUT_PATH
CODE2GRAPH_ROOT_EOF
```

If the import succeeds, print nothing and move straight to Step 2.

**In every subsequent bash block, replace `python3` with `$(cat code2graph-out/.code2graph_python)` to use the correct interpreter.**
