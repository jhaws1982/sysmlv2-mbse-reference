"""
req_traceability.py — SR-03 Stakeholder Requirement -> System Requirement Traceability

Maps requirement definitions that use 'frame concern' back to the concerns
they address, and shows which system requirement usages implement each def.

Usage: python __Tools/req_traceability.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_short_name, get_unnamed_doc, get_def_type_name,
    md_heading, md_table, write_report, collapse_doc, is_plain_req,
)
try:
    import syside
except ImportError:
    pass


def get_framed_concern_names(req_def) -> list:
    names = []
    try:
        for member in req_def.owned_members.collect():
            if member.isinstance(syside.ConcernUsage.STD):
                name = get_declared_name(member)
                if name:
                    names.append(name)
    except Exception:
        pass
    return names


def get_def_name_of_usage(req_usage) -> str:
    try:
        for typ in req_usage.types.collect():
            name = get_declared_name(typ)
            if name:
                return name
    except Exception:
        pass
    return ""


def main():
    args = parse_args("SR-03 Stakeholder->System Requirement Traceability")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        req_defs    = []
        req_usages  = []
        concern_defs = []
        for top in iter_user_elements(model, args.model_dir):
            collect_typed(top, syside.RequirementDefinition.STD, req_defs)
            collect_typed(top, syside.RequirementUsage.STD, req_usages)
            collect_typed(top, syside.ConcernDefinition.STD, concern_defs)

        # Filter req_defs to those with frame concerns (exclude ConcernDefinition)
        req_defs = [d for d in req_defs
                    if not d.isinstance(syside.ConcernDefinition.STD)]
        req_usages = [r for r in req_usages if is_plain_req(r)]

        # Build: def_name -> [usage]
        def_to_usages: dict = defaultdict(list)
        for usage in req_usages:
            def_name = get_def_name_of_usage(usage)
            if def_name:
                def_to_usages[def_name].append(usage)

        # Build: concern_name -> [req_def]
        concern_to_defs: dict = defaultdict(list)
        for rd in req_defs:
            for c_name in get_framed_concern_names(rd):
                concern_to_defs[c_name].append(rd)

        lines = [
            md_heading("Stakeholder -> System Requirement Traceability (SR-03)"),
            f"**Model:** `{args.model_dir}`\n",
            f"**Requirement defs:** {len(req_defs)}  "
            f"**Requirement usages:** {len(req_usages)}  "
            f"**Concerns:** {len(concern_defs)}\n",
        ]

        # Concern -> Req Def -> Req Usage chain
        lines.append(md_heading("Concern -> Requirement Traceability Chain", 2))
        if concern_to_defs:
            rows = []
            for c in sorted(concern_defs, key=get_declared_name):
                c_name = get_declared_name(c)
                defs = concern_to_defs.get(c_name, [])
                for rd in defs:
                    rd_name = get_declared_name(rd)
                    usages = def_to_usages.get(rd_name, [])
                    usage_ids = ", ".join(
                        get_short_name(u) or get_declared_name(u)
                        for u in usages
                    ) or "—"
                    rows.append([c_name, rd_name, usage_ids])
                if not defs:
                    rows.append([c_name, "—", "— NO REQUIREMENT DEF"])
            lines.append(md_table(["Concern", "Req Def", "Req Usages (IDs)"], rows))
        else:
            lines.append("> No `frame concern` links found in requirement definitions.\n")

        # Req Def coverage
        lines.append(md_heading("Requirement Definition Coverage", 2))
        rows = []
        for rd in sorted(req_defs, key=get_declared_name):
            rd_name = get_declared_name(rd)
            concerns = get_framed_concern_names(rd)
            usages = def_to_usages.get(rd_name, [])
            usage_ids = ", ".join(
                get_short_name(u) or get_declared_name(u) for u in usages
            ) or "NONE"
            rows.append([
                rd_name,
                ", ".join(concerns) if concerns else "NONE",
                usage_ids,
            ])
        if rows:
            lines.append(md_table(["Req Def", "Framed Concerns", "Declared Usages"], rows))
        else:
            lines.append("> No requirement definitions found.\n")

        # Gaps
        unframed = [get_declared_name(rd) for rd in req_defs
                    if not get_framed_concern_names(rd)]
        unimplemented = [get_declared_name(rd) for rd in req_defs
                         if not def_to_usages.get(get_declared_name(rd))]

        if unframed or unimplemented:
            lines.append(md_heading("Gaps", 2))
            if unframed:
                lines.append(f"**Req defs with no framed concern ({len(unframed)}):**\n")
                lines.append(md_table(["Req Def"], [[n] for n in unframed]))
            if unimplemented:
                lines.append(f"**Req defs with no usage ({len(unimplemented)}):**\n")
                lines.append(md_table(["Req Def"], [[n] for n in unimplemented]))
        else:
            lines.append("All requirement defs are framed and have at least one usage.\n")

        write_report(args.output / "req_traceability.md", "\n".join(lines), "SR-03")


if __name__ == "__main__":
    main()
