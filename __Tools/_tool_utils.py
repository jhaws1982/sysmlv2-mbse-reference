"""
_tool_utils.py — Shared utilities for OOSEM artifact generation scripts.

Model loading pattern (matches all working tools in this codebase):

    with load_model(model_dir) as model:
        diags = model.diagnostics
        if diags.contains_errors():
            print("WARNING: Model loaded with errors. Results may be incomplete.")
            for msg in diags.errors:
                print(f"  ERROR:   {msg}")
        for top in model.top_elements_from(str(model_dir)):
            collect_typed(top, syside.SomeType.STD, results)

Key rules (confirmed from working tools):
  - open_model() takes a directory string, used as a context manager
  - top_elements_from(path) scopes traversal to user files only —
    this is what prevents .venv / site-packages files from being processed
  - diagnostics.contains_errors() prints WARNING but never causes sys.exit
  - Never call sys.exit() based on diagnostics — always continue processing
"""

import sys
import json
import argparse
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    import syside
    from syside.preview import open_model
    SYSIDE_AVAILABLE = True
except ImportError:
    SYSIDE_AVAILABLE = False


# ── Argument parsing ──────────────────────────────────────────────────────────

def make_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("model_dir", type=Path,
                   help="Path to the model root directory")
    p.add_argument("--output", "-o", type=Path, default=None,
                   help="Output directory (default: __output/ under cwd)")
    p.add_argument("--config-json", type=str, default=None,
                   help="JSON config string injected by generate_artifacts.py")
    return p


def parse_args(description: str) -> argparse.Namespace:
    args = make_parser(description).parse_args()
    if args.output is None:
        args.output = Path.cwd() / "__output"
    args.output.mkdir(parents=True, exist_ok=True)
    args.diagrams_dir = args.output / "diagrams"
    args.diagrams_dir.mkdir(parents=True, exist_ok=True)
    args.script_config = {}
    if args.config_json:
        try:
            args.script_config = json.loads(args.config_json)
        except json.JSONDecodeError:
            pass
    return args


# ── Model loading ─────────────────────────────────────────────────────────────

_EXCLUDED_DIRS = {'.venv', '__Tools', '.git', '.claude', '__pycache__', 'node_modules'}


def collect_user_sysml_files(model_dir: Path) -> list[Path]:
    """Return .sysml files under model_dir, skipping tool/venv/git directories."""
    return [
        f for f in model_dir.rglob("*.sysml")
        if not any(part in _EXCLUDED_DIRS for part in f.relative_to(model_dir).parts)
    ]


@contextmanager
def load_model(model_dir: Path):
    """
    Context manager that opens a SysIDE model. Passes only user .sysml files
    to open_model (excluding .venv and tool directories).

    Use iter_user_elements(model, model_dir) for traversal to scope results
    to user-defined elements only.

        with load_model(model_dir) as model:
            diags = model.diagnostics
            if diags.contains_errors():
                print("WARNING: ...")
            for top in iter_user_elements(model, model_dir):
                collect_typed(top, syside.SomeType.STD, results)
    """
    model_dir = model_dir.resolve()
    if not SYSIDE_AVAILABLE:
        print("ERROR: syside (SysIDE Automator) is not installed.")
        sys.exit(1)
    if not model_dir.exists():
        print(f"ERROR: Model directory not found: {model_dir}")
        sys.exit(1)
    user_files = collect_user_sysml_files(model_dir)
    if not user_files:
        print(f"ERROR: No .sysml files found under {model_dir}")
        sys.exit(1)
    with open_model(user_files, allow_errors=True) as model:
        yield model


def iter_user_elements(model, model_dir: Path):
    """
    Yield top-level model elements from user directories only.

    Use this instead of model.top_elements_from(model_dir) to avoid
    collecting stdlib elements from .venv when .venv is inside model_dir.
    Iterates each non-excluded top-level directory/file and calls
    top_elements_from() on each, so elements from .venv are never returned.

    No id()-based deduplication: Python GC can reuse freed object IDs across
    directory iterations, causing false-positive deduplication. Since each
    top-level directory is distinct (no overlapping paths), there are no
    true duplicates to guard against.
    """
    model_dir = model_dir.resolve()  # must be absolute for top_elements_from
    for item in sorted(model_dir.iterdir()):
        if item.name in _EXCLUDED_DIRS or item.name.startswith('.'):
            continue
        if item.is_dir() or (item.is_file() and item.suffix == '.sysml'):
            try:
                yield from model.top_elements_from(str(item))
            except Exception:
                pass


# ── Traversal helpers ─────────────────────────────────────────────────────────

def collect_typed(root, std_type, results: list):
    """Depth-first collection of all elements matching std_type."""
    if root.isinstance(std_type):
        results.append(root.cast(std_type))
    if root.isinstance(syside.Namespace.STD):
        ns = root.cast(syside.Namespace.STD)
        for member in ns.owned_members.collect():
            collect_typed(member, std_type, results)


def get_declared_name(element) -> str:
    if element is None:
        return ""
    name = getattr(element, "declared_name", None)
    if name:
        return str(name)
    qn = getattr(element, "qualified_name", None)
    return str(qn) if qn else ""


