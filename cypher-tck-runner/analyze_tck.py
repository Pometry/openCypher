#!/usr/bin/env python3
"""
TCK Test Result Analyzer
========================
Runs `behave` on the TCK feature suite, parses every scenario outcome,
and prints a structured breakdown of errors grouped by category.

Usage:
    python analyze_tck.py                  # run behave and analyze
    python analyze_tck.py results.txt      # analyze a saved output file
    python analyze_tck.py --save results.txt  # run behave, save raw output, then analyze
"""

import sys
import re
import subprocess
import os
from collections import defaultdict, Counter
from pathlib import Path

# ── Colour helpers (disable if piped) ──────────────────────────────────────
USE_COLOUR = sys.stdout.isatty()

def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOUR else text

def green(t):  return _c("32", t)
def red(t):    return _c("31", t)
def yellow(t): return _c("33", t)
def cyan(t):   return _c("36", t)
def bold(t):   return _c("1", t)
def dim(t):    return _c("2", t)


# ── Error classification ──────────────────────────────────────────────────
def classify_error(error_line):
    """Classify a single error line into (category, detail)."""
    line = error_line.strip()

    # --- Parse errors ---
    m = re.search(r'Parse error: UnexpectedToken\((\w+)', line)
    if m:
        return ("Parse: UnexpectedToken", m.group(1))

    if "Parse error:" in line:
        m2 = re.search(r'Parse error: (.+)', line)
        detail = m2.group(1) if m2 else "unknown"
        return ("Parse: Other", detail[:80])

    # --- Binding errors ---
    m = re.search(r'Binding error: VariableNotFound\("(\w+)"\)', line)
    if m:
        return ("Binder: VariableNotFound", m.group(1))

    m = re.search(r'Binding error: UnsupportedExpression\("(.+?)"\)', line)
    if m:
        return ("Binder: UnsupportedExpression", m.group(1))

    if "Binding error:" in line:
        m2 = re.search(r'Binding error: (.+)', line)
        detail = m2.group(1) if m2 else "unknown"
        return ("Binder: Other", detail[:80])

    # --- Planner / optimizer ---
    if "UnsupportedPattern" in line:
        m = re.search(r'UnsupportedPattern\("(.+?)"\)', line)
        detail = m.group(1) if m else "unknown"
        return ("Planner: UnsupportedPattern", detail[:80])

    if "NoValidPlan" in line:
        return ("Optimizer: NoValidPlan", "")

    # --- Runtime / execution errors ---
    m = re.search(r'column types must match schema types, expected (\w+) but found (\w+)', line)
    if m:
        return ("Runtime: ColumnTypeMismatch", f"{m.group(1)} vs {m.group(2)}")

    m = re.search(r"Sort column '(.+?)' not found", line)
    if m:
        return ("Runtime: SortColumnNotFound", m.group(1))

    if "duration.inSeconds()" in line:
        return ("Runtime: duration.inSeconds", "")
    if "duration.inMonths()" in line:
        return ("Runtime: duration.inMonths", "")
    if "duration.inDays()" in line:
        return ("Runtime: duration.inDays", "")

    if "DELETE not supported" in line:
        return ("Runtime: DeleteNotSupported", "")

    if "statement type is not supported" in line:
        return ("Runtime: StatementNotSupported", "")

    if "Could not evaluate expression in INSERT" in line:
        return ("Runtime: InsertExpressionEval", "")

    if "Wrong type for property" in line:
        m = re.search(r'expected (\w+) but actual type is (\w+)', line)
        detail = f"{m.group(1)} vs {m.group(2)}" if m else ""
        return ("Runtime: WrongPropertyType", detail)

    if "RuntimeError" in line or "Runtime" in line:
        # Generic runtime
        m = re.search(r'RuntimeError\("(.+?)"\)', line)
        detail = m.group(1)[:80] if m else line[:80]
        return ("Runtime: Other", detail)

    # --- Expected errors that didn't fire ---
    m = re.search(r'Expected (SyntaxError|TypeError|SemanticError|ArgumentError) \((\w+)\), but query succeeded', line)
    if m:
        return (f"Missing Error: {m.group(1)}", m.group(2))

    m = re.search(r'Expected (SyntaxError|TypeError|SemanticError|ArgumentError)', line)
    if m:
        return (f"Expected Error: {m.group(1)}", line[:80])

    # --- Result mismatch ---
    if "Result mismatch" in line:
        return ("Result: Mismatch", "")

    # --- Side effect mismatch ---
    if "Side effects mismatch" in line:
        return ("Result: SideEffectsMismatch", "")

    # --- Fallback ---
    return ("Other", line[:100])


