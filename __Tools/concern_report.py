#!/usr/bin/env python3
"""
concern_report.py — SysML v2 Stakeholder Concern Report Generator

Scans a SysML v2 model directory for all concern def elements, maps each
concern to its declared stakeholders, then writes one Markdown file per
stakeholder listing their concerns. Shared concerns are documented in each
relevant stakeholder file. Stakeholders defined in the model but with no
concerns produce an empty file and a WARNING on stdout.

Usage:
    python concern_report.py <model_dir>
    python concern_report.py <model_dir> --output <out_dir>
    python concern_report.py <model_dir> --verbose

SysIDE API notes (SysIDE 0.8.x / SysML v2 2025-07):
  - open_model() requires a directory path
  - Traversal: model.top_elements() -> owned_members.collect() (recursive)
  - ConcernDefinition members accessed via owned_members.collect()
  - StakeholderUsage type resolved via feature_typing.collect() -> .type
"""

import argparse
import re
import sys
import textwrap
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import syside
from syside.preview import open_model


# ---------------------------------------------------------------------------
# Model traversal helpers
# ---------------------------------------------------------------------------

def get_name(element) -> str:
    """Return the declared name of an element, or '<unnamed>'."""
    if element is None:
        return "<unnamed>"
    name = element.declared_name
    if name:
        return str(name)
    qn = element.qualified_name
    return str(qn) if qn else "<unnamed>"


def get_doc(element) -> str:
    """Return the first doc comment body on an element, or empty string."""
    try:
        for member in element.owned_members.collect():
            if member.isinstance(syside.Documentation.STD):
                doc = member.cast(syside.Documentation.STD)
                body = doc.body
                if body:
                    text = str(body).strip()
                    # Strip surrounding /* */ if present
                    text = re.sub(r"^/\*\s*", "", text)
                    text = re.sub(r"\s*\*/$", "", text)
                    return text.strip()
    except (AttributeError, TypeError):
        pass
    return ""


def collect_typed(root, std_type, results: list):
    """Depth-first collection of all elements matching std_type."""
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    try:
        if root.isinstance(syside.Namespace.STD):
            ns = root.cast(syside.Namespace.STD)
            for member in ns.owned_members.collect():
                collect_typed(member, std_type, results)
    except (AttributeError, TypeError):
        pass


# ---------------------------------------------------------------------------
# Concern and stakeholder extraction
# ---------------------------------------------------------------------------

class ConcernRecord:
    """Data about one concern def and its stakeholder usages."""

    def __init__(self, name: str, qualified_name: str, doc: str):
        self.name = name
        self.qualified_name = qualified_name
        self.doc = doc
        # List of (usage_name, stakeholder_type_qualified_name) tuples
        self.stakeholder_usages: list[tuple[str, str]] = []

    def stakeholder_keys(self) -> list[str]:
        return [stype for _, stype in self.stakeholder_usages]