def get_short_name(element) -> str:
    """Return the <'REQ-ID'> short-name, stripping quotes."""
    for attr in ("req_id", "short_name", "declared_short_name"):
        val = getattr(element, attr, None)
        if val:
            return str(val).strip("'\"")
    return ""


def get_def_type_name(usage) -> str:
    """Return the declared name of the definition type of a usage."""
    try:
        for typ in usage.types.collect():
            name = get_declared_name(typ)
            if name:
                return name
    except Exception:
        pass
    return ""


# ── Doc annotation helpers (SRS_Definitions doc-convention) ──────────────────

def get_doc_blocks(element) -> list[tuple]:
    """
    Return all doc annotation blocks as (name, body) tuples.
    name is None for unnamed doc blocks.
    """
    blocks = []
    try:
        for doc in element.documentation.collect():
            body = getattr(doc, "body", None)
            if not body:
                continue
            text = str(body).strip()
            text = re.sub(r"^/\*+\s*\*?\s*", "", text)
            text = re.sub(r"\s*\*+/$", "", text)
            text = re.sub(r"\n\s*\*\s?", "\n", text).strip()
            name = getattr(doc, "declared_name", None)
            blocks.append((name, text))
    except Exception:
        pass
    return blocks


def get_unnamed_doc(element) -> str:
    """Return the body of the first unnamed doc block, or empty string."""
    for name, body in get_doc_blocks(element):
        if name is None:
            return body
    return ""


def get_named_doc(element, doc_name: str) -> str:
    """Return the body of the named doc block, or empty string."""
    for name, body in get_doc_blocks(element):
        if name == doc_name:
            return body
    return ""


def has_doc_rationale(element) -> bool:
    return bool(get_named_doc(element, "Rationale"))


def collapse_doc(text: str) -> str:
    """Collapse multi-line doc text to a single line for table cells."""
    return " ".join(text.split())


# ── Markdown utilities ────────────────────────────────────────────────────────

def md_heading(text: str, level: int = 1) -> str:
    return f"{'#' * level} {text}\n"


def md_table(headers: list[str], rows: list[list]) -> str:
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    def fmt_row(cells):
        return "| " + " | ".join(
            str(c).ljust(col_widths[i]) for i, c in enumerate(cells)
        ) + " |"

    lines = [
        fmt_row(headers),
        "| " + " | ".join("-" * w for w in col_widths) + " |",
    ]
    for row in rows:
        padded = list(row) + [""] * (len(headers) - len(row))
        lines.append(fmt_row(padded))
    return "\n".join(lines) + "\n"


def write_report(output_path: Path, content: str, label: str = ""):
    output_path.write_text(content, encoding="utf-8")
    tag = f"  [{label}] " if label else "  "
    print(f"{tag}→ {output_path}")


# ── Validation issue dataclass ────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    severity: str        # "INVALID" | "WARNING"
    req_id:   str
    name:     str
    check:    str
    detail:   str = ""


def format_issues_md(issues: list, title: str = "Issues") -> str:
    if not issues:
        return f"*No {title.lower()} found.*\n"
    rows = [[i.severity, i.req_id or "—", i.name or "—", i.check, i.detail]
            for i in issues]
    return md_table(["Severity", "ID", "Name", "Check", "Detail"], rows)


def issues_summary(issues: list) -> tuple[int, int]:
    invalid  = sum(1 for i in issues if i.severity == "INVALID")
    warnings = sum(1 for i in issues if i.severity == "WARNING")
    return invalid, warnings


def is_plain_req(r) -> bool:
    """Exclude SatisfyRequirementUsage and ConcernUsage from requirement checks."""
    try:
        if r.isinstance(syside.SatisfyRequirementUsage.STD):
            return False
    except Exception:
        pass
    try:
        if r.isinstance(syside.ConcernUsage.STD):
            return False
    except Exception:
        pass
    return True


def in_package_named(element, *pkg_names: str) -> bool:
    """Return True if element is owned by a package with any of the given names."""
    try:
        owner = element.owner
        while owner is not None:
            name = get_declared_name(owner)
            if name and any(p.lower() in name.lower() for p in pkg_names):
                return True
            owner = getattr(owner, "owner", None)
    except Exception:
        pass
    return False


def pdf_attempt(md_content: str, pdf_path: Path, artifact_id: str,
                *, number_sections: bool = True) -> None:
    """Convert Markdown to PDF via pandoc + weasyprint.

    Resolves the weasyprint binary from the same Python environment as the
    running interpreter so the call works whether or not the venv is activated
    in the calling shell.
    """
    weasyprint_bin = Path(sys.executable).parent / "weasyprint"
    tmp = pdf_path.with_suffix(".md.tmp")
    tmp.write_text(md_content, encoding="utf-8")
    cmd = ["pandoc", str(tmp), "-o", str(pdf_path),
           f"--pdf-engine={weasyprint_bin}", "--toc"]
    if number_sections:
        cmd.append("--number-sections")
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        print(f"  [{artifact_id} PDF] → {pdf_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pdf_path.with_suffix(".pdf.txt").write_text(
            f"PDF requires pandoc + weasyprint. Markdown at {pdf_path.stem}.md\n")
        print(f"  [{artifact_id} PDF] ⚠ PDF generation failed — see {pdf_path.stem}.md")
    finally:
        tmp.unlink(missing_ok=True)
