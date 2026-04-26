"""
behavioral_summary.py — LA-04 Behavioral Summary

Inventories action defs, state defs, and perform links from the Behavior
packages (StateMachines, ActionSequences) and logical architecture model.

Usage: python __Tools/behavioral_summary.py <model_dir> [--output DIR]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tool_utils import (
    parse_args, load_model, collect_typed, iter_user_elements,
    get_declared_name, get_unnamed_doc,
    md_heading, md_table, write_report, collapse_doc,
)
try:
    import syside
except ImportError:
    pass


def get_state_members(state_def) -> list:
    """Return (kind, name, doc) for each direct member state or transition."""
    members = []
    try:
        for m in state_def.owned_members.collect():
            m_name = get_declared_name(m)
            m_doc  = collapse_doc(get_unnamed_doc(m))[:60]
            if m.isinstance(syside.StateUsage.STD):
                members.append(("state", m_name, m_doc))
            elif m.isinstance(syside.TransitionUsage.STD):
                members.append(("transition", m_name, m_doc))
    except Exception:
        pass
    return members


def get_action_features(action_def) -> list:
    """Return (direction, name, type) for in/out parameters."""
    features = []
    try:
        for m in action_def.owned_members.collect():
            m_name = get_declared_name(m)
            if not m_name:
                continue
            direction = ""
            try:
                d = str(getattr(m, "direction", "")).lower()
                if "in" in d and "out" not in d:
                    direction = "in"
                elif "out" in d:
                    direction = "out"
            except Exception:
                pass
            type_name = ""
            try:
                for typ in m.types.collect():
                    type_name = get_declared_name(typ)
                    break
            except Exception:
                pass
            if direction:
                features.append((direction, m_name, type_name))
    except Exception:
        pass
    return features


def collect_perform_links(model, model_dir) -> list:
    """Find all PerformActionUsage elements (perform links)."""
    performs = []
    try:
        all_perform = []
        for top in iter_user_elements(model, model_dir):
            collect_typed(top, syside.PerformActionUsage.STD, all_perform)
        for p in all_perform:
            p_name = get_declared_name(p)
            # Get the action type
            action_type = ""
            try:
                for typ in p.cast(syside.PerformActionUsage.STD).types.collect():
                    action_type = get_declared_name(typ)
                    break
            except Exception:
                pass
            # Get the owning part def
            owner_name = ""
            try:
                owner = p.owner
                if owner:
                    owner_name = get_declared_name(owner)
            except Exception:
                pass
            performs.append((owner_name, p_name, action_type))
    except Exception:
        pass
    return performs


def main():
    args = parse_args("LA-04 Behavioral Summary")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        action_defs = []
        state_defs  = []
        for top in iter_user_elements(model, args.model_dir):
            collect_typed(top, syside.ActionDefinition.STD, action_defs)
            collect_typed(top, syside.StateDefinition.STD, state_defs)

        perform_links = collect_perform_links(model, args.model_dir)

        lines = [
            md_heading("Behavioral Summary (LA-04)"),
            f"**Model:** `{args.model_dir}`\n",
            f"**Action defs:** {len(action_defs)}  "
            f"**State defs:** {len(state_defs)}  "
            f"**Perform links:** {len(perform_links)}\n",
        ]

        # Action Definitions
        lines.append(md_heading("Action Definitions", 2))
        if action_defs:
            rows = []
            for ad in sorted(action_defs, key=get_declared_name):
                name     = get_declared_name(ad)
                doc      = collapse_doc(get_unnamed_doc(ad))[:80]
                features = get_action_features(ad)
                params   = ", ".join(f"{d} {n}: {t}" for d, n, t in features)
                rows.append([name, params or "—", doc or "—"])
            lines.append(md_table(["Action Def", "Parameters (in/out)", "Description"], rows))
        else:
            lines.append("> No action definitions found.\n")

        # State Definitions
        lines.append(md_heading("State Machine Definitions", 2))
        if state_defs:
            for sd in sorted(state_defs, key=get_declared_name):
                name    = get_declared_name(sd)
                doc     = get_unnamed_doc(sd)
                members = get_state_members(sd)

                lines.append(md_heading(name, 3))
                if doc:
                    lines.append(f"{doc}\n")

                states      = [(n, d) for k, n, d in members if k == "state"]
                transitions = [(n, d) for k, n, d in members if k == "transition"]

                if states:
                    lines.append(md_table(["State", "Description"],
                                          [[n, d or "—"] for n, d in states]))
                if transitions:
                    lines.append(md_table(["Transition", "Description"],
                                          [[n, d or "—"] for n, d in transitions]))
        else:
            lines.append("> No state definitions found.\n")

        # Perform links
        lines.append(md_heading("Perform Links (Behavior Assignments)", 2))
        if perform_links:
            rows = sorted(perform_links, key=lambda x: (x[0], x[2]))
            lines.append(md_table(["Owning Element", "Perform Usage", "Action Type"], rows))
        else:
            lines.append("> No perform links found.\n")
            lines.append("> Add `perform action x : ActionDef;` inside part defs "
                         "in LogicalArchModel.\n")

        write_report(args.output / "behavioral_summary.md", "\n".join(lines), "LA-04")


if __name__ == "__main__":
    main()