def resolve_stakeholder_type_name(stk_usage, debug: bool = False) -> str:
    """
    Given a StakeholderUsage, return the qualified name of its type
    (the StakeholderDefinition / part def it references).

    Tries multiple API paths because the exact path varies by SysIDE version:
      1. feature_typing.collect() -> ft.type
      2. owned_related_elements.collect() looking for FeatureTyping children
      3. direct .type attribute on the usage itself

    Falls back to the usage's declared name if nothing resolves.
    """
    if debug:
        print(f"    [debug resolve_type] usage={get_name(stk_usage)}  pytype={type(stk_usage).__name__}")

    # Path 1: feature_typing collection (standard KerML path)
    try:
        fts = list(stk_usage.feature_typing.collect())
        if debug:
            print(f"      feature_typing count: {len(fts)}")
        for ft in fts:
            typed_by = ft.type
            if debug:
                print(f"        ft.type={typed_by}  pytype={type(typed_by).__name__ if typed_by else 'None'}")
                if typed_by is not None:
                    print(f"        ft.type.qualified_name={typed_by.qualified_name!r}")
                    print(f"        ft.type.declared_name={typed_by.declared_name!r}")
            if typed_by is not None:
                qn = typed_by.qualified_name
                if qn:
                    return str(qn)
                n = typed_by.declared_name
                if n:
                    return str(n)
    except (AttributeError, TypeError) as e:
        if debug:
            print(f"      feature_typing ERROR: {e}")

    # Path 2: owned_relationships — handle both FeatureTyping (`:`) and Subsetting (`::>`).
    #   FeatureTyping: rel.type  -> the typed element (e.g. a part def)
    #   Subsetting:   rel.subsetting_supertype or rel.general -> the referenced element
    try:
        for rel in stk_usage.owned_relationships.collect():
            rtn = type(rel).__name__
            if debug:
                print(f"      owned_rel: {rtn}")

            # FeatureTyping — `stakeholder foo : SomeType`
            if "FeatureTyping" in rtn:
                try:
                    typed_by = rel.type
                    if debug:
                        print(f"        rel.type={typed_by}  pytype={type(typed_by).__name__ if typed_by else 'None'}")
                        if typed_by is not None:
                            print(f"        qualified_name={typed_by.qualified_name!r}  declared_name={typed_by.declared_name!r}")
                    if typed_by is not None:
                        qn = typed_by.qualified_name
                        if qn:
                            return str(qn)
                        n = typed_by.declared_name
                        if n:
                            return str(n)
                except (AttributeError, TypeError) as e:
                    if debug:
                        print(f"        FeatureTyping rel.type ERROR: {e}")

            # ReferenceSubsetting — `stakeholder foo ::> SomeRef`
            elif "ReferenceSubsetting" in rtn:
                for attr in ("reference_subsetting_supertype", "referencedFeature", "general", "subsettedFeature"):
                    try:
                        target = getattr(rel, attr)
                        if debug:
                            print(f"        ReferenceSubsetting .{attr}={target}  pytype={type(target).__name__ if target else 'None'}")
                        if target is not None:
                            qn = target.qualified_name
                            if qn:
                                return str(qn)
                            n = target.declared_name
                            if n:
                                return str(n)
                    except (AttributeError, TypeError) as e:
                        if debug:
                            print(f"        ReferenceSubsetting .{attr} ERROR: {e}")

    except (AttributeError, TypeError) as e:
        if debug:
            print(f"      owned_relationships ERROR: {e}")

    # Path 3: owned_related_elements directly on the usage
    try:
        for child in stk_usage.owned_related_elements.collect():
            ctn = type(child).__name__
            if debug:
                print(f"      owned_related_elements child: {ctn}  name={get_name(child)}")
            if "FeatureTyping" in ctn or "Typing" in ctn:
                try:
                    typed_by = child.type
                    if typed_by is not None:
                        qn = typed_by.qualified_name
                        if qn:
                            return str(qn)
                        n = typed_by.declared_name
                        if n:
                            return str(n)
                except (AttributeError, TypeError):
                    pass
    except (AttributeError, TypeError) as e:
        if debug:
            print(f"      owned_related_elements ERROR: {e}")

    # Path 4: direct .type attribute
    try:
        typed_by = stk_usage.type
        if debug:
            print(f"      direct .type={typed_by}  pytype={type(typed_by).__name__ if typed_by else 'None'}")
        if typed_by is not None:
            if hasattr(typed_by, "collect"):
                for t in typed_by.collect():
                    if debug:
                        print(f"        .type item: qn={t.qualified_name!r}  name={t.declared_name!r}")
                    qn = t.qualified_name
                    if qn:
                        return str(qn)
                    n = t.declared_name
                    if n:
                        return str(n)
            else:
                qn = typed_by.qualified_name
                if qn:
                    return str(qn)
                n = typed_by.declared_name
                if n:
                    return str(n)
    except (AttributeError, TypeError) as e:
        if debug:
            print(f"      direct .type ERROR: {e}")

    fallback = get_name(stk_usage)
    if debug:
        print(f"      → fallback to usage name: {fallback}")
    return fallback


