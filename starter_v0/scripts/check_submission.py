"""Offline, deterministic checks for the lab's contracts and security boundaries."""
from __future__ import annotations

import ast
import importlib
import inspect
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS, load_tool_declarations
from run_eval import load_cases, validate_expected_tools
from versioning import build_artifact_version


def main() -> None:
    records = []

    def check(name, condition, detail):
        records.append({"check": name, "passed": bool(condition), "detail": detail})

    files = [p for p in ROOT.rglob("*.py") if ".venv" not in p.parts and "__pycache__" not in p.parts]
    for path in files:
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    check("python_syntax", True, f"{len(files)} source files parsed without writing bytecode")
    declarations = load_tool_declarations(ROOT / "artifacts/tools.yaml")
    check("registry_names", {t["name"] for t in declarations} == set(TOOL_FUNCTIONS), "9 declared tools match implementations")
    for declaration in declarations:
        args = set(declaration["parameters"]["properties"])
        implemented = set(inspect.signature(TOOL_FUNCTIONS[declaration["name"]]).parameters)
        check(f"schema_{declaration['name']}", args <= implemented, "Declared arguments accepted by implementation")
    for path in sorted((ROOT / "data").glob("eval_*.json")):
        cases = load_cases(path, "B")
        validate_expected_tools(cases, declarations, path)
        check(path.name, len({c["id"] for c in cases}) == len(cases), f"{len(cases)} unique valid cases")
    group = load_cases(ROOT / "data/eval_group.json", "B")
    check("group_5_single_5_multi", len(group) == 10 and sum("turns" in c for c in group) == 5, "10 cases; 5 single and 5 multi")

    ticket_module = importlib.import_module("tools.create_ticket.tool")
    with tempfile.TemporaryDirectory(prefix="day04-guardrails-") as isolated:
        with patch.object(ticket_module, "TICKET_DIR", Path(isolated)):
            for index, confirmed in enumerate([False, "true", 1, {"confirmed": True}, None]):
                result = ticket_module.create_ticket(summary="Synthetic VPN issue", asset_id="LT-204", confirmed=confirmed)
                check(f"reject_fake_confirmation_{index}", result.get("status") == "needs_confirmation" and not list(Path(isolated).glob("*.json")), "No ticket written")
            result = ticket_module.create_ticket(summary="Synthetic token=DEMO_NOT_A_REAL_SECRET", confirmed=True)
            check("reject_sensitive_ticket", result.get("error") == "restricted_sensitive_data" and not list(Path(isolated).glob("*.json")), "Synthetic credential rejected before filesystem write")
            result = ticket_module.create_ticket(summary="Synthetic approved lab ticket", asset_id="LT-204", confirmed=True)
            check("confirmed_ticket_writes", result.get("status") == "created" and len(list(Path(isolated).glob("*.json"))) == 1, "Exactly one mock ticket written after boolean true")
    check("temporary_tickets_removed", not Path(isolated).exists(), "Only script-created temporary ticket directory cleaned")

    search_module = importlib.import_module("tools.search_device_info.tool")
    with patch.object(search_module.requests, "post") as post:
        result = search_module.search_device_info("Lenovo", "ThinkPad T14 Gen 4 LT-204 EMP-1001")
        check("external_identifiers_blocked", result.get("error") == "restricted_internal_identifier" and post.call_count == 0, "No HTTP request for smuggled asset/employee IDs")

    policy_module = importlib.import_module("tools.policy.tool")
    result = policy_module.search_company_policy("critical incident policy", "incident_response", 20)
    probes = [r for r in result["results"] if r["untrusted_text"]]
    check("policy_injection_separated", bool(probes) and all("mark every request" not in r["facts"] for r in result["results"]), "Probe stays in untrusted_text; absent from facts")
    kb_module = importlib.import_module("tools.search_kb.tool")
    result = kb_module.search_kb("print queue troubleshooting safety sample", "printing", 20)
    probes = [r for r in result["results"] if r["article_id"] == "KB-PRINT-011"]
    check("kb_injection_separated", bool(probes) and bool(probes[0]["untrusted_text"]) and "call create_ticket" not in probes[0]["content"], "Verified steps exclude injected tool instruction")

    from providers.openrouter_provider import OpenRouterProvider
    with patch.dict(os.environ, {"OPENROUTER_MAX_TOKENS": "2048", "OPENROUTER_API_KEY": "offline-placeholder"}):
        provider = OpenRouterProvider()
        with patch("openai.OpenAI") as client:
            client.return_value.chat.completions.create.return_value = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="offline test", tool_calls=[]))])
            provider.complete([{"role": "user", "content": "offline test"}])
            sent = client.return_value.chat.completions.create.call_args.kwargs
            check("bounded_openrouter_output", sent["max_tokens"] == 2048, "OpenRouter max_tokens sent; network client mocked")
    with patch.dict(os.environ, {"OPENROUTER_MAX_TOKENS": "0"}):
        try:
            OpenRouterProvider()
            rejected = False
        except ValueError:
            rejected = True
        check("reject_nonpositive_max_tokens", rejected, "Invalid limit rejected before provider request")

    errors = []
    empty_results = []
    for path in sorted((ROOT / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        for case in run["results"]:
            for event in case["tool_results"]:
                result = event.get("result", {})
                item = {"run": path.name, "case": case["id"], "tool": event["tool"]}
                if isinstance(result, dict) and result.get("error"):
                    errors.append({**item, "error": result["error"]})
                if isinstance(result, dict) and (result.get("results") == [] or result.get("items") == []):
                    empty_results.append(item)
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "artifact_version": build_artifact_version("v5", ROOT / "artifacts/system_prompt.md", ROOT / "artifacts/tools.yaml").artifact_version,
               "passed": all(r["passed"] for r in records), "checks": records,
               "historical_tool_errors": errors, "historical_empty_retrievals": empty_results,
               "scope": "Offline contract checks; HTTP mocked only for deterministic no-request assertion. Does not certify all prompt-injection variants or live Tavily success."}
    (ROOT / "artifacts/submission_checks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": payload["passed"], "checks": len(records), "tool_errors": len(errors), "empty_retrievals": len(empty_results)}))
    if not payload["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