# ── Parse behave output ───────────────────────────────────────────────────
def parse_behave_output(text):
    """
    Parse the full behave --no-capture output.
    Returns:
        scenarios: list of dicts with keys:
            feature, name, file_loc, status, errors, query
        summary: dict parsed from the summary lines
    """
    scenarios = []
    current_feature = ""
    current_scenario = None
    in_query = False
    query_lines = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        # Feature header
        fm = re.match(r'^Feature:\s+(.+?)(?:\s+#\s+(.+))?$', line)
        if fm:
            current_feature = fm.group(1).strip()
            continue

        # Scenario header (matches both "Scenario:" and "Scenario Outline:")
        sm = re.match(r'^\s+Scenario(?:\s+Outline)?:\s+(.+?)(?:\s+#\s+(.+))?$', line)
        if sm:
            # Save previous scenario
            if current_scenario is not None:
                scenarios.append(current_scenario)
            current_scenario = {
                "feature": current_feature,
                "name": sm.group(1).strip(),
                "file_loc": (sm.group(2) or "").strip(),
                "status": "passed",
                "errors": [],
                "query": "",
            }
            in_query = False
            query_lines = []
            continue

        if current_scenario is None:
            continue

        # Capture the query (between triple-quotes after "When executing query:")
        if '"""' in line:
            if in_query:
                in_query = False
                current_scenario["query"] = "\n".join(query_lines).strip()
                query_lines = []
            else:
                in_query = True
            continue

        if in_query:
            query_lines.append(line.strip())
            continue

        # ASSERT FAILED lines
        if "ASSERT FAILED:" in line:
            current_scenario["status"] = "failed"
            err_text = line.split("ASSERT FAILED:", 1)[1].strip()
            current_scenario["errors"].append(err_text)
            continue

        # RuntimeError lines (standalone, not inside ASSERT FAILED)
        if line.strip().startswith("RuntimeError:"):
            current_scenario["status"] = "error"
            current_scenario["errors"].append(line.strip())
            continue

        # Traceback (mark as error)
        if line.strip().startswith("Traceback"):
            current_scenario["status"] = "error"
            continue

        # Capture error message lines after Traceback
        em = re.match(r'^\s+((?:AttributeError|TypeError|KeyError|ValueError|IndexError|AssertionError|NotImplementedError|Exception|StopIteration)\S*:.+)', line)
        if em and current_scenario["status"] == "error":
            current_scenario["errors"].append(em.group(1).strip())
            continue

    # Don't forget the last scenario
    if current_scenario is not None:
        scenarios.append(current_scenario)

    # Parse summary line
    summary = {}
    sm = re.search(r'(\d+) scenarios? passed, (\d+) failed, (\d+) error', text)
    if sm:
        summary["passed"] = int(sm.group(1))
        summary["failed"] = int(sm.group(2))
        summary["errored"] = int(sm.group(3))
    sm2 = re.search(r'(\d+) scenarios? .* (\d+) skipped', text)
    if sm2:
        summary["skipped"] = int(sm2.group(2))

    return scenarios, summary


