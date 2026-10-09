"""Persistent broken-reference tracking and automatic graph healing.

Healing metadata is stored under ``graph.broken_references`` and
``graph.healing_status`` in graph.json. Broken edges stay out of the active
NetworkX edge set until all referenced nodes can be resolved again; this keeps
query traversals free of phantom nodes while making every dropped reference
visible and recoverable.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


_BROKEN_KEY = "broken_references"
_STATUS_KEY = "healing_status"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_value(value: Any) -> Any:
    """Return a JSON-safe value without allowing one malformed edge to abort a build."""
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        return repr(value)


def _graph_metadata(data: dict) -> dict:
    graph = data.get("graph")
    if not isinstance(graph, dict):
        graph = {}
        data["graph"] = graph
    return graph


def _edges(data: dict) -> list[dict]:
    edges = data.get("links")
    if not isinstance(edges, list):
        edges = data.get("edges")
    return [edge for edge in edges or [] if isinstance(edge, dict)]


def _nodes(data: dict) -> dict[Any, dict]:
    out: dict[Any, dict] = {}
    for node in data.get("nodes", []) or []:
        if not isinstance(node, dict) or "id" not in node:
            continue
        try:
            out[node["id"]] = node
        except TypeError:
            continue
    return out


def _normal_path(value: Any, root: str | Path | None = None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("\\", "/")
    path = Path(raw)
    if root is not None and path.is_absolute():
        try:
            raw = path.resolve().relative_to(Path(root).resolve()).as_posix()
        except (ValueError, OSError, RuntimeError):
            raw = path.as_posix()
    while raw.startswith("./"):
        raw = raw[2:]
    return raw


def _node_snapshot(node_id: Any, node: dict | None) -> dict:
    node = node if isinstance(node, dict) else {}
    return {
        "id": _json_value(node_id),
        "label": _json_value(node.get("label", str(node_id))),
        "source_file": _normal_path(node.get("source_file")),
        "source_location": _json_value(node.get("source_location")),
        "file_type": _json_value(node.get("file_type")),
        "kind": _json_value(node.get("kind")),
        "type": _json_value(node.get("type")),
        "language": _json_value(node.get("language")),
    }


def _edge_identity(edge: dict, missing_ids: list[Any]) -> str:
    identity = {
        "source": _json_value(edge.get("source", edge.get("from"))),
        "target": _json_value(edge.get("target", edge.get("to"))),
        "relation": _json_value(edge.get("relation", edge.get("type"))),
        "source_file": _normal_path(edge.get("source_file")),
        "source_location": _json_value(edge.get("source_location")),
        "missing": sorted((str(item) for item in missing_ids)),
    }
    raw = json.dumps(identity, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def make_broken_reference(
    edge: dict,
    missing_node_ids: list[Any],
    *,
    known_nodes: dict[Any, dict] | None = None,
    reason: str | None = None,
) -> dict:
    """Create a serializable BROKEN record for an edge with unresolved endpoints."""
    known_nodes = known_nodes or {}
    missing_ids: list[Any] = []
    for node_id in missing_node_ids:
        try:
            hash(node_id)
            safe_id = node_id
        except TypeError:
            safe_id = repr(node_id)
        if safe_id not in missing_ids:
            missing_ids.append(safe_id)
    missing_nodes = []
    affected_files: set[str] = set()
    for node_id in missing_ids:
        try:
            node = known_nodes.get(node_id)
        except TypeError:
            node = None
        snapshot = _node_snapshot(node_id, node)
        missing_nodes.append(snapshot)
        if snapshot.get("source_file"):
            affected_files.add(snapshot["source_file"])
    source_file = _normal_path(edge.get("source_file"))
    if source_file:
        affected_files.add(source_file)
    missing_names = [
        f"{node.get('label') or node.get('id')}"
        + (f" ({node['source_file']})" if node.get("source_file") else "")
        for node in missing_nodes
    ]
    return {
        "id": _edge_identity(edge, missing_ids),
        "status": "BROKEN",
        "reason": reason or (
            "Missing graph endpoint(s): " + ", ".join(missing_names or map(str, missing_ids))
        ),
        "created_at": _now(),
        "missing_nodes": missing_nodes,
        "missing_node_ids": [_json_value(item) for item in missing_ids],
        "affected_files": sorted(affected_files),
        "edge": {str(key): _json_value(value) for key, value in edge.items()},
    }


def _merge_records(*record_lists: list) -> list[dict]:
    merged: dict[str, dict] = {}
    order: list[str] = []
    for records in record_lists:
        for record in records or []:
            if not isinstance(record, dict):
                continue
            edge = record.get("edge")
            missing = record.get("missing_node_ids")
            if not isinstance(edge, dict):
                continue
            if not isinstance(missing, list):
                missing = [n.get("id") for n in record.get("missing_nodes", []) if isinstance(n, dict)]
            identity = str(record.get("id") or _edge_identity(edge, missing))
            copied = dict(record)
            copied["id"] = identity
            copied["status"] = str(copied.get("status", "BROKEN")).upper()
            if identity not in merged:
                order.append(identity)
                merged[identity] = copied
            else:
                previous = merged[identity]
                # The latest observation wins state/reason while retaining the
                # first-seen timestamp and any useful node metadata.
                merged[identity] = {**previous, **copied}
                if previous.get("created_at"):
                    merged[identity]["created_at"] = previous["created_at"]
                old_missing = previous.get("missing_nodes", [])
                new_missing = copied.get("missing_nodes", [])
                if len(old_missing) > len(new_missing):
                    merged[identity]["missing_nodes"] = old_missing
                old_files = previous.get("affected_files", [])
                new_files = copied.get("affected_files", [])
                merged[identity]["affected_files"] = sorted(set(old_files) | set(new_files))
    return [merged[key] for key in order]


def _same_node_kind(expected: dict, candidate: dict) -> bool:
    for key in ("file_type", "kind", "type", "language"):
        value = expected.get(key)
        if value not in (None, "") and candidate.get(key) not in (None, "") and candidate.get(key) != value:
            return False
    return True


def _find_replacement(expected: dict, nodes: dict[Any, dict], root: str | Path | None) -> Any | None:
    old_id = expected.get("id")
    if old_id in nodes:
        return old_id

    old_file = _normal_path(expected.get("source_file"), root)
    old_label = expected.get("label")
    if not old_file:
        return None
    same_file = [
        (node_id, node)
        for node_id, node in nodes.items()
        if _normal_path(node.get("source_file"), root) == old_file
    ]

    # Re-created symbols with the same display name are the safest match.
    exact_label = [
        node_id for node_id, node in same_file
        if old_label and str(node.get("label", "")) == str(old_label)
    ]
    if len(exact_label) == 1:
        return exact_label[0]

    # A symbol rename normally keeps its file, source line, and AST kind. Use
    # that signature only when it selects exactly one new node in the file.
    old_location = expected.get("source_location")
    if old_location not in (None, ""):
        at_location = [
            node_id for node_id, node in same_file
            if node.get("source_location") == old_location and _same_node_kind(expected, node)
        ]
        if len(at_location) == 1:
            return at_location[0]
    return None


def _set_metadata(data: dict, key: str, value: Any) -> None:
    _graph_metadata(data)[key] = value


def read_broken_references(data: dict, *, include_healed: bool = False) -> list[dict]:
    """Return persisted reference records, broken-only unless requested otherwise."""
    graph = data.get("graph") if isinstance(data, dict) else None
    records = graph.get(_BROKEN_KEY, []) if isinstance(graph, dict) else []
    if not isinstance(records, list):
        return []
    out = [record for record in records if isinstance(record, dict)]
    if not include_healed:
        out = [record for record in out if str(record.get("status", "BROKEN")).upper() == "BROKEN"]
    return out


def record_broken_reference(data: dict, record: dict) -> None:
    """Add a broken edge record to either raw graph data or NetworkX metadata."""
    graph = _graph_metadata(data)
    current = graph.get(_BROKEN_KEY, [])
    graph[_BROKEN_KEY] = _merge_records(current if isinstance(current, list) else [], [record])


def reconcile_healing(
    old_graph: dict,
    new_graph: dict,
    *,
    changed_paths: list[str | Path] | None = None,
    project_root: str | Path | None = None,
) -> dict:
    """Carry broken references forward, detect deleted nodes, and auto-heal matches.

    ``new_graph`` is mutated in place. Its regular edge list contains only valid
    endpoints; any unresolved edge is retained in graph metadata with a reason.
    When all missing nodes reappear (or a unique same-file rename match is
    found), the original edge is restored to the active edge list and its
    record transitions to ``HEALED``.
    """
    old_graph = old_graph if isinstance(old_graph, dict) else {}
    new_graph = new_graph if isinstance(new_graph, dict) else {}
    old_meta = old_graph.get("graph") if isinstance(old_graph.get("graph"), dict) else {}
    new_meta = _graph_metadata(new_graph)
    old_nodes = _nodes(old_graph)
    new_nodes = _nodes(new_graph)
    old_edges = _edges(old_graph)
    new_edges_key = "links" if isinstance(new_graph.get("links"), list) else "edges"
    current_edges = new_graph.get(new_edges_key)
    if not isinstance(current_edges, list):
        current_edges = []
        new_graph[new_edges_key] = current_edges

    records = _merge_records(
        old_meta.get(_BROKEN_KEY, []) if isinstance(old_meta.get(_BROKEN_KEY), list) else [],
        new_meta.get(_BROKEN_KEY, []) if isinstance(new_meta.get(_BROKEN_KEY), list) else [],
    )
    by_id = {record["id"]: record for record in records}
    removed_ids = set(old_nodes) - set(new_nodes)
    for edge in old_edges:
        src = edge.get("source", edge.get("from"))
        tgt = edge.get("target", edge.get("to"))
        missing = [node_id for node_id in (src, tgt) if node_id in removed_ids]
        if not missing:
            continue
        snapshots = {node_id: old_nodes.get(node_id) for node_id in missing}
        record = make_broken_reference(
            edge,
            missing,
            known_nodes=snapshots,
            reason=(
                "Connected node(s) were removed or renamed during file re-parse: "
                + ", ".join(
                    str((old_nodes.get(node_id) or {}).get("label", node_id))
                    for node_id in missing
                )
            ),
        )
        prior = by_id.get(record["id"])
        if prior:
            prior.update(record)
            prior["status"] = "BROKEN"
        else:
            records.append(record)
            by_id[record["id"]] = record

    resolved_this_run: list[dict] = []
    for record in records:
        if str(record.get("status", "BROKEN")).upper() != "BROKEN":
            continue
        edge = record.get("edge")
        if not isinstance(edge, dict):
            continue
        missing_nodes = record.get("missing_nodes")
        if not isinstance(missing_nodes, list):
            missing_nodes = []
        missing_ids = record.get("missing_node_ids")
        if not isinstance(missing_ids, list):
            missing_ids = [n.get("id") for n in missing_nodes if isinstance(n, dict)]
        snapshots_by_id = {
            node.get("id"): node for node in missing_nodes if isinstance(node, dict)
        }
        mapping: dict[Any, Any] = {}
        unresolved: list[Any] = []
        for missing_id in missing_ids:
            expected = snapshots_by_id.get(missing_id)
            if expected is None:
                expected = _node_snapshot(missing_id, old_nodes.get(missing_id))
            replacement = _find_replacement(expected, new_nodes, project_root)
            if replacement is None:
                unresolved.append(missing_id)
            else:
                mapping[missing_id] = replacement
                replacement_file = _normal_path(new_nodes[replacement].get("source_file"), project_root)
                if replacement_file:
                    record["affected_files"] = sorted(
                        set(record.get("affected_files", [])) | {replacement_file}
                    )
        if unresolved:
            continue

        healed_edge = dict(edge)
        src_key = "source" if "source" in healed_edge else "from"
        tgt_key = "target" if "target" in healed_edge else "to"
        if healed_edge.get(src_key) in mapping:
            healed_edge[src_key] = mapping[healed_edge[src_key]]
        if healed_edge.get(tgt_key) in mapping:
            healed_edge[tgt_key] = mapping[healed_edge[tgt_key]]
        src = healed_edge.get(src_key)
        tgt = healed_edge.get(tgt_key)
        if src not in new_nodes or tgt not in new_nodes:
            continue

        healed_edge.pop("from", None)
        healed_edge.pop("to", None)
        healed_edge["healed_from_reference"] = record.get("id")
        healed_edge["healed_at"] = _now()
        if not any(
            isinstance(existing, dict)
            and existing.get("source", existing.get("from")) == src
            and existing.get("target", existing.get("to")) == tgt
            and existing.get("relation", existing.get("type")) == healed_edge.get("relation", healed_edge.get("type"))
            for existing in current_edges
        ):
            current_edges.append(healed_edge)
            resolved_this_run.append(healed_edge)
        record["status"] = "HEALED"
        record["resolved_at"] = _now()
        record["resolved_nodes"] = [
            {"from": _json_value(old_id), "to": _json_value(new_id)}
            for old_id, new_id in mapping.items()
        ]
        record["reason"] = "Automatically healed after the missing node was reintroduced or renamed."
        resolved_this_run.append(record)

    # Track only files with broken/healed references. Ordinary saves do not
    # churn graph metadata or cause a redundant graph clustering pass.
    statuses = old_meta.get(_STATUS_KEY, {}) if isinstance(old_meta.get(_STATUS_KEY), dict) else {}
    statuses = dict(statuses)
    changed_keys = {
        key for raw in (changed_paths or [])
        if (key := _normal_path(str(raw), project_root))
    }
    newly_healed_ids = {
        item.get("id") for item in resolved_this_run
        if isinstance(item, dict) and item.get("status") == "HEALED"
    }
    for file_key in changed_keys:
        broken_for_file = [
            record for record in records
            if str(record.get("status", "BROKEN")).upper() == "BROKEN"
            and file_key in (record.get("affected_files") or [])
        ]
        healed_for_file = [
            record for record in records
            if record.get("id") in newly_healed_ids
            and file_key in (record.get("affected_files") or [])
        ]
        previous = statuses.get(file_key, {})
        if broken_for_file:
            state = "BROKEN"
        elif healed_for_file or previous.get("status") == "BROKEN":
            state = "HEALED"
        else:
            # A healthy file needs no stored event record; the MCP status tool
            # can answer from the current graph without recording every save.
            continue
        snapshot = {
            "status": state,
            "broken_references": len(broken_for_file),
            "healed_references": max(
                int(previous.get("healed_references", 0)), len(healed_for_file)
            ),
        }
        if previous.get("status") != state or previous.get("broken_references") != snapshot["broken_references"]:
            snapshot["updated_at"] = _now()
            snapshot["last_action"] = "deleted" if project_root and not (Path(project_root) / file_key).exists() else "updated"
        else:
            snapshot.update({key: value for key, value in previous.items() if key not in snapshot})
        statuses[file_key] = snapshot

    new_meta[_BROKEN_KEY] = records
    new_meta[_STATUS_KEY] = statuses
    return {
        "broken": [record for record in records if record.get("status") == "BROKEN"],
        "healed": [item for item in resolved_this_run if isinstance(item, dict) and item.get("status") == "HEALED"],
        "healed_edges": [item for item in resolved_this_run if isinstance(item, dict) and "source" in item and "target" in item],
        "removed_node_ids": sorted((str(item) for item in removed_ids)),
    }


def file_healing_status(data: dict, file_path: str, *, project_root: str | Path | None = None) -> dict:
    """Compute the current healing state for a file from graph records."""
    key = _normal_path(file_path, project_root)
    graph = data.get("graph") if isinstance(data.get("graph"), dict) else {}
    statuses = graph.get(_STATUS_KEY, {}) if isinstance(graph.get(_STATUS_KEY), dict) else {}
    status_record = statuses.get(key, {}) if key else {}
    broken = [
        record for record in read_broken_references(data)
        if key in (record.get("affected_files") or [])
    ]
    historical = [
        record for record in read_broken_references(data, include_healed=True)
        if str(record.get("status", "")).upper() == "HEALED"
        and key in (record.get("affected_files") or [])
    ]
    state = "BROKEN" if broken else status_record.get("status", "HEALTHY")
    return {
        "file": key or file_path,
        "status": state,
        "broken_references": len(broken),
        "healed_references": max(
            int(status_record.get("healed_references", 0)), len(historical)
        ),
        "updated_at": status_record.get("updated_at"),
        "last_action": status_record.get("last_action"),
        "references": broken,
    }
