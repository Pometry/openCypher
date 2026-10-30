"""Fail when a scenario that is not listed as an expected failure fails, errors or crashes.

Usage: python check_expected.py <run_all.sh out dir> <expected failures file>
The expected file has one `location :: name` per line, as printed below; lines starting `#` are comments.
Listed scenarios that now pass are reported, so the list can shrink, but do not fail the check.
"""

import collections
import glob
import json
import os
import sys


def statuses(run):
    out = {}
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        try:
            features = json.load(open(path))
        except json.JSONDecodeError:
            # behave died mid-feature: count the feature as crashed.
            out[f"{os.path.basename(path)} :: <crashed>"] = "crashed"
            continue
        for feature in features:
            for el in feature.get("elements", []):
                if el.get("type") == "scenario":
                    # Outline rows end in a space, which a list file would not keep.
                    out[f"{el['location']} :: {el['name']}".strip()] = el["status"]
    return out


run, expected_path = sys.argv[1:]
status = statuses(run)
expected = {line.strip() for line in open(expected_path) if line.strip() and line[0] != "#"}
print(dict(collections.Counter(status.values())))
unexpected = sorted(k for k, s in status.items() if s not in ("passed", "skipped") and k not in expected)
fixed = sorted(k for k in expected if status.get(k) == "passed")
for title, keys in (("Unexpected failures", unexpected), ("Expected failures that now pass", fixed)):
    if keys:
        print(f"\n{title}: {len(keys)}")
        for key in keys:
            print(f"  {key}  [{status[key]}]")
sys.exit(1 if unexpected else 0)
