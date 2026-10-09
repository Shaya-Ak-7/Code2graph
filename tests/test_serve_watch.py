"""MCP-owned watcher startup and stdio-safe rebuild dispatch."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


def test_mcp_auto_watch_uses_quiet_isolated_rebuild(tmp_path, monkeypatch):
    from code2graph import serve

    project = tmp_path / "project"
    output = project / "code2graph-out"
    output.mkdir(parents=True)
    graph = output / "graph.json"
    graph.write_text('{"nodes": [], "links": []}', encoding="utf-8")
    captured = {}

    class FakeThread:
        def __init__(self, *, target, args, kwargs, name, daemon):
            captured.update(target=target, args=args, kwargs=kwargs, name=name, daemon=daemon)

        def start(self):
            captured["started"] = True

        def is_alive(self):
            return False

    monkeypatch.setattr(serve, "_AUTO_WATCHERS", {})
    monkeypatch.setattr(serve.threading, "Thread", FakeThread)

    thread = serve._start_auto_watch(str(graph))

    assert thread is not None
    assert captured["started"] is True
    assert captured["args"] == (project.resolve(),)
    assert captured["kwargs"]["quiet"] is True
    assert captured["kwargs"]["isolated_rebuild"] is True


def test_incremental_rebuild_child_routes_progress_away_from_mcp_stdout(tmp_path, monkeypatch):
    import subprocess

    from code2graph.watch import _rebuild_in_subprocess

    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    changed = [Path("src/changed file.py"), Path("old.py")]

    assert _rebuild_in_subprocess(tmp_path, changed) is True
    assert captured["stdout"] is sys.stderr
    assert captured["stderr"] is sys.stderr
    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["cwd"] == str(tmp_path.resolve())
    assert captured["command"][-2:] == ["src/changed file.py", "old.py"]
