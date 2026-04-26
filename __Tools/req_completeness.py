"""
req_completeness.py — SR-05 Requirements Completeness Gap Report

Checks every RequirementUsage for: short-name ID, unnamed doc block,
doc Rationale block, and duplicate IDs/text.

Usage: python __Tools/req_completeness.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_short_name, get_unnamed_doc, has_doc_rationale,
    md_heading, md_table, write_report, format_issues_md, issues_summary,
    is_plain_req, ValidationIssue,
)
try:
    import syside
except ImportError:
    pass


def main():
    args = parse_args("SR-05 Requirements Completeness Gap Report")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        all_reqs = []
        for top in iter_user_elements(model, args.model_dir):
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)

        reqs = [r for r in all_reqs if is_plain_req(r)]

        issues = []
        id_counts   = defaultdict(list)
        text_counts = defaultdict(list)

        for req in reqs:
            req_id   = get_short_name(req)
            req_name = get_declared_name(req)

            if not req_id:
                issues.append(ValidationIssue("INVALID", "", req_name, "HasId",
                    "No short-name ID. Add <'REQ-NNN'> before the requirement name."))
            else:
                id_counts[req_id].append(req_name)

            doc_text = get_unnamed_doc(req)
            if not doc_text:
                issues.append(ValidationIssue("INVALID", req_id, req_name, "HasText",
                    "No unnamed doc block (normative text missing)."))
            else:
                norm = " ".join(doc_text.split()).lower()
                text_counts[norm].append(req_id or req_name)

            if not has_doc_rationale(req):
                issues.append(ValidationIssue("INVALID", req_id, req_name, "HasRationale",
                    "No 'doc Rationale' block."))

        for sid, names in id_counts.items():
            if len(names) > 1:
                issues.append(ValidationIssue("INVALID", sid, ", ".join(names), "DuplicateId",
                    f"ID '{sid}' used on {len(names)} requirements."))

        for norm, labels in text_counts.items():
            if len(labels) > 1:
                issues.append(ValidationIssue("INVALID", "", ", ".join(labels), "DuplicateText",
                    f"Identical doc text on: {', '.join(labels)}"))

        invalid, warns = issues_summary(issues)
        lines = [
            md_heading("Requirements Completeness Gap Report (SR-05)"),
            f"**Model:** `{args.model_dir}`  \n",
            f"**Requirements found:** {len(reqs)}  |  "
            f"**INVALID:** {invalid}  |  **WARNING:** {warns}\n",
        ]

        by_check: dict = {}
        for issue in issues:
            by_check.setdefault(issue.check, []).append(issue)

        if not issues:
            lines.append("All requirements pass completeness checks.\n")
        else:
            for check, check_issues in sorted(by_check.items()):
                lines.append(md_heading(check, 2))
                lines.append(format_issues_md(check_issues, check))

        lines.append(md_heading("Summary", 2))
        if by_check:
            rows = [[c,
                     str(sum(1 for i in ci if i.severity == "INVALID")),
                     str(sum(1 for i in ci if i.severity == "WARNING"))]
                    for c, ci in sorted(by_check.items())]
            lines.append(md_table(["Check", "INVALID", "WARNING"], rows))
        else:
            lines.append("*No issues.*\n")

        write_report(args.output / "req_completeness.md", "\n".join(lines), "SR-05")
        if invalid > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
