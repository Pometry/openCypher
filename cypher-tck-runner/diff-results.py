#!/usr/bin/env python3
"""Compare two TCK result JSON files and show regressions.

Usage:
    python3 diff-results.py <baseline.json> <current.json>
    python3 diff-results.py                   # auto-picks the two most recent results
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load_statuses(path: str) -> dict[str, str]:
    """Return {scenario_id: status} from a behave JSON result file."""
    with open(path) as f:
        features = json.load(f)
    statuses: dict[str, str] = {}
    for feat in features:
        feat_name = feat["name"]
        for el in feat.get("elements", []):
            if el.get("type") != "scenario":
                continue
            key = f"{feat_name} :: {el['name']}"
            statuses[key] = el["status"]
    return statuses


def main() -> None:
    results_dir = Path(__file__).parent / "results"

    if len(sys.argv) == 3:
        baseline_path, current_path = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 1:
        golden = results_dir / "golden.json"
        non_golden = sorted(p for p in results_dir.glob("*.json") if p.name != "golden.json")
        if golden.exists() and non_golden:
            baseline_path, current_path = str(golden), str(non_golden[-1])
        elif len(non_golden) >= 2:
            baseline_path, current_path = str(non_golden[-2]), str(non_golden[-1])
        else:
            print("Need a golden.json or at least 2 result files. Run `make tck-golden` to set a baseline.")
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)

    print(f"Baseline: {Path(baseline_path).name}")
    print(f"Current:  {Path(current_path).name}")
    print()

    baseline = load_statuses(baseline_path)
    current = load_statuses(current_path)

    # Regressions: passed in baseline, not passed now
    regressions = []
    fixes = []
    for key in sorted(set(baseline) | set(current)):
        old = baseline.get(key, "missing")
        new = current.get(key, "missing")
        if old == new:
            continue
        if old == "passed" and new != "passed":
            regressions.append((key, new))
        elif new == "passed" and old != "passed":
            fixes.append((key, old))

    if regressions:
        print(f"❌ REGRESSIONS ({len(regressions)} tests that used to pass but now fail):")
        for name, status in regressions:
            print(f"  {name}  [{status}]")
    else:
        print("✅ No regressions — nothing that previously passed is now failing.")

    if fixes:
        print(f"\n🎉 FIXES ({len(fixes)} tests that now pass):")
        for name, old_status in fixes:
            print(f"  {name}  [was {old_status}]")

    # Summary
    bp = sum(1 for s in baseline.values() if s == "passed")
    cp = sum(1 for s in current.values() if s == "passed")
    print(f"\nTotal passed: {bp} → {cp} ({cp - bp:+d})")


if __name__ == "__main__":
    main()
