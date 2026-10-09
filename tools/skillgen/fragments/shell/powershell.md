```powershell
# Detect Python with code2graph — uv/pipx-aware (fixes #831)
New-Item -ItemType Directory -Force -Path code2graph-out | Out-Null
$CODE2GRAPH_PYTHON = $null

function Find-Code2GraphPython {
    # 1. uv tool install — 'uv tool dir' is authoritative, respects UV_TOOL_DIR automatically
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $uvDir = (uv tool dir 2>$null).Trim()
        if ($uvDir) {
            $py = Join-Path $uvDir "code2graph\Scripts\python.exe"
            if (Test-Path $py) {
                & $py -c "import code2graph" 2>$null
                if ($LASTEXITCODE -eq 0) { return $py }
            }
        }
    }
    # 2. pipx install — 'pipx environment' respects PIPX_HOME automatically
    if (Get-Command pipx -ErrorAction SilentlyContinue) {
        $venvs = (pipx environment --value PIPX_LOCAL_VENVS 2>$null).Trim()
        if ($venvs) {
            $py = Join-Path $venvs "code2graph\Scripts\python.exe"
            if (Test-Path $py) {
                & $py -c "import code2graph" 2>$null
                if ($LASTEXITCODE -eq 0) { return $py }
            }
        }
    }
    # 3. Active venv / conda / pip-into-current-env
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) {
        & $pyCmd.Source -c "import code2graph" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return (& $pyCmd.Source -c "import sys; print(sys.executable)").Trim()
        }
    }
    return $null
}

# Try to find the right Python (uv → pipx → active env)
$CODE2GRAPH_PYTHON = Find-Code2GraphPython

# Not found — install then re-detect
if (-not $CODE2GRAPH_PYTHON) {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv tool install --upgrade code2graph -q 2>&1 | Select-Object -Last 3
    } else {
        pip install code2graph -q 2>&1 | Select-Object -Last 3
    }
    $CODE2GRAPH_PYTHON = Find-Code2GraphPython
}

# Save interpreter path — all subsequent steps read this.
# `Out-File -Encoding utf8` always writes a BOM on Windows PowerShell 5.1 (utf8NoBOM
# only exists from PowerShell 6), and that BOM rides into the saved path, so the hook
# rebuild fails with WinError 123 (#3028). WriteAllText with an explicit BOM-less
# encoding writes the bytes POSIX writes, and adds no trailing newline.
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Join-Path $PWD 'code2graph-out\.code2graph_python'), [string]$CODE2GRAPH_PYTHON, $Utf8NoBom)
# Save scan root so `code2graph update` (no args) knows where to look next time.
# INPUT_PATH is captured through a single-quoted (literal) here-string, never
# substituted directly into the command line: an unquoted bareword argument
# substituted here would let a malicious path (a stray `;`, `|`, or `$(...)`)
# execute as script code the moment this line runs.
$InputPathRaw = @'
INPUT_PATH
'@
[System.IO.File]::WriteAllText((Join-Path $PWD 'code2graph-out\.code2graph_root'), (Resolve-Path $InputPathRaw.Trim()).Path, $Utf8NoBom)
```

If the import succeeds, print nothing and move straight to Step 2.

**In every subsequent block, run Python through the saved interpreter — `& (Get-Content code2graph-out\.code2graph_python)` in place of a bare `python3` — so every step uses the interpreter that actually has code2graph.**
