"""Per-language extractors, incrementally migrated out of code2graph/extract.py.

Dispatch still flows through code2graph.extract (the facade re-exports every
moved name), so importing from code2graph.extract keeps working unchanged.
LANGUAGE_EXTRACTORS is the registry seed; wiring dispatch through it is a
later, separate step. See MIGRATION.md for how to port another language.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from code2graph.extractors.apex import extract_apex
from code2graph.extractors.bash import extract_bash
from code2graph.extractors.blade import extract_blade
from code2graph.extractors.cobol import extract_cobol
from code2graph.extractors.commonlisp import extract_commonlisp
from code2graph.extractors.dart import extract_dart
from code2graph.extractors.dm import extract_dm, extract_dmf, extract_dmi, extract_dmm
from code2graph.extractors.elixir import extract_elixir
from code2graph.extractors.erlang import extract_erlang
from code2graph.extractors.fortran import extract_fortran
from code2graph.extractors.go import extract_go
from code2graph.extractors.json_config import extract_json
from code2graph.extractors.julia import extract_julia
from code2graph.extractors.markdown import extract_markdown
from code2graph.extractors.objc import extract_objc
from code2graph.extractors.pascal import extract_pascal
from code2graph.extractors.pascal_forms import extract_delphi_form, extract_lazarus_form
from code2graph.extractors.powershell import extract_powershell, extract_powershell_manifest
from code2graph.extractors.r import extract_r
from code2graph.extractors.razor import extract_razor
from code2graph.extractors.rust import extract_rust
from code2graph.extractors.sln import extract_sln
from code2graph.extractors.solidity import extract_solidity
from code2graph.extractors.sql import extract_sql
from code2graph.extractors.terraform import extract_terraform
from code2graph.extractors.verilog import extract_verilog
from code2graph.extractors.vbnet import extract_vbnet
from code2graph.extractors.zig import extract_zig

LANGUAGE_EXTRACTORS: dict[str, Callable[[Path], dict]] = {
    "apex": extract_apex,
    "bash": extract_bash,
    "blade": extract_blade,
    "cobol": extract_cobol,
    "commonlisp": extract_commonlisp,
    "dart": extract_dart,
    "delphi_form": extract_delphi_form,
    "dm": extract_dm,
    "dmf": extract_dmf,
    "dmi": extract_dmi,
    "dmm": extract_dmm,
    "elixir": extract_elixir,
    "erlang": extract_erlang,
    "fortran": extract_fortran,
    "go": extract_go,
    "json": extract_json,
    "julia": extract_julia,
    "lazarus_form": extract_lazarus_form,
    "markdown": extract_markdown,
    "objc": extract_objc,
    "pascal": extract_pascal,
    "powershell": extract_powershell,
    "powershell_manifest": extract_powershell_manifest,
    "r": extract_r,
    "razor": extract_razor,
    "rust": extract_rust,
    "sln": extract_sln,
    "solidity": extract_solidity,
    "sql": extract_sql,
    "terraform": extract_terraform,
    "verilog": extract_verilog,
    "vbnet": extract_vbnet,
    "zig": extract_zig,
}
