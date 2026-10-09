"""Tests for persistent broken-reference tracking and automatic healing."""

from pathlib import Path

from code2graph.build import build_from_json, finalize_raw_graph_endpoints
from code2graph.healing import file_healing_status, read_broken_references, reconcile_healing


def _node(node_id: str, label: str, source_file: str, **extra) -> dict:
    return {
        "id": node_id,
        "label": label,
        "file_type": "code",
        "source_file": source_file,
        **extra,
    }


def test_build_records_dangling_edge_without_creating_phantom_node():
    graph = build_from_json(
        {
            "nodes": [_node("caller", "caller()", "caller.py")],
            "edges": [
                {
                    "source": "caller",
                    "target": "missing",
                    "relation": "calls",
                    "source_file": "caller.py",
                    "source_location": "L4",
                }
            ],
        }
    )

    assert "missing" not in graph
    assert graph.number_of_edges() == 0
    records = graph.graph["broken_references"]
    assert len(records) == 1
    assert records[0]["status"] == "BROKEN"
    assert records[0]["edge"]["target"] == "missing"
    assert "endpoint" in records[0]["reason"]


def test_raw_graph_finalizer_persists_dangling_edge_reason():
    graph_data = {
        "nodes": [_node("source", "source", "source.js")],
        "links": [
            {"source": "source", "target": "absent", "relation": "calls"}
        ],
    }

    finalize_raw_graph_endpoints(graph_data)

    assert graph_data["links"] == []
    records = read_broken_references(graph_data)
    assert len(records) == 1
    assert records[0]["status"] == "BROKEN"
    assert "absent" in records[0]["missing_node_ids"]


def test_deleted_node_marks_all_old_edges_broken_then_readdition_heals_them(tmp_path):
    old_graph = {
        "directed": True,
        "graph": {},
        "nodes": [
            _node("caller", "caller()", "caller.py"),
            _node("target", "target()", "target.py", source_location="L8", kind="function"),
        ],
        "links": [
            {
                "source": "caller",
                "target": "target",
                "relation": "calls",
                "source_file": "caller.py",
                "source_location": "L4",
            }
        ],
    }
    after_delete = {
        "directed": True,
        "graph": {},
        "nodes": [_node("caller", "caller()", "caller.py")],
        "links": [],
    }

    result = reconcile_healing(
        old_graph,
        after_delete,
        changed_paths=[Path("target.py")],
        project_root=tmp_path,
    )

    broken = read_broken_references(after_delete)
    assert len(broken) == 1
    assert broken[0]["status"] == "BROKEN"
    assert broken[0]["missing_node_ids"] == ["target"]
    assert file_healing_status(after_delete, "target.py", project_root=tmp_path)["status"] == "BROKEN"

    restored = {
        "directed": True,
        "graph": {},
        "nodes": [
            _node("caller", "caller()", "caller.py"),
            _node("target", "target()", "target.py", source_location="L8", kind="function"),
        ],
        "links": [],
    }
    healed = reconcile_healing(
        after_delete,
        restored,
        changed_paths=[Path("target.py")],
        project_root=tmp_path,
    )

    assert len(healed["healed_edges"]) == 1
    assert restored["links"][0]["source"] == "caller"
    assert restored["links"][0]["target"] == "target"
    assert restored["links"][0]["healed_from_reference"]
    assert read_broken_references(restored) == []
    status = file_healing_status(restored, "target.py", project_root=tmp_path)
    assert status["status"] == "HEALED"
    assert status["healed_references"] == 1


def test_unique_same_file_symbol_rename_auto_heals_inbound_edge(tmp_path):
    old_graph = {
        "graph": {},
        "nodes": [
            _node("caller", "caller()", "caller.py"),
            _node("old_name", "old_name()", "module.py", source_location="L12", kind="function"),
        ],
        "links": [
            {"source": "caller", "target": "old_name", "relation": "calls", "source_file": "caller.py"}
        ],
    }
    renamed_graph = {
        "graph": {},
        "nodes": [
            _node("caller", "caller()", "caller.py"),
            _node("new_name", "new_name()", "module.py", source_location="L12", kind="function"),
        ],
        "links": [],
    }

    reconcile_healing(
        old_graph,
        renamed_graph,
        changed_paths=[Path("module.py")],
        project_root=tmp_path,
    )

    assert renamed_graph["links"] == [
        {
            "source": "caller",
            "target": "new_name",
            "relation": "calls",
            "source_file": "caller.py",
            "healed_from_reference": renamed_graph["graph"]["broken_references"][0]["id"],
            "healed_at": renamed_graph["links"][0]["healed_at"],
        }
    ]
    assert renamed_graph["graph"]["broken_references"][0]["status"] == "HEALED"
    assert read_broken_references(renamed_graph) == []
