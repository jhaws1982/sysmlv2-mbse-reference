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
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_short_name, get_unnamed_doc,
    md_heading, md_table, write_report, collapse_doc, is_plain_req,
)
try:
    import syside
except ImportError:
    pass


def get_satisfied_req_name(satisfy_usage) -> str:
    """Get the short-name ID of the requirement being satisfied."""
    try:
        r = satisfy_usage.satisfied_requirement
        if r is not None:
            return get_short_name(r) or get_declared_name(r)
    except Exception:
        pass
    return ""


def get_satisfying_element_name(satisfy_usage) -> str:
    """Get the declared name of the feature satisfying the requirement."""
    try:
        sf = satisfy_usage.satisfying_feature
        if sf is not None:
            return get_declared_name(sf) or "—"
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
        for top in iter_user_elements(model, args.model_dir):
            collect_typed(top, syside.SatisfyRequirementUsage.STD, satisfy_usages)
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        plain_reqs = [r for r in all_reqs if is_plain_req(r)]

        # Only keep direct architectural `satisfy req by element;` usages —
        # those with a non-None satisfying_feature. Verification-case satisfy
        # claims (nested inside VerificationCaseUsage) have satisfying_feature=None.
        def _has_satisfying_feature(su) -> bool:
            try:
                return su.satisfying_feature is not None
            except Exception:
                return False

        direct_satisfies = [su for su in satisfy_usages if _has_satisfying_feature(su)]

        # Build req_id -> [satisfying elements]
        req_to_elements: dict = defaultdict(list)
        for su in direct_satisfies:
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
            f"**Satisfy links:** {len(direct_satisfies)}  "
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