def _is_stakeholder_usage(element) -> bool:
    """
    Return True if element represents a stakeholder usage inside a concern def.

    SysIDE 0.8.x represents `stakeholder foo : SomeType` inside a concern def
    as a PartUsage in the owned_members collection (not StakeholderUsage).
    The other member types in a concern def body are:
      - ReferenceUsage  -> the `subject` declaration
      - Documentation   -> the `doc` comment
    Everything that is a PartUsage or StakeholderUsage is therefore a
    stakeholder member.
    """
    tn = type(element).__name__
    return tn in ("PartUsage", "StakeholderUsage") or "StakeholderUsage" in tn


def collect_concern_defs(model, debug: bool = False) -> list[ConcernRecord]:
    """
    Walk the entire model and collect all ConcernDefinition elements,
    returning a list of ConcernRecord objects populated with their
    StakeholderUsage members.
    """
    concern_defs = []
    for top in model.top_elements():
        collect_typed(top, syside.ConcernDefinition.STD, concern_defs)

    records = []
    for cd in concern_defs:
        name = get_name(cd)
        qname = str(cd.qualified_name) if cd.qualified_name else name
        doc_text = get_doc(cd)
        record = ConcernRecord(name=name, qualified_name=qname, doc=doc_text)

        if debug:
            print(f"  [debug concern] {qname}")

        # Collect StakeholderUsage members owned by this concern def
        try:
            members = list(cd.owned_members.collect())
            if debug:
                print(f"    owned_members count: {len(members)}")
            for member in members:
                mtn = type(member).__name__
                if debug:
                    print(f"    member: {mtn}  name={get_name(member)}")
                if _is_stakeholder_usage(member):
                    # Cast if possible, otherwise use as-is
                    try:
                        stk = member.cast(syside.StakeholderUsage.STD)
                    except (AttributeError, Exception):
                        stk = member
                    usage_name = get_name(stk)
                    stk_type = resolve_stakeholder_type_name(stk, debug=debug)
                    if debug:
                        print(f"      → stakeholder usage '{usage_name}' typed as '{stk_type}'")
                    record.stakeholder_usages.append((usage_name, stk_type))
        except (AttributeError, TypeError) as e:
            if debug:
                print(f"    owned_members ERROR: {e}")

        records.append(record)

    return records


def _collect_by_type_name(root, type_name: str, results: list):
    """
    Depth-first collection of elements whose metaclass name contains
    type_name. Used for types not directly exported on the syside module.
    """
    try:
        tn = type(root).__name__
        if type_name in tn:
            results.append(root)
    except Exception:
        pass
    try:
        if root.isinstance(syside.Namespace.STD):
            ns = root.cast(syside.Namespace.STD)
            for member in ns.owned_members.collect():
                _collect_by_type_name(member, type_name, results)
    except (AttributeError, TypeError):
        pass


def collect_stakeholder_defs(model) -> list[str]:
    """
    Walk the entire model and return qualified names of all
    StakeholderDefinition elements (for zero-concern detection).
    Uses string-based type matching since StakeholderDefinition is not
    directly exported on the syside module.
    """
    stk_defs = []
    for top in model.top_elements():
        _collect_by_type_name(top, "StakeholderDefinition", stk_defs)

    names = []
    for sd in stk_defs:
        try:
            qn = sd.qualified_name
            names.append(str(qn) if qn else get_name(sd))
        except (AttributeError, TypeError):
            names.append(get_name(sd))
    return names


