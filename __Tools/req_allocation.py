"""
req_allocation.py — LA-05 Requirements Allocation Matrix

Reports satisfy links from RequirementAllocations and verification blocks,
showing which architectural elements are claimed to satisfy each requirement.

Usage: python __Tools/req_allocation.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_short_name, get_unnamed_doc,
    md_heading, md_table, write_report, collapse_doc, is_plain_req,
)
try:
    import syside
except ImportError:
    pass


def get_satisfied_req_name(satisfy_usage) -> str:
    """Get the name of the requirement being satisfied."""
    try:
        for r in satisfy_usage.satisfied_requirements.collect():
            return get_short_name(r) or get_declared_name(r)
    except Exception:
        pass
    # Fallback: check referenced requirement name in the usage
    try:
        for member in satisfy_usage.owned_members.collect():
            if member.isinstance(syside.RequirementUsage.STD):
                return get_short_name(member) or get_declared_name(member)
    except Exception:
        pass
    return ""


def get_satisfying_element_name(satisfy_usage) -> str:
    """Get the name of the element doing the satisfying (subject or owner)."""
    try:
        for m in satisfy_usage.owned_members.collect():
            if m.isinstance(syside.SubjectMembership.STD):
                sm = m.cast(syside.SubjectMembership.STD)
                for typ in sm.types.collect():
                    name = get_declared_name(typ)
                    if name:
                        return name
    except Exception:
        pass
    try:
        owner = satisfy_usage.owner
        if owner:
            return get_declared_name(owner)
    except Exception:
        pass
    return "—"


def main():
    args = parse_args("LA-05 Requirements Allocation Matrix")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        # Collect all satisfy usages and requirement usages
        satisfy_usages = []
        all_reqs       = []
        for top in model.top_elements_from(str(args.model_dir)):
            collect_typed(top, syside.SatisfyRequirementUsage.STD, satisfy_usages)
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        plain_reqs = [r for r in all_reqs if is_plain_req(r)]

        # Build req_id -> [satisfying elements]
        req_to_elements: dict = defaultdict(list)
        for su in satisfy_usages:
            req_name = get_satisfied_req_name(su)
            elem_name = get_satisfying_element_name(su)
            if req_name:
                req_to_elements[req_name].append(elem_name)

        # Build all req IDs from the model
        all_req_ids = {}
        for req in plain_reqs:
            req_id = get_short_name(req) or get_declared_name(req)
            all_req_ids[req_id] = req

        allocated   = {r for r in req_to_elements if req_to_elements[r]}
        unallocated = [rid for rid in sorted(all_req_ids) if rid not in allocated]

        lines = [
            md_heading("Requirements Allocation Matrix (LA-05)"),
            f"**Model:** `{args.model_dir}`\n",
            f"**Requirements:** {len(all_req_ids)}  "
            f"**Satisfy links:** {len(satisfy_usages)}  "
            f"**Allocated:** {len(allocated)}  "
            f"**Unallocated:** {len(unallocated)}\n",
        ]

        # Allocation matrix
        lines.append(md_heading("Allocation Matrix", 2))
        if req_to_elements:
            rows = []
            for req_id in sorted(req_to_elements):
                elements = req_to_elements[req_id]
                req_doc = ""
                req = all_req_ids.get(req_id)
                if req:
                    req_doc = collapse_doc(get_unnamed_doc(req))[:60]
                rows.append([
                    req_id,
                    req_doc or "—",
                    ", ".join(sorted(set(elements))),
                ])
            lines.append(md_table(["Requirement", "Summary", "Allocated To"], rows))
        else:
            lines.append("> No `satisfy` links found.\n")
            lines.append("> Add `satisfy requirement X by Y;` in "
                         "`02_Core/Allocations/req_allocations.sysml`.\n")

        # Unallocated requirements
        lines.append(md_heading("Unallocated Requirements", 2))
        if unallocated:
            lines.append(f"> **{len(unallocated)} requirement(s)** have no allocation.\n")
            rows = []
            for rid in unallocated:
                req = all_req_ids.get(rid)
                doc = collapse_doc(get_unnamed_doc(req))[:80] if req else ""
                rows.append([rid, doc or "—"])
            lines.append(md_table(["Requirement", "Summary"], rows))
        else:
            lines.append("All requirements have at least one allocation.\n")

        write_report(args.output / "req_allocation.md", "\n".join(lines), "LA-05")


if __name__ == "__main__":
    main()
