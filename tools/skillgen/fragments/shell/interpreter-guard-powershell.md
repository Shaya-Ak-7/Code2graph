```powershell
if (-not (Test-Path code2graph-out\.code2graph_python)) {
    $CODE2GRAPH_PYTHON = $null
    $code2graphCmd = Get-Command code2graph -ErrorAction SilentlyContinue
    if ($code2graphCmd) {
        # The interpreter that owns the code2graph entry point sits next to it
        # (<env>\Scripts\python.exe for uv tool, pipx, and venv installs).
        $py = Join-Path (Split-Path $code2graphCmd.Source) "python.exe"
        if (Test-Path $py) { $CODE2GRAPH_PYTHON = $py }
    }
    if (-not $CODE2GRAPH_PYTHON) { $CODE2GRAPH_PYTHON = "python" }
    New-Item -ItemType Directory -Force -Path code2graph-out | Out-Null
    & $CODE2GRAPH_PYTHON -c "import sys; open('code2graph-out/.code2graph_python', 'w', encoding='utf-8').write(sys.executable)"
}
```
