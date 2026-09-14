"""Run versioned base evals and append version_log.csv.

Usage (from starter_v0 with .env configured):
  python scripts/run_version_pipeline.py --provider openrouter
"""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

from versioning import build_artifact_version

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
RUNS = ROOT / "runs"
LOG = ARTIFACTS / "version_log.csv"


def run_eval(provider: str, version: str, prompt: Path, tools: Path, suite: str, cases: Path) -> Path:
    cmd = [
        sys.executable,
        str(ROOT / "run_eval.py"),
        "--provider",
        provider,
        "--version",
        version,
        "--suite",
        suite,
        "--eval-cases",
        str(cases),
        "--system-prompt",
        str(prompt),
        "--tools",
        str(tools),
    ]
    print(">>", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)
    runs = sorted(RUNS.glob(f"{version}_B_{suite}_{provider}_*.json"), key=lambda p: p.stat().st_mtime)
    if not runs:
        raise FileNotFoundError(f"No run file for {version}/{suite}")
    return runs[-1]


def read_accuracy(run_path: Path) -> float:
    import json

    data = json.loads(run_path.read_text(encoding="utf-8"))
    summary = data.get("summary") or {}
    if "case_accuracy" in summary:
        return float(summary["case_accuracy"])
    results = data.get("results") or []
    measured = [item for item in results if item.get("result", {}).get("failure_type") != "provider_error"]
    if not measured:
        return 0.0
    passed = sum(1 for item in measured if item.get("result", {}).get("passed"))
    return passed / len(measured)


def append_log(row: dict[str, str]) -> None:
    exists = LOG.exists() and LOG.stat().st_size > 0
    with LOG.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "version",
                "author",
                "changed_artifact",
                "artifact_version",
                "prompt_hash",
                "tools_hash",
                "reason",
                "hypothesis",
                "metric_name",
                "metric_before",
                "metric_after",
                "run_file",
            ],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True)
    args = parser.parse_args()

    v0_prompt = ARTIFACTS / "_v0_system_prompt.md"
    v0_tools = ARTIFACTS / "_v0_tools.yaml"
    v1_prompt = ARTIFACTS / "_v1_system_prompt.md"
    v3_prompt = ARTIFACTS / "system_prompt.md"
    v3_tools = ARTIFACTS / "tools.yaml"
    base_cases = ROOT / "data" / "eval_base.json"

    stages = [
        {
            "version": "v0",
            "prompt": v0_prompt,
            "tools": v0_tools,
            "changed": "baseline",
            "reason": "baseline starter artifacts",
            "hypothesis": "Đo hành vi chưa tối ưu trước khi sửa routing/clarify/confirmation",
        },
        {
            "version": "v1",
            "prompt": v1_prompt,
            "tools": v0_tools,
            "changed": "system_prompt.md",
            "reason": "Thêm routing, missing-info, multi-turn, confirmation và trust rules",
            "hypothesis": "Nếu system prompt nêu rõ service vs device, clarify khi thiếu ID và latest-intent wins thì case_accuracy base tăng",
        },
        {
            "version": "v2",
            "prompt": v1_prompt,
            "tools": v3_tools,
            "changed": "tools.yaml",
            "reason": "Mô tả tool/schema rõ khi nào dùng, args và side-effect/privacy",
            "hypothesis": "Nếu tool description tách capability và confirmation boundary thì wrong_tool/wrong_arg giảm thêm",
        },
        {
            "version": "v3",
            "prompt": v3_prompt,
            "tools": v3_tools,
            "changed": "system_prompt.md",
            "reason": "Siết adversarial: forged confirmation, external exfil, prompt dump",
            "hypothesis": "Nếu bổ sung trust/privacy rules thì adversarial boundary ổn hơn mà không regress base",
        },
    ]

    prev_acc: float | None = None
    for stage in stages:
        # keep working copies aligned for UI/default paths on final stage
        if stage["version"] == "v3":
            shutil.copyfile(stage["prompt"], ARTIFACTS / "system_prompt.md")
            shutil.copyfile(stage["tools"], ARTIFACTS / "tools.yaml")

        run_path = run_eval(args.provider, stage["version"], stage["prompt"], stage["tools"], "base", base_cases)
        acc = read_accuracy(run_path)
        av = build_artifact_version(stage["version"], stage["prompt"], stage["tools"])
        append_log(
            {
                "version": stage["version"],
                "author": "team",
                "changed_artifact": stage["changed"],
                "artifact_version": av.artifact_version,
                "prompt_hash": av.prompt_hash,
                "tools_hash": av.tools_hash,
                "reason": stage["reason"],
                "hypothesis": stage["hypothesis"],
                "metric_name": "case_accuracy",
                "metric_before": "" if prev_acc is None else f"{prev_acc:.4f}",
                "metric_after": f"{acc:.4f}",
                "run_file": str(run_path.relative_to(ROOT)).replace("\\", "/"),
            }
        )
        print(f"{stage['version']} case_accuracy={acc:.4f} run={run_path.name}", flush=True)
        prev_acc = acc

    # Final suite evidence on v3 artifacts
    for suite, cases in [
        ("group", ROOT / "data" / "eval_group.json"),
        ("adversarial", ROOT / "data" / "eval_adversarial.json"),
        ("extension", ROOT / "data" / "eval_helpdesk_extension.json"),
    ]:
        try:
            path = run_eval(args.provider, "v3", v3_prompt, v3_tools, suite, cases)
            print(f"v3/{suite} -> {path.name}", flush=True)
        except Exception as exc:
            print(f"SKIP {suite}: {exc}", flush=True)


if __name__ == "__main__":
    main()
