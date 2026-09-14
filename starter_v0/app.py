"""Streamlit chat UI for the IT Helpdesk Agent.

Reuses `run_model_tool_loop` from chat.py so the UI, the CLI chat and the eval
runner share one agent loop and one transcript format. The UI is a trace
viewer first: every turn shows tool name, args, result/error, round and status,
plus the artifact version/hashes and the transcript path.

Run from starter_v0/:
    streamlit run app.py
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDERS = ["openai", "openrouter", "anthropic", "gemini"]
# gpt-4o-mini is the model used for every run in runs/ and version_log.csv.
DEFAULT_MODELS = {"openai": "gpt-4o-mini", "openrouter": "openai/gpt-4o-mini", "anthropic": "", "gemini": ""}
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"

st.set_page_config(page_title="IT Helpdesk Agent", page_icon="🛠️", layout="wide")


# ---------------------------------------------------------------- session ----
def start_session(provider_name: str, model: str, version: str, history_window: int, max_tool_rounds: int) -> None:
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    provider = make_provider(provider_name)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", timestamp])
    st.session_state.update(
        {
            "provider_name": provider_name,
            "provider": provider,
            "model": model or None,
            "version": version,
            "history_window": history_window,
            "max_tool_rounds": max_tool_rounds,
            "system_prompt": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
            "openai_tools": to_openai_tools(load_tool_declarations(TOOLS_PATH)),
            "artifact": artifact_version,
            "transcript_path": TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json",
            "transcript": {
                "transcript_id": transcript_id,
                **artifact_version_dict(artifact_version),
                "provider": provider_name,
                "model": model or getattr(provider, "default_model", None),
                "system_prompt": str(SYSTEM_PROMPT_PATH),
                "tools": str(TOOLS_PATH),
                "history_window": history_window,
                "max_tool_rounds": max_tool_rounds,
                "ui": "streamlit",
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "turns": [],
            },
            "history": [],  # user/assistant pairs fed back to the model
            "turns": [],  # full turn records rendered in the UI
        }
    )


def run_turn(user_text: str) -> dict[str, Any]:
    s = st.session_state
    messages = [
        {"role": "system", "content": s.system_prompt},
        *trim_history(s.history, s.history_window),
        {"role": "user", "content": user_text},
    ]
    turn: dict[str, Any] = {
        "turn_index": len(s.turns) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    try:
        result = run_model_tool_loop(
            provider=s.provider,
            messages=messages,
            tools=s.openai_tools,
            model=s.model,
            max_tool_rounds=s.max_tool_rounds,
        )
        turn.update(result)
        s.history.append({"role": "user", "content": user_text})
        s.history.append({"role": "assistant", "content": result["assistant_text"]})
    except Exception as exc:  # provider/network failure is evidence too
        turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
    turn["ended_at"] = now_iso()
    s.turns.append(turn)
    s.transcript["turns"].append(turn)
    write_transcript(s.transcript_path, s.transcript)
    return turn


# --------------------------------------------------------------- rendering ---
STATUS_ICON = {"answered": "✅", "waiting_for_user": "❓", "max_tool_rounds": "⚠️", "provider_error": "❌"}


def render_reply(text: str | None) -> None:
    """Show the JSON `reply` field as prose when the model followed the output format."""
    if not text:
        st.markdown("_(empty response)_")
        return
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "reply" in data:
            st.markdown(data["reply"])
            meta = {k: v for k, v in data.items() if k != "reply"}
            st.caption(" · ".join(f"{k}: `{v}`" for k, v in meta.items()))
            return
    except (json.JSONDecodeError, TypeError):
        pass
    st.markdown(text)


def render_trace(turn: dict[str, Any]) -> None:
    status = turn.get("status", "?")
    n_calls = len(turn.get("tool_events", []))
    n_rounds = len(turn.get("rounds", []))
    label = f"{STATUS_ICON.get(status, '•')} status: {status} · {n_rounds} round(s) · {n_calls} tool call(s)"
    with st.expander(label, expanded=status != "answered" or n_calls > 0):
        if turn.get("error"):
            st.error(turn["error"])
        for rnd in turn.get("rounds", []):
            st.markdown(f"**Round {rnd['round']}**")
            if rnd.get("assistant_text"):
                st.caption("assistant text before tool calls:")
                st.code(rnd["assistant_text"], language="json")
            if not rnd.get("tool_calls"):
                st.caption("no tool calls — final answer")
            for event in rnd.get("tool_results", []):
                result = event.get("result") or {}
                is_error = isinstance(result, dict) and result.get("error")
                header = f"🔧 `{event['tool']}`" + ("  🔴 error" if is_error else "")
                st.markdown(header)
                left, right = st.columns(2)
                with left:
                    st.caption("args")
                    st.code(json.dumps(event.get("args", {}), ensure_ascii=False, indent=2), language="json")
                with right:
                    st.caption("result")
                    st.code(json.dumps(result, ensure_ascii=False, indent=2, default=str)[:6000], language="json")
        st.caption(f"{turn.get('started_at')} → {turn.get('ended_at')}")


# ----------------------------------------------------------------- sidebar ---
with st.sidebar:
    st.title("🛠️ IT Helpdesk Agent")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model (blank = provider default)", value=DEFAULT_MODELS.get(provider_name, ""))
    version = st.text_input("Artifact version label", value="v3")
    history_window = st.slider("History window (user/assistant pairs)", 0, 10, 5)
    max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)
    if st.button("🔄 New session", type="primary", use_container_width=True) or "transcript" not in st.session_state:
        start_session(provider_name, model, version, history_window, max_tool_rounds)

    s = st.session_state
    st.divider()
    st.subheader("Artifact")
    st.code(s.artifact.artifact_version, language="text")
    st.caption(f"prompt sha256: `{s.artifact.prompt_hash}`")
    st.caption(f"tools sha256: `{s.artifact.tools_hash}`")
    st.caption(f"provider: `{s.provider_name}` · model: `{s.transcript['model']}`")
    st.subheader("Transcript")
    st.code(str(s.transcript_path.relative_to(ROOT)), language="text")
    st.caption(f"{len(s.turns)} turn(s) saved")
    with st.expander("System prompt in use"):
        st.markdown(s.system_prompt)
    with st.expander("Declared tools"):
        for t in s.openai_tools:
            fn = t.get("function", t)
            st.markdown(f"- `{fn['name']}` — {fn.get('description', '')[:140]}…")


# -------------------------------------------------------------------- main ---
st.header("Chat")
st.caption("Mọi dữ liệu là giả lập. Tool `create_ticket` chỉ ghi file khi có xác nhận rõ ràng.")

for turn in st.session_state.turns:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        if turn.get("status") == "provider_error":
            st.error(turn.get("error"))
        else:
            render_reply(turn.get("assistant_text"))
        render_trace(turn)

if prompt := st.chat_input("Ví dụ: Kiểm tra VPN production và máy LT-204"):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Đang chạy agent loop…"):
            turn = run_turn(prompt)
        if turn.get("status") == "provider_error":
            st.error(turn.get("error"))
        else:
            render_reply(turn.get("assistant_text"))
        render_trace(turn)
    st.rerun()
