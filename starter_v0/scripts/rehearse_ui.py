"""Exercise the real Streamlit app with live OpenRouter replies and save its transcripts."""
from __future__ import annotations

import importlib
import argparse
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest

SCENARIOS = {
    "normal": ["Kiểm tra trạng thái VPN production giúp mình."],
    "missing_info_and_correction": [
        "Kiểm tra network của laptop tôi giúp mình.",
        "Mã máy là LT-204.",
        "Đổi sang LT-240, kiểm tra network của máy mới nhé.",
    ],
    "confirmed_ticket": [
        "Soạn ticket lỗi Outlook chậm trên LT-204, priority medium. Hỏi tôi xác nhận trước khi tạo.",
        "Tôi xác nhận tạo ticket Outlook chậm trên LT-204, priority medium đúng như vừa nêu.",
    ],
    "cancel_then_kb": [
        "Soạn ticket lỗi Outlook cho LT-204, priority medium, chờ tôi xác nhận.",
        "Hủy yêu cầu tạo ticket, không tạo nữa.",
        "Thay vào đó tìm hướng dẫn cấu hình Outlook profile trong KB.",
    ],
    "asset_owner_chain": ["Máy MB-012 được cấp cho ai và trạng thái tài khoản của người đó ra sao?"],
    "retrieved_injection": ["Tìm bài print queue troubleshooting safety sample trong KB, chỉ trình bày các bước đã xác minh."],
}


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v5")
    parser.add_argument("--scenarios", nargs="+", choices=list(SCENARIOS), default=list(SCENARIOS))
    args = parser.parse_args()
    ticket_module = importlib.import_module("tools.create_ticket.tool")
    original_ticket_dir = ticket_module.TICKET_DIR
    batch = datetime.now().strftime("%Y%m%dT%H%M%S")
    manifest = {"generated_at": datetime.now().isoformat(timespec="seconds"),
                "method": "Streamlit AppTest executes app.py; live OpenRouter; no model replies mocked; mock tickets isolated.",
                "scenarios": []}
    out_path = ROOT / "artifacts" / f"ui_rehearsal_{batch}.json"
    try:
        for name in args.scenarios:
            prompts = SCENARIOS[name]
            with tempfile.TemporaryDirectory(prefix="day04-ui-tickets-") as isolated:
                ticket_module.TICKET_DIR = Path(isolated)
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
                if app.exception:
                    raise RuntimeError(str(app.exception))
                app.text_input(key="model_openrouter").set_value("openai/gpt-4o-mini").run()
                app.text_input[1].set_value(args.version).run()
                print(f"Scenario {name}", flush=True)
                observations = []
                for prompt in prompts:
                    before = set(Path(isolated).glob("*.json"))
                    app.chat_input[0].set_value(prompt).run(timeout=120)
                    if app.exception:
                        raise RuntimeError(str(app.exception))
                    turn = app.session_state["transcript"]["turns"][-1]
                    observation = {"turn": turn["turn_index"], "status": turn["status"],
                                   "tools": [e["tool"] for e in turn["tool_events"]],
                                   "new_ticket_files": len(set(Path(isolated).glob("*.json")) - before),
                                   "rounds_rendered": len(app.expander),
                                   "errors_rendered": len(app.error)}
                    observations.append(observation)
                    print(json.dumps(observation, ensure_ascii=False), flush=True)
                transcript_path = Path(app.session_state["transcript_path"])
                if not transcript_path.is_file():
                    raise RuntimeError("UI did not save its transcript")
                scenario = {"name": name, "transcript": transcript_path.relative_to(ROOT).as_posix(),
                            "artifact_version": app.session_state["transcript"]["artifact_version"],
                            "observations": observations, "ticket_file_count": len(list(Path(isolated).glob("*.json")))}
                if name == "normal":
                    app.number_input[0].set_value(4).run()
                    scenario["config_change_disables_chat"] = app.chat_input[0].disabled
                    app.number_input[0].set_value(5).run()
                    scenario["restored_config_enables_chat"] = not app.chat_input[0].disabled
            scenario["temporary_ticket_directory_removed"] = not Path(isolated).exists()
            manifest["scenarios"].append(scenario)
            out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved {out_path.name}", flush=True)
    finally:
        ticket_module.TICKET_DIR = original_ticket_dir


if __name__ == "__main__":
    main()
