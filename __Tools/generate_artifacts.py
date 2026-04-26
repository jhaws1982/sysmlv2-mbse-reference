"""
generate_artifacts.py — OOSEM Artifact Generation Orchestrator

Reads artifacts.yaml, executes the selected scripts, and prints a summary.

Usage:
    python __Tools/generate_artifacts.py --suite all
    python __Tools/generate_artifacts.py --suite diagnostics
    python __Tools/generate_artifacts.py --script req_completeness
    python __Tools/generate_artifacts.py --list
    python __Tools/generate_artifacts.py --suite all --dry-run
    python __Tools/generate_artifacts.py --suite formal_docs --config path/to/artifacts.yaml
"""

import sys
import argparse
import subprocess
import time
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required.  pip install pyyaml")
    sys.exit(1)

TOOLS_DIR   = Path(__file__).parent.resolve()
DEFAULT_CFG = TOOLS_DIR / "artifacts.yaml"


def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def model_root(config: dict, cfg_path: Path) -> Path:
    rel = config.get("model", {}).get("root", "../")
    return (cfg_path.parent / rel).resolve()


def script_path(name: str) -> Path:
    return TOOLS_DIR / f"{name}.py"


def run_script(path: Path, root: Path, cfg: dict) -> tuple[bool, str, float]:
    if not path.exists():
        return False, f"Script not found: {path}", 0.0
    cmd = [sys.executable, str(path), str(root)]
    if cfg:
        cmd += ["--config-json", json.dumps(cfg)]
    t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.monotonic() - t0
        return r.returncode == 0, (r.stdout + r.stderr).strip(), elapsed
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT after 300s", time.monotonic() - t0
    except Exception as e:
        return False, f"Exception: {e}", time.monotonic() - t0


def sep(char="─", w=72):
    print(char * w)


def main():
    p = argparse.ArgumentParser(description="OOSEM Artifact Generation Orchestrator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--suite",  metavar="NAME")
    g.add_argument("--script", metavar="NAME")
    g.add_argument("--list",   action="store_true")
    p.add_argument("--config",   default=str(DEFAULT_CFG))
    p.add_argument("--dry-run",  action="store_true")
    args = p.parse_args()

    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        print(f"ERROR: Config not found: {cfg_path}")
        sys.exit(1)

    config     = load_config(cfg_path)
    root       = model_root(config, cfg_path)
    suites     = config.get("suites", {})
    scr_cfg    = config.get("script_config", {})
    report_cfg = config.get("report", {})
    project    = config.get("model", {}).get("project_name", "")

    if args.list:
        print(f"\nAvailable suites in {cfg_path.name}:\n")
        for name, suite in suites.items():
            desc = suite.get("description", "")
            scripts = suite.get("scripts", [])
            print(f"  {name:<20} {desc}")
            for s in scripts:
                mark = "✓" if script_path(s).exists() else "✗ MISSING"
                print(f"    {mark}  {s}.py")
        print()
        return

    if args.script:
        scripts_to_run = [args.script]
        label = f"script:{args.script}"
    else:
        if args.suite not in suites:
            print(f"ERROR: Suite '{args.suite}' not found. Available: {', '.join(suites)}")
            sys.exit(1)
        scripts_to_run = suites[args.suite].get("scripts", [])
        label = f"suite:{args.suite}"

    sep("═")
    print(f"  OOSEM Artifact Generator — {project}")
    print(f"  Run:        {label}")
    print(f"  Model root: {root}")
    print(f"  Scripts:    {len(scripts_to_run)}")
    if args.dry_run:
        print("  Mode:       DRY RUN")
    sep("═")

    results = []
    t_total = time.monotonic()

    for name in scripts_to_run:
        sp = script_path(name)
        cfg = dict(scr_cfg.get(name, {}))
        if report_cfg:
            cfg["report"] = report_cfg
        if args.dry_run:
            mark = "✓" if sp.exists() else "✗ MISSING"
            print(f"  {mark}  {name}.py")
            results.append((name, True, "", 0.0))
            continue

        print(f"\n  Running {name}.py ...", end=" ", flush=True)
        ok, out, elapsed = run_script(sp, root, cfg)
        print(f"{'✓ OK' if ok else '✗ FAIL'}  ({elapsed:.1f}s)")
        if out:
            for line in out.splitlines()[:40]:
                print(f"    {line}")
            if len(out.splitlines()) > 40:
                print(f"    ... ({len(out.splitlines()) - 40} more lines)")
        results.append((name, ok, out, elapsed))

    if not args.dry_run:
        total = time.monotonic() - t_total
        passed = sum(1 for _, ok, _, _ in results if ok)
        failed = len(results) - passed
        print()
        sep()
        print(f"  Results: {passed} passed, {failed} failed  ({total:.1f}s total)")
        sep()
        if failed:
            print("\n  Failed scripts:")
            for name, ok, _, _ in results:
                if not ok:
                    print(f"    ✗  {name}.py")
            sys.exit(1)
        print()


if __name__ == "__main__":
    main()
