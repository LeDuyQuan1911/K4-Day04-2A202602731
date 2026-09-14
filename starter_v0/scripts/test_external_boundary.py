"""Deterministic smoke test for the search_device_info outbound-data guard (no network, no key needed)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS  # noqa: E402

search = TOOL_FUNCTIONS["search_device_info"]

BLOCKED = [
    ("Lenovo", "ThinkPad T14 Gen 4 LT-204", "restricted_internal_identifier"),
    ("Lenovo", "ThinkPad T14 Gen 4 EMP-1001", "restricted_internal_identifier"),
    ("Lenovo", "ThinkPad T14 Gen 4 serial PF3ABC12", "restricted_internal_data"),
    ("Lenovo", "ThinkPad T14 Gen 4 hostname nsl-lt204", "restricted_internal_data"),
    ("Lenovo", "ThinkPad T14 Gen 4 lt204.corp", "restricted_internal_data"),
    ("Lenovo", "ThinkPad T14 Gen 4 Bangkok floor 3", "restricted_internal_data"),
    ("Lenovo", "ThinkPad T14 Gen 4 AUTH_TIMEOUT", "restricted_internal_data"),
    ("Lenovo", "ThinkPad T14 Gen 4 password", "restricted_internal_data"),
]
ALLOWED = [("Lenovo", "ThinkPad T14 Gen 4"), ("Dell", "Latitude 5440"), ("Apple", "MacBook Air M2")]

failures = 0
for manufacturer, model, expected in BLOCKED:
    result = search(manufacturer, model, "specs", 1)
    ok = result.get("error") == expected
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'} blocked  {model!r:45} -> {result.get('error')}")
for manufacturer, model in ALLOWED:
    result = search(manufacturer, model, "specs", 1)
    # Without a key the guard passes and the tool stops at missing_api_key; with a key it performs the search.
    ok = result.get("error") in (None, "missing_api_key")
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'} allowed  {model!r:45} -> {result.get('error')}")
print("ALL PASS" if not failures else f"{failures} FAILED")
sys.exit(1 if failures else 0)
