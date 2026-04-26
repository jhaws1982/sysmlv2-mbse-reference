"""
stakeholder_register.py — SN-01 Stakeholder Register

Lists all stakeholder role definitions and their concerns.
Groups concerns by stakeholder for easy review.

Usage: python __Tools/stakeholder_register.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_unnamed_doc,
    md_heading, md_table, write_report, collapse_doc,
)
import syside


def get_actor_type_name(concern) -> str:
    """Return the first user-defined type name of the actor PartUsage in a concern def.

    `actor op : PrimaryOperator;` creates a PartUsage with declared_name='op'
    and types=['PrimaryOperator', 'Part', ...]. Skip ReferenceUsage (subject)
    and Documentation, then take the first non-stdlib type of any PartUsage.
    """
    try:
        for member in concern.owned_members.collect():
            if not member.isinstance(syside.PartUsage.STD):
                continue
            for typ in member.types.collect():
                name = get_declared_name(typ)
                if name and name not in ("Part", "Anything"):
                    return name
    except Exception:
        pass
    return ""


def main():
    args = parse_args("SN-01 Stakeholder Register")
    model_dir = args.model_dir

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        # Collect part defs (stakeholder roles) and concern defs
        part_defs = []
        concern_defs = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.PartDefinition.STD, part_defs)
            collect_typed(top, syside.ConcernDefinition.STD, concern_defs)

        # Filter to stakeholder-named part defs (heuristic: in Stakeholder packages)
        stakeholders = []
        for pd in part_defs:
            try:
                owner = pd.owner
                while owner is not None:
                    name = get_declared_name(owner)
                    if name and "Stakeholder" in name:
                        stakeholders.append(pd)
                        break
                    owner = getattr(owner, "owner", None)
            except Exception:
                pass

        # Map actor type name -> concerns
        concerns_by_actor: dict[str, list] = defaultdict(list)
        for concern in concern_defs:
            actor_name = get_actor_type_name(concern)
            concerns_by_actor[actor_name].append(concern)

        # Build report
        lines = [
            md_heading("Stakeholder Register (SN-01)"),
            f"**Model:** `{model_dir}`\n",
            f"**Stakeholder roles found:** {len(stakeholders)}  "
            f"**Concerns found:** {len(concern_defs)}\n",
        ]

        if not stakeholders:
            lines.append("> No stakeholder part defs found. "
                         "Populate `01_Stakeholders/Stakeholders.sysml`.\n")
        else:
            # Summary table
            lines.append(md_heading("Stakeholder Summary", 2))
            rows = []
            for sh in sorted(stakeholders, key=get_declared_name):
                sh_name = get_declared_name(sh)
                doc = collapse_doc(get_unnamed_doc(sh))[:80]
                n_concerns = len(concerns_by_actor.get(sh_name, []))
                rows.append([sh_name, doc or "—", str(n_concerns)])
            lines.append(md_table(["Stakeholder", "Description", "Concerns"], rows))

            # Detail sections
            lines.append(md_heading("Stakeholder Details", 2))
            for sh in sorted(stakeholders, key=get_declared_name):
                sh_name = get_declared_name(sh)
                doc = get_unnamed_doc(sh)
                lines.append(md_heading(sh_name, 3))
                if doc:
                    lines.append(f"{doc}\n")
                related = concerns_by_actor.get(sh_name, [])
                if related:
                    concern_rows = []
                    for c in sorted(related, key=get_declared_name):
                        concern_rows.append([
                            get_declared_name(c),
                            collapse_doc(get_unnamed_doc(c))[:100] or "—",
                        ])
                    lines.append(md_table(["Concern", "Description"], concern_rows))
                else:
                    lines.append("> No concerns linked to this stakeholder.\n")

        # All concerns (including those not linked to a known stakeholder)
        lines.append(md_heading("All Concerns", 2))
        if concern_defs:
            rows = []
            for c in sorted(concern_defs, key=get_declared_name):
                actor = get_actor_type_name(c) or "—"
                doc = collapse_doc(get_unnamed_doc(c))[:100]
                rows.append([get_declared_name(c), actor, doc or "—"])
            lines.append(md_table(["Concern", "Actor", "Description"], rows))
        else:
            lines.append("> No concern definitions found.\n")

        write_report(args.output / "stakeholder_register.md", "\n".join(lines), "SN-01")


if __name__ == "__main__":
    main()
