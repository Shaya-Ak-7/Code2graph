```bash
if [ ! -f code2graph-out/.code2graph_python ]; then
    CODE2GRAPH_BIN=$(which code2graph 2>/dev/null)
    if [ -n "$CODE2GRAPH_BIN" ]; then
        PYTHON=$(head -1 "$CODE2GRAPH_BIN" | tr -d '#!')
        case "$PYTHON" in *[!a-zA-Z0-9/_.@-]*) PYTHON="python3" ;; esac
    else
        PYTHON="python3"
    fi
    mkdir -p code2graph-out
    "$PYTHON" -c "import sys; open('code2graph-out/.code2graph_python', 'w', encoding='utf-8').write(sys.executable)"
fi
```
