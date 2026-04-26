"""
dependency_map.py

Maps executables and software artifacts to their dependencies as declared
in a SysML v2 model using `dependency X to Y` relationships.

Reports:
  1. Forward map: each artifact and what it depends on
  2. Reverse map: each capability/library and what depends on it
  3. Unused targets: defined but not referenced by anything
  4. Summary counts

Also writes a Markdown file with the full report.

Usage:
    python dependency_map.py path/to/model.sysml
    python dependency_map.py path/to/model/
    python dependency_map.py path/to/model.sysml --output path/to/report.md

Model conventions expected:
  - Base kind types declared at top level:
      part def capability; part def executable; part def sharedLib;
      part def staticLib;  part def thirdPartyLib; part def ifc;
  - Concrete artifacts specialize these base types:
      part def adsb_ifc :> executable { ... }
  - Dependencies declared inside the part def body:
      dependency adsb_ifc to capabilities::CapNetwork;

SysIDE API notes (SysIDE 0.8.x / SysML v2 2025-07):
  - open_model() requires a directory; top_elements_from() accepts file or dir
  - dependency X to Y inside a part def body is stored as:
      PartDefinition.owned_relationships
        -> OwningMembership
            -> owned_related_elements[0]  (Dependency)
                -> .suppliers  (DependencyEnds -- iterate directly, no .collect())
  - DependencyEnds does NOT support .collect() -- iterate directly with for..in
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import iter_user_elements, collect_user_sysml_files
from collections import defaultdict
import syside
from syside.preview import open_model


# ── Kind definitions ──────────────────────────────────────────────────────────

# Display order for all sections
KIND_BASES = ["executable", "ifc", "sharedLib", "staticLib", "thirdPartyLib",
              "capability"]

KIND_LABELS = {
    "executable":    "Executable",
    "ifc":           "Interface Adapter",
    "sharedLib":     "Shared Library",
    "staticLib":     "Static Library",
    "thirdPartyLib": "Third-Party Library",
    "capability":    "Capability",
}

KIND_PLURAL = {
    "executable":    "Executables",
    "ifc":           "Interface Adapters",
    "sharedLib":     "Shared Libraries",
    "staticLib":     "Static Libraries",
    "thirdPartyLib": "Third-Party Libraries",
    "capability":    "Capabilities",
}

# Kinds that can appear as the TARGET of a dependency (the `to` side)
DEPENDENCY_TARGET_KINDS = {"capability", "sharedLib", "staticLib", "thirdPartyLib"}

# Kinds that can appear as the SOURCE of a dependency (the artifact doing the depending)
DEPENDENCY_SOURCE_KINDS = {"executable", "ifc", "sharedLib", "staticLib"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_name(element) -> str:
    if element is None:
        return "<none>"
    name = element.declared_name
    if name:
        return name
    qn = element.qualified_name
    return str(qn) if qn else "<unnamed>"


def collect_typed(root, std_type: type, results: list):
    """Depth-first collection of all elements matching std_type."""
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            collect_typed(member, std_type, results)


def resolve_kind(part_def: syside.PartDefinition) -> str | None:
    """
    Return the base kind name for a PartDefinition by walking
    owned_specializations up to two levels deep.
    Returns None for the base kind definitions themselves (they specialize 'Part').
    """
    try:
        for spec in part_def.owned_specializations.collect():
            general = spec.general
            if general is None:
                continue
            general_name = get_name(general)
            if general_name in KIND_BASES:
                return general_name
            # One level of indirection (e.g. part def myIfc :> ifc :> executable)
            if general.isinstance(syside.PartDefinition.STD):
                gp = general.cast(syside.PartDefinition.STD)
                for gspec in gp.owned_specializations.collect():
                    gg = gspec.general
                    if gg is not None and get_name(gg) in KIND_BASES:
                        return get_name(gg)
    except Exception:
        pass
    return None


def get_dependencies_from_part_def(part_def: syside.PartDefinition) -> list[str]:
    """
    Return the names of all dependency targets declared inside this part def.

    In SysIDE 0.8.x, `dependency X to Y` inside a part def body is stored as:
      PartDefinition.owned_relationships
        -> OwningMembership
            -> owned_related_elements[0]  (Dependency)
                -> .suppliers  (DependencyEnds -- iterate directly, no .collect())
    """
    deps: list[str] = []
    try:
        for rel in part_def.owned_relationships.collect():
            if rel.isinstance(syside.Dependency.STD):
                # Direct dependency (top-level statement)
                dep = rel.cast(syside.Dependency.STD)
                for supplier in dep.suppliers:
                    n = get_name(supplier)
                    if n and n not in ("<none>", "<unnamed>"):
                        deps.append(n)
            else:
                # Unwrap OwningMembership to find the Dependency inside
                try:
                    for child in rel.owned_related_elements.collect():
                        if child.isinstance(syside.Dependency.STD):
                            dep = child.cast(syside.Dependency.STD)
                            for supplier in dep.suppliers:
                                n = get_name(supplier)
                                if n and n not in ("<none>", "<unnamed>"):
                                    deps.append(n)
                except Exception:
                    pass
    except Exception:
        pass
    return sorted(deps)


# ── Markdown output ───────────────────────────────────────────────────────────

def write_markdown(
    output_path: Path,
    by_kind: dict,
    reverse_map: dict,
    all_targets: dict,
    all_referenced: set,
    source_file: str,
):
    """Write the full dependency report to a Markdown file."""

    unused = {
        name: kind
        for name, kind in all_targets.items()
        if name not in all_referenced
    }

    lines = []
    lines.append("# Dependency Map Report")
    lines.append(f"\n**Source:** `{source_file}`\n")

    # ── Section 1: Summary ────────────────────────────────────────────────
    lines.append("---")
    lines.append("\n## Summary\n")
    lines.append("| Kind | Count | Unused |")
    lines.append("|---|---|---|")
    for kind in KIND_BASES:
        if kind not in by_kind:
            continue
        count = len(by_kind[kind])
        unused_count = sum(
            1 for name, _ in by_kind[kind]
            if name in all_targets and name not in all_referenced
        )
        unused_cell = f"⚠️ {unused_count}" if unused_count else "✅ 0"
        lines.append(f"| {KIND_PLURAL[kind]} | {count} | {unused_cell} |")
    lines.append("")

    # ── Section 2: Unused targets ─────────────────────────────────────────
    lines.append("---")
    lines.append("\n## Unused Dependency Targets\n")

    if unused:
        by_unused_kind: dict[str, list[str]] = defaultdict(list)
        for name, kind in unused.items():
            by_unused_kind[kind].append(name)

        lines.append(f"> ⚠️ **{len(unused)} target(s) defined but not referenced.**\n")
        for kind in KIND_BASES:
            if kind not in by_unused_kind:
                continue
            lines.append(f"### {KIND_PLURAL[kind]}\n")
            lines.append("| Unused Target |")
            lines.append("|---|")
            for name in sorted(by_unused_kind[kind]):
                lines.append(f"| `{name}` |")
            lines.append("")
    else:
        lines.append("✅ All defined targets are referenced by at least one artifact.\n")

    # ── Section 3: Forward map ────────────────────────────────────────────
    lines.append("---")
    lines.append("\n## Forward Map — Artifact → Dependencies\n")

    source_kinds = [k for k in KIND_BASES if k in by_kind and k in DEPENDENCY_SOURCE_KINDS]
    if not source_kinds:
        lines.append("_No dependency sources found._\n")
    else:
        for kind in source_kinds:
            entries = sorted(by_kind[kind], key=lambda x: x[0])
            lines.append(f"### {KIND_PLURAL[kind]}\n")
            lines.append("| Artifact | Depends On | Type |")
            lines.append("|---|---|---|")
            for name, deps in entries:
                if deps:
                    for i, dep in enumerate(deps):
                        dep_kind = all_targets.get(dep, "")
                        kind_label = KIND_LABELS.get(dep_kind, "") if dep_kind else ""
                        art_col = f"`{name}`" if i == 0 else ""
                        lines.append(f"| {art_col} | `{dep}` | {kind_label} |")
                else:
                    lines.append(f"| `{name}` | _(none)_ | |")
            lines.append("")

    # ── Section 4: Reverse map ────────────────────────────────────────────
    lines.append("---")
    lines.append("\n## Reverse Map — Dependency Target → Used By\n")

    target_kinds_present = [
        k for k in KIND_BASES
        if k in DEPENDENCY_TARGET_KINDS and k in by_kind
    ]

    if not target_kinds_present:
        lines.append("_No dependency targets found._\n")
    else:
        for kind in target_kinds_present:
            entries = sorted(by_kind[kind], key=lambda x: x[0])
            lines.append(f"### {KIND_PLURAL[kind]}\n")
            lines.append("| Target | Used By | Status |")
            lines.append("|---|---|---|")
            for name, _ in entries:
                users = sorted(reverse_map.get(name, []))
                if users:
                    used_by_str = ", ".join(f"`{u}`" for u in users)
                    lines.append(f"| `{name}` | {used_by_str} | ✅ In use |")
                else:
                    lines.append(f"| `{name}` | | ⚠️ UNUSED |")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nMarkdown written to: {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def run(model_dir: Path, output_dir: Path):

    source_label = str(model_dir)
    print(f"Loading model from: {model_dir}\n")

    with open_model(collect_user_sysml_files(model_dir), allow_errors=True) as model:

        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")
        for msg in diags.warnings:
            print(f"  WARNING: {msg}")

        # ── Collect and classify ──────────────────────────────────────────
        all_part_defs: list = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.PartDefinition.STD, all_part_defs)

        # by_kind[kind] = list of (name, [dep_names])
        by_kind: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
        # All artifacts that can be depended upon: name -> kind
        all_targets: dict[str, str] = {}

        for pd in all_part_defs:
            name = get_name(pd)
            if name in ("<none>", "<unnamed>"):
                continue
            kind = resolve_kind(pd)
            if kind is None:
                continue  # base type defs themselves -- skip

            if kind in DEPENDENCY_TARGET_KINDS:
                all_targets[name] = kind

            if kind in DEPENDENCY_SOURCE_KINDS:
                deps = get_dependencies_from_part_def(pd)
                by_kind[kind].append((name, deps))
            elif kind == "capability":
                by_kind[kind].append((name, []))
            elif kind in DEPENDENCY_TARGET_KINDS:
                # e.g. a thirdPartyLib -- target only, no deps of its own
                by_kind[kind].append((name, []))

        # Build reverse map: target_name -> sorted list of artifacts that use it
        reverse_map: dict[str, list[str]] = defaultdict(list)
        all_referenced: set[str] = set()
        for kind_entries in by_kind.values():
            for art_name, deps in kind_entries:
                for dep in deps:
                    reverse_map[dep].append(art_name)
                    all_referenced.add(dep)

        # ── Section 1: Forward map ────────────────────────────────────────
        print("═" * 62)
        print("  FORWARD MAP — Artifact → Dependencies")
        print("═" * 62)

        source_kinds = [k for k in KIND_BASES if k in by_kind and k in DEPENDENCY_SOURCE_KINDS]
        if not source_kinds:
            print("\n  (no dependency sources found)")
        else:
            for kind in source_kinds:
                entries = sorted(by_kind[kind], key=lambda x: x[0])
                print(f"\n▶ {KIND_PLURAL[kind]} ({len(entries)})")
                print("─" * 50)
                for name, deps in entries:
                    if deps:
                        print(f"  {name}")
                        for dep in deps:
                            dep_kind = all_targets.get(dep, "")
                            kind_tag = f"  [{KIND_LABELS.get(dep_kind, dep_kind)}]" if dep_kind else ""
                            print(f"    → {dep}{kind_tag}")
                    else:
                        print(f"  {name}  (no dependencies declared)")

        # ── Section 2: Reverse map ────────────────────────────────────────
        print()
        print("═" * 62)
        print("  REVERSE MAP — Dependency Target → Used By")
        print("═" * 62)

        target_kinds_present = [
            k for k in KIND_BASES
            if k in DEPENDENCY_TARGET_KINDS and k in by_kind
        ]

        if not target_kinds_present:
            print("\n  (no dependency targets found)")
        else:
            for kind in target_kinds_present:
                entries = sorted(by_kind[kind], key=lambda x: x[0])
                print(f"\n▶ {KIND_PLURAL[kind]} ({len(entries)})")
                print("─" * 50)
                for name, _ in entries:
                    users = sorted(reverse_map.get(name, []))
                    if users:
                        print(f"  {name}  <- used by: {', '.join(users)}")
                    else:
                        print(f"  {name}  <- UNUSED")

        # ── Section 3: Unused targets ─────────────────────────────────────
        unused = {
            name: kind
            for name, kind in all_targets.items()
            if name not in all_referenced
        }

        print()
        print("═" * 62)
        print("  UNUSED DEPENDENCY TARGETS")
        print("═" * 62)

        if unused:
            by_unused_kind: dict[str, list[str]] = defaultdict(list)
            for name, kind in unused.items():
                by_unused_kind[kind].append(name)
            print(f"\n  {len(unused)} target(s) defined but not referenced:\n")
            for kind in KIND_BASES:
                if kind not in by_unused_kind:
                    continue
                print(f"  {KIND_PLURAL[kind]}:")
                for name in sorted(by_unused_kind[kind]):
                    print(f"    - {name}")
        else:
            print("\n  All defined targets are referenced by at least one artifact.")

        # ── Section 4: Summary ────────────────────────────────────────────
        print()
        print("═" * 62)
        print("  SUMMARY")
        print("═" * 62)
        for kind in KIND_BASES:
            if kind in by_kind:
                count = len(by_kind[kind])
                unused_count = sum(
                    1 for name, _ in by_kind[kind]
                    if name in all_targets and name not in all_referenced
                )
                unused_str = f"  ({unused_count} unused)" if unused_count else ""
                print(f"  {KIND_PLURAL[kind]}:  {count}{unused_str}")

        # ── Write Markdown ────────────────────────────────────────────────
        md_path = output_dir / "dependency_map.md"
        write_markdown(
            output_path=md_path,
            by_kind=by_kind,
            reverse_map=reverse_map,
            all_targets=all_targets,
            all_referenced=all_referenced,
            source_file=source_label,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Map executables and artifacts to their declared dependencies."
    )
    parser.add_argument(
        "model_dir",
        help="Path to model root directory"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory (default: __output in current working directory)"
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    if not model_dir.is_dir():
        print(f"Error: '{model_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else Path.cwd() / "__output"
    output_dir.mkdir(parents=True, exist_ok=True)

    run(model_dir, output_dir)
