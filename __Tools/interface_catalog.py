"""
interface_catalog.py — LA-03 Interface Catalog

Lists all port defs and flow item defs from LogicalInterfaces and other
interface packages, with directionality and type information.

Usage: python __Tools/interface_catalog.py <model_dir> [--output DIR]
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


def in_interface_pkg(element) -> bool:
    try:
        owner = element.owner
        while owner is not None:
            n = get_declared_name(owner)
            if n and any(k in n for k in ("Interface", "Logical")):
                return True
            owner = getattr(owner, "owner", None)
    except Exception:
        pass
    return False


def get_port_features(port_def) -> list:
    """Return (direction, name, type_name) for each directional feature."""
    features = []
    try:
        for member in port_def.owned_members.collect():
            name = get_declared_name(member)
            if not name:
                continue
            # Get direction
            direction = ""
            try:
                d = getattr(member, "direction", None)
                if d is not None:
                    direction = str(d).lower()
                    if "in" in direction and "out" not in direction:
                        direction = "in"
                    elif "out" in direction:
                        direction = "out"
                    elif "inout" in direction:
                        direction = "inout"
            except Exception:
                pass
            # Get type
            type_name = ""
            try:
                for typ in member.types.collect():
                    type_name = get_declared_name(typ)
                    break
            except Exception:
                pass
            if direction or type_name:
                features.append((direction, name, type_name))
    except Exception:
        pass
    return features


def main():
    args = parse_args("LA-03 Interface Catalog")

    with load_model(args.model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")

        port_defs = []
        item_defs = []
        for top in iter_user_elements(model, args.model_dir):
            collect_typed(top, syside.PortDefinition.STD, port_defs)
            collect_typed(top, syside.ItemDefinition.STD, item_defs)

        # Scope to interface/logical packages
        port_defs = [p for p in port_defs if in_interface_pkg(p)]
        item_defs = [i for i in item_defs if in_interface_pkg(i)]

        lines = [
            md_heading("Interface Catalog (LA-03)"),
            f"**Model:** `{args.model_dir}`\n",
            f"**Port defs:** {len(port_defs)}  **Item/flow defs:** {len(item_defs)}\n",
        ]

        # Port Definitions
        lines.append(md_heading("Port Definitions", 2))
        if port_defs:
            for pd in sorted(port_defs, key=get_declared_name):
                name     = get_declared_name(pd)
                doc      = get_unnamed_doc(pd)
                features = get_port_features(pd)

                lines.append(md_heading(name, 3))
                if doc:
                    lines.append(f"{doc}\n")

                if features:
                    feat_rows = [[d, n, t or "—"] for d, n, t in features]
                    lines.append(md_table(["Direction", "Feature", "Type"], feat_rows))
                else:
                    lines.append("> No directional features defined.\n")
        else:
            lines.append("> No port definitions found.\n")

        # Flow Item Definitions
        lines.append(md_heading("Flow Item Definitions", 2))
        if item_defs:
            rows = []
            for id_ in sorted(item_defs, key=get_declared_name):
                name = get_declared_name(id_)
                doc  = collapse_doc(get_unnamed_doc(id_))[:100]
                # Count attributes
                n_attrs = 0
                try:
                    for m in id_.owned_members.collect():
                        if m.isinstance(syside.AttributeUsage.STD):
                            n_attrs += 1
                except Exception:
                    pass
                rows.append([name, str(n_attrs), doc or "—"])
            lines.append(md_table(["Flow Item", "Attributes", "Description"], rows))

            # Detailed attribute listing
            lines.append(md_heading("Flow Item Attributes", 2))
            for id_ in sorted(item_defs, key=get_declared_name):
                name  = get_declared_name(id_)
                attrs = []
                try:
                    for m in id_.owned_members.collect():
                        if m.isinstance(syside.AttributeUsage.STD):
                            a_name = get_declared_name(m)
                            a_type = ""
                            try:
                                for typ in m.cast(syside.AttributeUsage.STD).types.collect():
                                    a_type = get_declared_name(typ)
                                    break
                            except Exception:
                                pass
                            attrs.append((a_name, a_type))
                except Exception:
                    pass
                if attrs:
                    lines.append(md_heading(name, 3))
                    lines.append(md_table(
                        ["Attribute", "Type"],
                        [[a, t or "—"] for a, t in attrs]
                    ))
        else:
            lines.append("> No flow item definitions found.\n")

        write_report(args.output / "interface_catalog.md", "\n".join(lines), "LA-03")


if __name__ == "__main__":
    main()