# ── Reporting ─────────────────────────────────────────────────────────────
def print_report(scenarios, summary):
    total = summary.get("passed", 0) + summary.get("failed", 0) + summary.get("errored", 0) + summary.get("skipped", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    errored = summary.get("errored", 0)
    skipped = summary.get("skipped", 0)

    print()
    print(bold("=" * 72))
    print(bold("  TCK Test Results"))
    print(bold("=" * 72))
    print()
    print(f"  {green(f'{passed:>5} passed')}  "
          f"{red(f'{failed:>5} failed')}  "
          f"{yellow(f'{errored:>5} error')}  "
          f"{dim(f'{skipped:>5} skipped')}  "
          f"  {bold(f'{total} total')}")
    pct = (passed / total * 100) if total else 0
    print(f"  Pass rate: {bold(f'{pct:.1f}%')}")
    print()

    # Classify all errors
    category_counts = Counter()      # category -> count
    category_details = defaultdict(Counter)  # category -> {detail -> count}
    category_examples = defaultdict(list)    # category -> [(scenario_name, file_loc, query)]

    failed_scenarios = [s for s in scenarios if s["status"] in ("failed", "error")]

    for sc in failed_scenarios:
        if not sc["errors"]:
            cat = "Unknown (no error captured)"
            category_counts[cat] += 1
            category_examples[cat].append((sc["name"], sc["file_loc"], sc["query"]))
            continue

        # Use the first error to classify the scenario (avoid double-counting)
        first_error = sc["errors"][0]
        cat, detail = classify_error(first_error)
        category_counts[cat] += 1
        if detail:
            category_details[cat][detail] += 1
        if len(category_examples[cat]) < 3:  # Keep up to 3 examples
            category_examples[cat].append((sc["name"], sc["file_loc"], sc["query"]))

    # Print categories sorted by count
    print(bold("-" * 72))
    print(bold("  Error Breakdown (by first error per scenario)"))
    print(bold("-" * 72))
    print()

    for cat, count in category_counts.most_common():
        bar = "█" * min(count // 5, 40) or "▏"
        print(f"  {red(f'{count:>5}')}  {cat:<45}  {dim(bar)}")

        # Show top details
        details = category_details.get(cat)
        if details:
            for det, dcount in details.most_common(5):
                print(f"         {dim(f'{dcount:>4}x')}  {dim(det[:70])}")

    print()

    # Show top-level summary table
    print(bold("-" * 72))
    print(bold("  High-Level Groups"))
    print(bold("-" * 72))
    print()

    groups = defaultdict(int)
    for cat, count in category_counts.items():
        prefix = cat.split(":")[0] if ":" in cat else cat
        groups[prefix] += count

    for grp, count in sorted(groups.items(), key=lambda x: -x[1]):
        pct_of_fail = count / max(len(failed_scenarios), 1) * 100
        bar = "█" * min(count // 10, 40) or "▏"
        print(f"  {count:>5}  ({pct_of_fail:>5.1f}%)  {grp:<30}  {dim(bar)}")

    print()

    # Feature-level failure breakdown
    feature_fails = Counter()
    for sc in failed_scenarios:
        feature_fails[sc["feature"]] += 1

    print(bold("-" * 72))
    print(bold("  Top 15 Failing Features"))
    print(bold("-" * 72))
    print()
    for feat, count in feature_fails.most_common(15):
        print(f"  {red(f'{count:>5}')}  {feat[:65]}")

    print()

    # Optionally show example queries for the top error categories
    print(bold("-" * 72))
    print(bold("  Example Queries (first 2 per top-10 category)"))
    print(bold("-" * 72))
    print()
    for cat, _ in category_counts.most_common(10):
        examples = category_examples.get(cat, [])
        if not examples:
            continue
        print(f"  {bold(cat)}:")
        for name, loc, query in examples[:2]:
            q_display = query.replace("\n", " ")[:80] if query else "(no query captured)"
            print(f"    {dim(loc)}")
            print(f"    {cyan(q_display)}")
        print()

    print(bold("=" * 72))
    print()


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    save_path = None
    input_file = None

    args = sys.argv[1:]
    if "--save" in args:
        idx = args.index("--save")
        if idx + 1 < len(args):
            save_path = args[idx + 1]
        args = [a for i, a in enumerate(args) if i != idx and i != idx + 1]

    if args and not args[0].startswith("-"):
        input_file = args[0]

    if input_file:
        print(f"Reading saved output from {input_file}...")
        with open(input_file) as f:
            raw = f.read()
    else:
        runner_dir = Path(__file__).parent
        print(f"Running behave in {runner_dir}...")
        result = subprocess.run(
            [sys.executable, "-m", "behave", "features/", "--no-capture"],
            capture_output=True, text=True, cwd=str(runner_dir),
        )
        raw = result.stdout + result.stderr

        if save_path:
            with open(save_path, "w") as f:
                f.write(raw)
            print(f"Raw output saved to {save_path}")

    scenarios, summary = parse_behave_output(raw)
    print_report(scenarios, summary)


if __name__ == "__main__":
    main()