def build_stakeholder_index(
    concerns: list[ConcernRecord],
) -> dict[str, list[ConcernRecord]]:
    """Build mapping: stakeholder_type_qualified_name -> [ConcernRecord, ...]"""
    index: dict[str, list[ConcernRecord]] = defaultdict(list)
    for c in concerns:
        for stk_key in c.stakeholder_keys():
            index[stk_key].append(c)
    return dict(index)


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _safe_filename(stakeholder_name: str) -> str:
    """Convert a qualified stakeholder name to a safe filename stem."""
    safe = re.sub(r"[^A-Za-z0-9]+", "_", stakeholder_name)
    return safe.strip("_") or "unknown_stakeholder"


def render_stakeholder_md(
    stakeholder_name: str,
    concerns: list[ConcernRecord],
) -> str:
    """
    Render a Markdown document for one stakeholder.
    Sections:
      - Exclusive concerns (only this stakeholder)
      - Shared concerns (also listed by other stakeholders, with co-owners named)
      - Warning block if no concerns
    """
    lines = []
    lines.append(f"# Stakeholder Concerns: `{stakeholder_name}`")
    lines.append("")

    if not concerns:
        lines.append(
            "> **⚠ WARNING:** No concerns are declared for this stakeholder."
        )
        return "\n".join(lines)

    # Partition into exclusive vs. shared
    exclusive = []
    shared = []
    for c in concerns:
        other_stks = [s for s in c.stakeholder_keys() if s != stakeholder_name]
        if other_stks:
            shared.append((c, sorted(other_stks)))
        else:
            exclusive.append(c)

    total = len(exclusive) + len(shared)
    lines.append(
        f"**Total concerns:** {total} "
        f"({len(exclusive)} exclusive, {len(shared)} shared)"
    )
    lines.append("")

    # Exclusive concerns
    lines.append("---")
    lines.append("")
    lines.append("## Exclusive Concerns")
    lines.append("")
    if not exclusive:
        lines.append("_No concerns are exclusive to this stakeholder._")
        lines.append("")
    else:
        for c in exclusive:
            lines.append(f"### `{c.name}`")
            lines.append("")
            lines.append(f"**Qualified name:** `{c.qualified_name}`")
            lines.append("")
            if c.doc:
                wrapped = textwrap.fill(c.doc.strip(), width=90)
                lines.append(f"> {wrapped}")
            else:
                lines.append("> _No doc comment._")
            lines.append("")

    # Shared concerns
    lines.append("---")
    lines.append("")
    lines.append("## Shared Concerns")
    lines.append("")
    if not shared:
        lines.append("_No concerns are shared with other stakeholders._")
        lines.append("")
    else:
        for c, other_stks in shared:
            lines.append(f"### `{c.name}`")
            lines.append("")
            lines.append(f"**Qualified name:** `{c.qualified_name}`")
            lines.append("")
            other_formatted = ", ".join(f"`{s}`" for s in other_stks)
            lines.append(f"**Also shared with:** {other_formatted}")
            lines.append("")
            if c.doc:
                wrapped = textwrap.fill(c.doc.strip(), width=90)
                lines.append(f"> {wrapped}")
            else:
                lines.append("> _No doc comment._")
            lines.append("")

    return "\n".join(lines)


