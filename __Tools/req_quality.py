"""
req_quality.py — SR-06 Requirements Quality Report

Heuristic text checks on requirement doc blocks. All findings are WARNINGs.

Usage: python __Tools/req_quality.py <model_dir> [--output DIR]
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed,
    get_declared_name, get_short_name, get_unnamed_doc, get_named_doc,
    md_heading, md_table, write_report, format_issues_md,
    collapse_doc, is_plain_req, ValidationIssue,
)
try:
    import syside
except ImportError:
    pass

AMBIGUOUS_TERMS = [
    "adequate", "as necessary", "sufficient", "appropriate", "timely",
    "etc.", "and/or", "if applicable", "where applicable",
    "to the extent practicable", "user-friendly", "easy to use",
    "reasonable", "as required",
]
PLACEHOLDER_TERMS = [
    "tbd", "tbi", "tba", "placeholder", "fill in", "to be determined",
    "to be defined", "<replace", "<describe", "<insert",
]


def main():
    args = parse_args("SR-06 Requirements Quality Report")
    cfg  = args.script_config

    ambiguous  = cfg.get("ambiguous_terms", AMBIGUOUS_TERMS)
    min_words  = cfg.get("min_doc_word_count", 8)
    chk_shall  = cfg.get("check_shall_pattern", True)

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        all_reqs = []
        for top in model.top_elements_from(str(args.model_dir)):
            collect_typed(top, syside.RequirementUsage.STD, all_reqs)
        reqs = [r for r in all_reqs if is_plain_req(r)]

        issues = []
        for req in reqs:
            req_id    = get_short_name(req)
            req_name  = get_declared_name(req)
            doc_text  = get_unnamed_doc(req)
            rationale = get_named_doc(req, "Rationale")
            if not doc_text:
                continue

            if chk_shall and not re.search(r"\bshall\b", doc_text, re.IGNORECASE):
                issues.append(ValidationIssue("WARNING", req_id, req_name, "ShallPattern",
                    f"Text lacks 'shall': \"{collapse_doc(doc_text)[:80]}\""))

            wc = len(doc_text.split())
            if wc < min_words:
                issues.append(ValidationIssue("WARNING", req_id, req_name, "TooShort",
                    f"Only {wc} words (min {min_words}): \"{collapse_doc(doc_text)}\""))

            found = [t for t in ambiguous if t.lower() in doc_text.lower()]
            if found:
                issues.append(ValidationIssue("WARNING", req_id, req_name, "AmbiguousTerms",
                    f"Ambiguous terms: {', '.join(repr(t) for t in found)}"))

            if any(p in doc_text.lower() for p in PLACEHOLDER_TERMS):
                issues.append(ValidationIssue("WARNING", req_id, req_name, "PlaceholderText",
                    f"Doc text appears to be a placeholder: \"{collapse_doc(doc_text)[:80]}\""))

            if rationale and any(p in rationale.lower() for p in PLACEHOLDER_TERMS):
                issues.append(ValidationIssue("WARNING", req_id, req_name, "PlaceholderRationale",
                    f"Rationale appears to be a placeholder: \"{collapse_doc(rationale)[:80]}\""))

        warns = sum(1 for i in issues if i.severity == "WARNING")
        lines = [
            md_heading("Requirements Quality Report (SR-06)"),
            f"**Model:** `{args.model_dir}`  \n",
            f"**Requirements checked:** {len(reqs)}  |  **Warnings:** {warns}\n",
            "> All findings are warnings — quality checks are heuristic.\n",
        ]

        by_check: dict = {}
        for issue in issues:
            by_check.setdefault(issue.check, []).append(issue)

        if not issues:
            lines.append("All requirements pass quality checks.\n")
        else:
            for check, ci in sorted(by_check.items()):
                lines.append(md_heading(check, 2))
                lines.append(format_issues_md(ci, check))

        lines.append(md_heading("Summary", 2))
        if by_check:
            rows = [[c, str(len(ci))] for c, ci in sorted(by_check.items())]
            lines.append(md_table(["Check", "Warnings"], rows))
        else:
            lines.append("*No warnings.*\n")

        write_report(args.output / "req_quality.md", "\n".join(lines), "SR-06")


if __name__ == "__main__":
    main()
