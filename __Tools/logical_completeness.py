"""
logical_completeness.py — LA-06 Logical Architecture Completeness

Gap report for the logical architecture layer:
  - Part defs missing doc blocks
  - Action defs with no perform link
  - Port defs with no directional features
  - Requirements with no satisfy link

Usage: python __Tools/logical_completeness.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_unnamed_doc, get_short_name,
    md_heading, md_table, write_report, is_plain_req,
    ValidationIssue, format_issues_md, issues_summary,
)
try:
    import syside
except ImportError:
    pass


def in_logical_or_alloc(element) -> bool:
    try:
        owner = element.owner
        while owner is not None:
            n = get_declared_name(owner)
            if n and any(k in n for k in (
                "Logical", "Feature", "CoreSystem",
                "Allocation", "Interface", "Behavior",
                "StateMachine", "ActionSequence",
            )):
                return True
            owner = getattr(owner, "owner", None)
    except Exception:
        pass
    return False


def has_perform_link(action_def, model, model_dir) -> bool:
    """Check if any PerformActionUsage references this action def."""
    ad_name = get_declared_name(action_def)
    try:
        all_perform = []
        for top in model.top_elements_from(str(model_dir)):
            collect_typed(top, syside.PerformActionUsage.STD, all_perform)
        for p in all_perform:
            try:
                for typ in p.cast(syside.PerformActionUsage.STD).types.collect():
                    if get_declared_name(typ) == ad_name:
                        return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def get_port_directional_count(port_def) -> int:
    count = 0
    try:
        for m in port_def.owned_members.collect():
            try:
                d = str(getattr(m, "direction", "")).lower()
                if "in" in d or "out" in d:
                    count += 1
            except Exception:
                pass
    except Exception:
        pass
    return count


def main():
    args = parse_args("LA-06 Logical Architecture Completeness")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        part_defs    = []
        action_defs  = []
        port_defs    = []
        all_reqs     = []
        satisfy_uses = []

        for top in model.top_elements_from(str(args.model_dir)):
            collect_typed(top, syside.PartDefinition.STD, part_defs)
            collect_typed(top, syside.ActionDefinition.STD, action_defs)
            collect_typed(top, syside.PortDefinition.STD, port_defs)
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)
            collect_typed(top, syside.SatisfyRequirementUsage.STD, satisfy_uses)

        # Scope to logical layer
        logical_parts   = [p for p in part_defs if in_logical_or_alloc(p)]
        logical_actions = [a for a in action_defs if in_logical_or_alloc(a)]
        logical_ports   = [p for p in port_defs if in_logical_or_alloc(p)]
        plain_reqs      = [r for r in all_reqs if is_plain_req(r)]

        # Build satisfied req set
        satisfied_req_ids = set()
        for su in satisfy_uses:
            try:
                for r in su.satisfied_requirements.collect():
                    rid = get_short_name(r) or get_declared_name(r)
                    satisfied_req_ids.add(rid)
            except Exception:
                pass

        issues = []

        # Check 1: part defs without doc
        for pd in logical_parts:
            name = get_declared_name(pd)
            if not get_unnamed_doc(pd):
                issues.append(ValidationIssue("WARNING", "", name, "PartDefMissingDoc",
                    "Part def has no doc block."))

        # Check 2: action defs with no perform link
        for ad in logical_actions:
            name = get_declared_name(ad)
            if not has_perform_link(ad, model, args.model_dir):
                issues.append(ValidationIssue("WARNING", "", name, "ActionDefNoPerformLink",
                    "Action def is not referenced by any perform link."))

        # Check 3: port defs with no directional features
        for pd in logical_ports:
            name = get_declared_name(pd)
            if get_port_directional_count(pd) == 0:
                issues.append(ValidationIssue("WARNING", "", name, "PortDefNoFeatures",
                    "Port def has no in/out directional features."))

        # Check 4: requirements with no satisfy link
        for req in plain_reqs:
            req_id = get_short_name(req) or get_declared_name(req)
            if req_id not in satisfied_req_ids:
                issues.append(ValidationIssue("WARNING", req_id,
                    get_declared_name(req), "RequirementNotAllocated",
                    "No satisfy link found for this requirement."))

        invalid, warns = issues_summary(issues)
        lines = [
            md_heading("Logical Architecture Completeness (LA-06)"),
            f"**Model:** `{args.model_dir}`\n",
            f"**Logical part defs:** {len(logical_parts)}  "
            f"**Action defs:** {len(logical_actions)}  "
            f"**Port defs:** {len(logical_ports)}  "
            f"**Requirements:** {len(plain_reqs)}\n",
            f"**INVALID:** {invalid}  |  **WARNING:** {warns}\n",
        ]

        by_check: dict = {}
        for issue in issues:
            by_check.setdefault(issue.check, []).append(issue)

        if not issues:
            lines.append("All logical architecture elements pass completeness checks.\n")
        else:
            for check, check_issues in sorted(by_check.items()):
                lines.append(md_heading(check, 2))
                lines.append(format_issues_md(check_issues, check))

        # Summary
        lines.append(md_heading("Summary", 2))
        if by_check:
            rows = [[c,
                     str(sum(1 for i in ci if i.severity == "INVALID")),
                     str(sum(1 for i in ci if i.severity == "WARNING"))]
                    for c, ci in sorted(by_check.items())]
            lines.append(md_table(["Check", "INVALID", "WARNING"], rows))
        else:
            lines.append("*No issues.*\n")

        write_report(args.output / "logical_completeness.md",
                     "\n".join(lines), "LA-06")


if __name__ == "__main__":
    main()