def render_summary_md(
    stakeholder_index: dict[str, list[ConcernRecord]],
    all_concerns: list[ConcernRecord],
    warnings: list[str],
) -> str:
    """
    Render a top-level summary Markdown document listing all stakeholders,
    their concern counts, and any warnings.
    """
    lines = []
    lines.append("# Concern Report — Summary")
    lines.append("")
    lines.append(f"**Total concern defs found:** {len(all_concerns)}")
    lines.append(f"**Total stakeholders found:** {len(stakeholder_index)}")
    lines.append("")

    if warnings:
        lines.append("## ⚠ Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("## Stakeholder Coverage")
    lines.append("")
    lines.append("| Stakeholder | Exclusive | Shared | Total |")
    lines.append("|---|---|---|---|")
    for stk, concerns in sorted(stakeholder_index.items()):
        exclusive = sum(
            1 for c in concerns
            if all(s == stk for s in c.stakeholder_keys())
        )
        shared_count = len(concerns) - exclusive
        lines.append(
            f"| `{stk}` | {exclusive} | {shared_count} | {len(concerns)} |"
        )
    lines.append("")

    lines.append("## All Concern Defs")
    lines.append("")
    lines.append("| Concern | Stakeholders |")
    lines.append("|---|---|")
    for c in sorted(all_concerns, key=lambda x: x.qualified_name):
        stks = (
            "<br>".join(f"`{s}`" for s in sorted(c.stakeholder_keys()))
            or "_none_"
        )
        lines.append(f"| `{c.qualified_name}` | {stks} |")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate per-stakeholder concern reports from a SysML v2 model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Output:
              <out_dir>/
                _summary.md            — All stakeholders and concern counts
                <StakeholderName>.md   — One file per stakeholder
        """),
    )
    parser.add_argument(
        "model_dir",
        help="Root directory of the SysML v2 model (.sysml files).",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory for Markdown files. Defaults to __output/ in CWD.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print progress information to stdout.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Dump raw API traversal for concern defs (diagnose stakeholder type resolution).",
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"ERROR: Model directory not found: {model_dir}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output) if args.output else Path.cwd() / "__output"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"[concern_report] Loading model from: {model_dir}")

    with open_model(model_dir) as model:

        diags = model.diagnostics
        if diags.contains_errors():
            print(
                "WARNING: Model loaded with errors. Results may be incomplete.",
                file=sys.stderr,
            )

        if args.verbose:
            print("[concern_report] Scanning for concern defs...")

        concerns = collect_concern_defs(model, debug=args.debug)
        all_stk_def_names = collect_stakeholder_defs(model)

        if args.verbose:
            print(f"[concern_report] Found {len(concerns)} concern def(s).")

    # Build index and detect issues (done outside the model context — data already collected)
    stakeholder_index = build_stakeholder_index(concerns)

    warnings = []

    # Flag concern defs with no stakeholder usages
    for c in concerns:
        if not c.stakeholder_keys():
            msg = f"Concern `{c.qualified_name}` has no stakeholder declarations."
            warnings.append(msg)
            print(f"WARNING: {msg}", file=sys.stderr)

    # Flag stakeholder defs that appear in no concern
    for stk_qn in all_stk_def_names:
        if stk_qn not in stakeholder_index:
            msg = (
                f"Stakeholder `{stk_qn}` is defined in the model "
                f"but has no associated concerns."
            )
            warnings.append(msg)
            print(f"WARNING: {msg}", file=sys.stderr)
            stakeholder_index[stk_qn] = []  # still produce the empty file

    if not concerns:
        print(
            "WARNING: No concern def elements found in the model.",
            file=sys.stderr,
        )

    # Write per-stakeholder Markdown files
    for stk_name, stk_concerns in sorted(stakeholder_index.items()):
        md_content = render_stakeholder_md(stk_name, stk_concerns)
        filename = _safe_filename(stk_name) + ".md"
        out_path = out_dir / filename
        out_path.write_text(md_content, encoding="utf-8")
        if args.verbose:
            status = (
                "⚠ EMPTY" if not stk_concerns
                else f"{len(stk_concerns)} concern(s)"
            )
            print(f"  → {out_path.name}  [{status}]")

    # Write summary file
    summary_content = render_summary_md(stakeholder_index, concerns, warnings)
    summary_path = out_dir / "_summary.md"
    summary_path.write_text(summary_content, encoding="utf-8")
    if args.verbose:
        print(f"  → {summary_path.name}  [summary]")

    warn_count = len(warnings)
    print(
        f"[concern_report] Done. "
        f"{len(stakeholder_index)} stakeholder file(s) written to {out_dir}. "
        f"{warn_count} warning(s)."
    )
    if warn_count > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()