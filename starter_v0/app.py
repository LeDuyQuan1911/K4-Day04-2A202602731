"""Streamlit UI for IT Helpdesk Agent — reuses chat.run_model_tool_loop."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import run_model_tool_loop, write_transcript, now_iso, safe_slug, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)


def init_state() -> None:
    defaults: dict[str, Any] = {
        "history": [],
        "ui_messages": [],
        "transcript_path": None,
        "transcript": None,
        "turn_index": 0,
        "ready": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_session(provider_name: str, model: str | None, version: str, max_rounds: int) -> None:
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(declarations)
    provider = make_provider(provider_name)
    selected_model = model or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", timestamp])
    transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": selected_model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "ui": "streamlit",
        "max_tool_rounds": max_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    write_transcript(transcript_path, transcript)

    st.session_state.provider = provider
    st.session_state.model = selected_model
    st.session_state.system_prompt = system_prompt
    st.session_state.openai_tools = openai_tools
    st.session_state.artifact_version = artifact_version
    st.session_state.max_rounds = max_rounds
    st.session_state.transcript_path = transcript_path
    st.session_state.transcript = transcript
    st.session_state.history = []
    st.session_state.ui_messages = []
    st.session_state.turn_index = 0
    st.session_state.ready = True


def handle_user_message(user_text: str) -> None:
    st.session_state.turn_index += 1
    messages = [
        {"role": "system", "content": st.session_state.system_prompt},
        *trim_history(st.session_state.history, 5),
        {"role": "user", "content": user_text},
    ]
    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    try:
        result = run_model_tool_loop(
            provider=st.session_state.provider,
            messages=messages,
            tools=st.session_state.openai_tools,
            model=st.session_state.model,
            max_tool_rounds=st.session_state.max_rounds,
        )
        turn_record.update(result)
        assistant_text = result["assistant_text"]
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": assistant_text})
        st.session_state.ui_messages.append({
            "role": "user",
            "content": user_text,
        })
        st.session_state.ui_messages.append({
            "role": "assistant",
            "content": assistant_text,
            "rounds": result.get("rounds", []),
            "tool_events": result.get("tool_events", []),
            "status": result.get("status"),
        })
    except Exception as exc:
        turn_record.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {str(exc)}",
        })
        st.session_state.ui_messages.append({"role": "user", "content": user_text})
        st.session_state.ui_messages.append({
            "role": "assistant",
            "content": f"Provider error: {turn_record['error']}",
            "rounds": [],
            "tool_events": [],
            "status": "provider_error",
        })

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)


def render_tool_trace(msg: dict[str, Any]) -> None:
    events = msg.get("tool_events") or []
    rounds = msg.get("rounds") or []
    if not events and not rounds:
        st.caption("Không có tool call trong lượt này.")
        return
    with st.expander("Tool trace", expanded=True):
        for event in events:
            st.markdown(f"**{event.get('tool')}**")
            st.code(json.dumps(event.get("args", {}), ensure_ascii=False, indent=2), language="json")
            result = event.get("result", {})
            if isinstance(result, dict) and result.get("error"):
                st.error(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                st.code(json.dumps(result, ensure_ascii=False, indent=2, default=str), language="json")
        if rounds:
            st.caption(f"Rounds: {len(rounds)} | status: {msg.get('status')}")


def main() -> None:
    st.set_page_config(page_title="Northstar IT Helpdesk Agent", layout="wide")
    init_state()
    st.title("Northstar Labs — IT Helpdesk Agent")
    st.write("UI dùng chung `run_model_tool_loop` với CLI chat để audit tool calls.")

    with st.sidebar:
        st.header("Session")
        provider = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
        model = st.text_input("Model (để trống = default provider)", value="")
        version = st.text_input("Artifact version", value="v3")
        max_rounds = st.number_input("Max tool rounds", min_value=1, max_value=8, value=4)
        if st.button("Start / Reset session", type="primary"):
            try:
                start_session(provider, model.strip() or None, version.strip() or "v3", int(max_rounds))
                st.success("Session sẵn sàng.")
            except Exception as exc:
                st.error(f"Không khởi tạo được session: {exc}")

        if st.session_state.ready:
            av = st.session_state.artifact_version
            st.markdown(f"**artifact_version:** `{av.artifact_version}`")
            st.markdown(f"**model:** `{st.session_state.model}`")
            st.markdown(f"**transcript:** `{st.session_state.transcript_path}`")
            st.caption(f"prompt_hash: {av.prompt_hash[:12]}…")
            st.caption(f"tools_hash: {av.tools_hash[:12]}…")

    if not st.session_state.ready:
        st.info("Chọn provider/version ở sidebar rồi bấm **Start / Reset session**.")
        return

    for msg in st.session_state.ui_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                render_tool_trace(msg)

    user_text = st.chat_input("Nhập yêu cầu IT helpdesk…")
    if user_text:
        handle_user_message(user_text.strip())
        st.rerun()


if __name__ == "__main__":
    main()
