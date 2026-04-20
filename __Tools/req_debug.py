#!/usr/bin/env python3
"""
req_debug.py — deep multiplicity probe for a specific RequirementDefinition.

Usage:
    python __Tools/req_debug.py . <TypeName>
    e.g. python __Tools/req_debug.py . CapabilityRequirement
"""

import sys
from pathlib import Path
import syside
from syside.preview import open_model

SRS_DEFS_PACKAGE = "SRS_Definitions"


def collect_typed(root, std_type, results):
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        for m in root.cast(syside.Namespace.STD).owned_members.collect():
            collect_typed(m, std_type, results)


def dump_node(node, label: str, depth: int = 0, max_depth: int = 6):
    pad = "  " * depth
    pytype = type(node).__name__
    val = getattr(node, 'value', '<no .value>')
    print(f"{pad}{label}: type={pytype!r}  value={val!r}")
    if depth >= max_depth:
        return
    # Try owned_members
    try:
        children = list(node.owned_members.collect())
        for i, child in enumerate(children):
            dump_node(child, f"owned_members[{i}]", depth + 1, max_depth)
    except Exception as e:
        print(f"{pad}  owned_members: ERROR({e})")
    # Try result
    try:
        r = node.result
        if r is not None:
            dump_node(r, "result", depth + 1, max_depth)
    except Exception:
        pass
    # Try operand
    try:
        ops = list(node.operand.collect()) if hasattr(node, 'operand') else []
        for i, op in enumerate(ops):
            dump_node(op, f"operand[{i}]", depth + 1, max_depth)
    except Exception:
        pass


def probe_multiplicity(member):
    name = member.declared_name or "<None>"
    pytype = type(member).__name__
    print(f"\n  member: {name!r}  ({pytype})")
    try:
        mult = member.declared_multiplicity
        if mult is None:
            print(f"    declared_multiplicity: None")
            return
        print(f"    declared_multiplicity: type={type(mult).__name__!r}")
        # lower_bound
        try:
            lb = mult.lower_bound
            print(f"    lower_bound: type={type(lb).__name__!r}  value={getattr(lb, 'value', '<no .value>')!r}")
            if lb is not None:
                dump_node(lb, "lower_bound tree", depth=6, max_depth=12)
        except Exception as e:
            print(f"    lower_bound: ERROR({e})")
        # upper_bound
        try:
            ub = mult.upper_bound
            print(f"    upper_bound: type={type(ub).__name__!r}  value={getattr(ub, 'value', '<no .value>')!r}")
        except Exception as e:
            print(f"    upper_bound: ERROR({e})")
    except Exception as e:
        print(f"    declared_multiplicity: ERROR({e})")


def main():
    if len(sys.argv) < 3:
        print("Usage: python req_debug.py <model_dir> <TypeName>")
        sys.exit(1)

    model_dir  = Path(sys.argv[1]).resolve()
    type_name  = sys.argv[2]

    with open_model(model_dir) as model:
        for top in model.top_elements_from(model_dir):
            if not top.isinstance(syside.Namespace.STD):
                continue
            if top.declared_name != SRS_DEFS_PACKAGE:
                continue

            req_defs = []
            collect_typed(top, syside.RequirementDefinition.STD, req_defs)

            for rd in req_defs:
                if rd.declared_name != type_name:
                    continue
                print(f"\nRequirementDefinition: {rd.declared_name!r}")
                print("=" * 60)
                for member in rd.owned_members.collect():
                    probe_multiplicity(member)
            break


if __name__ == "__main__":
    main()
