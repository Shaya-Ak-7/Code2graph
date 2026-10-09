"""MCP exposure for broken references and per-file healing state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("mcp")
pytest.importorskip("starlette")

from starlette.testclient import TestClient

from code2graph import serve as serve_mod

_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "healing-test", "version": "0"},
    },
}


def _call(client, headers: dict, name: str, arguments: dict, request_id: int) -> str:
    response = client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
    )
    assert response.status_code == 200
    return response.json()["result"]["content"][0]["text"]


def test_broken_references_and_heal_status_tools(tmp_path: Path):
    graph = {
        "directed": True,
        "nodes": [
            {"id": "caller", "label": "caller()", "source_file": "src/main.py", "community": 0},
        ],
        "edges": [],
        "graph": {
            "broken_references": [
                {
                    "id": "broken-1",
                    "status": "BROKEN",
                    "reason": "Target symbol was deleted during re-parse.",
                    "affected_files": ["src/main.py", "src/target.py"],
                    "missing_node_ids": ["target"],
                    "missing_nodes": [
                        {"id": "target", "label": "target()", "source_file": "src/target.py"}
                    ],
                    "edge": {
                        "source": "caller",
                        "target": "target",
                        "relation": "calls",
                        "source_file": "src/main.py",
                        "source_location": "L7",
                    },
                }
            ],
            "healing_status": {
                "src/main.py": {
                    "status": "BROKEN",
                    "broken_references": 1,
                    "healed_references": 0,
                    "updated_at": "2026-10-09T12:00:00+00:00",
                    "last_action": "updated",
                }
            },
        },
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    app = serve_mod._build_http_app(str(graph_path), json_response=True)

    with TestClient(app, base_url="http://127.0.0.1") as client:
        init = client.post("/mcp", headers=_HEADERS, json=_INIT)
        assert init.status_code == 200
        headers = {**_HEADERS, "mcp-session-id": init.headers.get("mcp-session-id")}
        client.post(
            "/mcp",
            headers=headers,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        broken = _call(client, headers, "broken_references", {}, 2)
        assert "Broken references: 1" in broken
        assert "caller -> target" in broken
        assert "deleted during re-parse" in broken

        status = _call(client, headers, "heal_status", {"file_path": "src/main.py"}, 3)
        assert "Healing status for src/main.py: BROKEN" in status
        assert "Broken references: 1" in status
