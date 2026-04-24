"""
use_case_catalog.py — SN-03 Use Case Catalog

Lists all use case usages with actors, descriptions, and include relationships.

Usage: python __Tools/use_case_catalog.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_unnamed_doc, get_def_type_name,
    md_heading, md_table, write_report, collapse_doc,
)
import syside


def get_subject_type(uc) -> str:
    try:
        for member in uc.owned_members.collect():
            if member.isinstance(syside.SubjectMembership.STD):
                sm = member.cast(syside.SubjectMembership.STD)
                for typ in sm.types.collect():
                    return get_declared_name(typ)
    except Exception:
        pass
    return ""


def get_includes(uc) -> list[str]:
    includes = []
    try:
        for member in uc.owned_members.collect():
            if member.isinstance(syside.IncludeUseCaseUsage.STD):
                inc = member.cast(syside.IncludeUseCaseUsage.STD)
                for typ in inc.types.collect():
                    includes.append(get_declared_name(typ))
    except Exception:
        pass
    return includes


def main():
    args = parse_args("SN-03 Use Case Catalog")
    model_dir = args.model_dir

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        use_cases = []
        for top in model.top_elements_from(str(model_dir)):
            collect_typed(top, syside.UseCaseUsage.STD, use_cases)

        lines = [
            md_heading("Use Case Catalog (SN-03)"),
            f"**Model:** `{model_dir}`\n",
            f"**Use cases found:** {len(use_cases)}\n",
        ]

        if not use_cases:
            lines.append("> No use case usages found. "
                         "Populate `02_Core/UseCases/use_case_model.sysml`.\n")
        else:
            # Summary table
            lines.append(md_heading("Summary", 2))
            rows = []
            for uc in sorted(use_cases, key=get_declared_name):
                name = get_declared_name(uc)
                uc_type = get_def_type_name(uc)
                subject = get_subject_type(uc)
                doc = collapse_doc(get_unnamed_doc(uc))[:80]
                includes = get_includes(uc)
                rows.append([
                    name,
                    uc_type or "—",
                    subject or "—",
                    doc or "—",
                    ", ".join(includes) if includes else "—",
                ])
            lines.append(md_table(
                ["Use Case", "Type", "Subject", "Description", "Includes"],
                rows
            ))

            # Details
            lines.append(md_heading("Details", 2))
            for uc in sorted(use_cases, key=get_declared_name):
                name = get_declared_name(uc)
                doc = get_unnamed_doc(uc)
                uc_type = get_def_type_name(uc)
                subject = get_subject_type(uc)
                includes = get_includes(uc)

                lines.append(md_heading(name, 3))
                if uc_type:
                    lines.append(f"**Type:** `{uc_type}`  ")
                if subject:
                    lines.append(f"**Subject:** `{subject}`  ")
                if includes:
                    lines.append(f"**Includes:** {', '.join(f'`{i}`' for i in includes)}  ")
                lines.append("")
                if doc:
                    lines.append(f"{doc}\n")
                else:
                    lines.append("> No description. Add a `doc` block.\n")

        write_report(args.output / "use_case_catalog.md", "\n".join(lines), "SN-03")


if __name__ == "__main__":
    main()
