"""Run the unchanged lab evaluator with isolated mock-ticket storage.

Scores still come from run_eval.py. The companion audit records real ticket
writes and external-search request bodies (never authorization headers).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_eval


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v3")
    parser.add_argument("--model", default="openai/gpt-4o-mini")
    parser.add_argument("--suites", nargs="+", default=["base", "group", "adversarial", "extension"])
    args = parser.parse_args()
    dataset_files = {"base": "eval_base.json", "group": "eval_group.json",
                     "adversarial": "eval_adversarial.json", "extension": "eval_helpdesk_extension.json"}
    ticket_module = importlib.import_module("tools.create_ticket.tool")
    search_module = importlib.import_module("tools.search_device_info.tool")
    original_ticket_dir = ticket_module.TICKET_DIR
    original_post = search_module.requests.post
    original_argv = sys.argv[:]
    external_requests: list[dict] = []
    reports: list[dict] = []
    batch = datetime.now().strftime("%Y%m%dT%H%M%S")
    audit_path = ROOT / "artifacts" / f"submission_audit_{batch}.json"

    def observed_post(url, *post_args, **post_kwargs):
        if url == "https://api.tavily.com/search":
            external_requests.append({"url": url, "body": post_kwargs.get("json")})
        return original_post(url, *post_args, **post_kwargs)

    try:
        search_module.requests.post = observed_post
        for suite in args.suites:
            before_requests = len(external_requests)
            before_runs = set((ROOT / "runs").glob("*.json"))
            with tempfile.TemporaryDirectory(prefix="day04-eval-tickets-") as isolated:
                ticket_module.TICKET_DIR = Path(isolated)
                sys.argv = ["run_eval.py", "--provider", "openrouter", "--model", args.model,
                            "--version", args.version, "--suite", suite,
                            "--eval-cases", str(ROOT / "data" / dataset_files[suite])]
                print(f"\nStarting {suite}: original evaluator, isolated mock tickets", flush=True)
                run_eval.main()
                new_runs = set((ROOT / "runs").glob("*.json")) - before_runs
                if len(new_runs) != 1:
                    raise RuntimeError(f"Expected one new {suite} run, found {len(new_runs)}")
                run_path = new_runs.pop()
                run = json.loads(run_path.read_text(encoding="utf-8"))
                files = {p.stem: p for p in Path(isolated).glob("*.json")}
                created = []
                tool_errors = []
                for case in run["results"]:
                    for event in case["tool_results"]:
                        result = event.get("result", {})
                        if isinstance(result, dict) and result.get("error"):
                            tool_errors.append({"case": case["id"], "tool": event["tool"],
                                                "error": result["error"]})
                        if isinstance(result, dict) and result.get("status") == "created":
                            path = files.get(result["ticket_id"])
                            created.append({"case": case["id"], "ticket_id": result["ticket_id"],
                                            "file_existed": path is not None,
                                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path else None})
                report = {"suite": suite, "run": str(run_path.relative_to(ROOT)).replace("\\", "/"),
                          "artifact_version": run["artifact_version"], "summary": run["summary"],
                          "ticket_file_count": len(files), "ticket_writes": created,
                          "tool_errors": tool_errors,
                          "external_search_requests": external_requests[before_requests:]}
            report["temporary_ticket_directory_removed"] = not Path(isolated).exists()
            reports.append(report)
            audit_path.write_text(json.dumps({"generated_at": datetime.now().isoformat(timespec="seconds"),
                "method": "Unchanged run_eval.main; only TICKET_DIR isolated and requests.post observed; no model replies mocked.",
                "suites": reports}, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Audit updated: {audit_path.name}", flush=True)
    finally:
        ticket_module.TICKET_DIR = original_ticket_dir
        search_module.requests.post = original_post
        sys.argv = original_argv


if __name__ == "__main__":
    main()
