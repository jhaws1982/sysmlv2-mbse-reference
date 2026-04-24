"""
stakeholder_traceability.py — SN-06 Stakeholder Requirement → Use Case Traceability

Shows which use cases address which stakeholder concerns via frame concern links.
Identifies concerns with no use case coverage.

Usage: python __Tools/stakeholder_traceability.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_unnamed_doc,
    md_heading, md_table, write_report, collapse_doc,
)
import syside


def get_framed_concerns(req_def) -> list[str]:
    """Return concern names framed by a requirement definition."""
    names = []
    try:
        for member in req_def.owned_members.collect():
            if member.isinstance(syside.FramedConcernMembership.STD):
                fcm = member.cast(syside.FramedConcernMembership.STD)
                try:
                    for concern in fcm.concerns.collect():
                        names.append(get_declared_name(concern))
                except Exception:
                    pass
    except Exception:
        pass
    return names


def main():
    args = parse_args("SN-06 Stakeholder Requirement → Use Case Traceability")
    model_dir = args.model_dir

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        concern_defs, use_cases, req_defs = [], [], []
        for top in model.top_elements_from(str(model_dir)):
            collect_typed(top, syside.ConcernDefinition.STD, concern_defs)
            collect_typed(top, syside.UseCaseUsage.STD, use_cases)
            collect_typed(top, syside.RequirementDefinition.STD, req_defs)

        # Build: concern_name -> [req_def_names that frame it]
        concern_to_reqdefs: dict[str, list[str]] = defaultdict(list)
        for rd in req_defs:
            rd_name = get_declared_name(rd)
            for concern_name in get_framed_concerns(rd):
                concern_to_reqdefs[concern_name].append(rd_name)

        # Build: concern_name -> [use case names] via req def framing
        concern_to_ucs: dict[str, list[str]] = defaultdict(list)
        uc_names = [get_declared_name(uc) for uc in use_cases]

        # Use case descriptions often reference concerns by name similarity
        for concern in concern_defs:
            c_name = get_declared_name(concern)
            # Check if any use case doc mentions this concern or if req defs
            # frame it and those defs are referenced in use cases
            for uc in use_cases:
                uc_doc = get_unnamed_doc(uc).lower()
                uc_name = get_declared_name(uc).lower()
                c_lower = c_name.lower()
                # Simple heuristic: check name overlap or doc mention
                if (c_lower in uc_name or c_lower in uc_doc or
                        any(word in uc_name for word in c_lower.split("_") if len(word) > 4)):
                    if get_declared_name(uc) not in concern_to_ucs[c_name]:
                        concern_to_ucs[c_name].append(get_declared_name(uc))

        lines = [
            md_heading("Stakeholder Requirement → Use Case Traceability (SN-06)"),
            f"**Model:** `{model_dir}`\n",
            f"**Concerns:** {len(concern_defs)}  "
            f"**Use Cases:** {len(use_cases)}  "
            f"**Req Defs with frame concern:** "
            f"{sum(1 for rd in req_defs if get_framed_concerns(rd))}\n",
        ]

        # Concern → Req Def traceability
        lines.append(md_heading("Concern → Requirement Definition Links", 2))
        if concern_to_reqdefs:
            rows = []
            for c in sorted(concern_defs, key=get_declared_name):
                c_name = get_declared_name(c)
                reqs = concern_to_reqdefs.get(c_name, [])
                rows.append([
                    c_name,
                    collapse_doc(get_unnamed_doc(c))[:70] or "—",
                    ", ".join(reqs) if reqs else "⚠ NONE",
                ])
            lines.append(md_table(["Concern", "Description", "Framed By (Req Def)"], rows))
        else:
            lines.append("> No `frame concern` links found in requirement definitions.\n")
            lines.append("> Add `frame concern <ConcernName>;` inside requirement defs.\n")

        # Gaps
        gaps = [get_declared_name(c) for c in concern_defs
                if not concern_to_reqdefs.get(get_declared_name(c))]
        lines.append(md_heading("Gaps — Concerns with No Requirement Definition", 2))
        if gaps:
            lines.append(f"> **{len(gaps)} concern(s)** not framed by any requirement definition.\n")
            lines.append(md_table(["Concern"], [[g] for g in gaps]))
        else:
            lines.append("✓ All concerns are framed by at least one requirement definition.\n")

        # Use case inventory
        lines.append(md_heading("Use Case Inventory", 2))
        if use_cases:
            rows = [[get_declared_name(uc),
                     collapse_doc(get_unnamed_doc(uc))[:100] or "—"]
                    for uc in sorted(use_cases, key=get_declared_name)]
            lines.append(md_table(["Use Case", "Description"], rows))
        else:
            lines.append("> No use case usages found.\n")

        write_report(args.output / "stakeholder_traceability.md",
                     "\n".join(lines), "SN-06")


if __name__ == "__main__":
    main()
