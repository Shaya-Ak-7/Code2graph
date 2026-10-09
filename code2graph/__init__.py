"""code2graph - extract · build · cluster · analyze · report."""


def __getattr__(name):
    # Lazy imports so `code2graph install` works before heavy deps are in place.
    _map = {
        "extract": ("code2graph.extract", "extract"),
        "collect_files": ("code2graph.extract", "collect_files"),
        "build_from_json": ("code2graph.build", "build_from_json"),
        "cluster": ("code2graph.cluster", "cluster"),
        "score_all": ("code2graph.cluster", "score_all"),
        "cohesion_score": ("code2graph.cluster", "cohesion_score"),
        "god_nodes": ("code2graph.analyze", "god_nodes"),
        "surprising_connections": ("code2graph.analyze", "surprising_connections"),
        "suggest_questions": ("code2graph.analyze", "suggest_questions"),
        "generate": ("code2graph.report", "generate"),
        "to_json": ("code2graph.export", "to_json"),
        "to_html": ("code2graph.export", "to_html"),
        "to_svg": ("code2graph.export", "to_svg"),
        "to_canvas": ("code2graph.export", "to_canvas"),
        "to_wiki": ("code2graph.wiki", "to_wiki"),
        "reflect": ("code2graph.reflect", "reflect"),
        "save_query_result": ("code2graph.ingest", "save_query_result"),
    }
    if name in _map:
        import importlib
        mod_name, attr = _map[name]
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr)
    raise AttributeError(f"module 'code2graph' has no attribute {name!r}")
