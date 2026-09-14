from __future__ import annotations

"""Streamlit chat UI for the IT Helpdesk Agent.

Reuses `run_model_tool_loop` from chat.py (no new agent loop). The goal is a
simple, auditable trace: every round, tool call, args, result/error, status,
artifact version/hashes and the transcript path are visible on screen.
"""

import json
import os
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
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini"]
# Model prefilled in the sidebar per provider. Blank = use provider's own default.
# Note: reasoning models (gpt-5.x, o-series) reject function tools on
# /v1/chat/completions, so keep a plain tool-calling model here.
PROVIDER_DEFAULT_MODEL = {
    "openrouter": "",
    "openai": "",
    "anthropic": "",
    "gemini": "",
}
PROVIDER_KEY_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"

STATUS_LABEL = {
    "answered": ("✅", "answered"),
    "waiting_for_user": ("❓", "waiting_for_user"),
    "max_tool_rounds": ("⚠️", "max_tool_rounds"),
    "provider_error": ("❌", "provider_error"),
}


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def new_session(provider_name: str, model: str | None, version: str, history_window: int, max_tool_rounds: int) -> None:
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", timestamp])
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "ui": "streamlit",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.messages = []   # what is rendered
    st.session_state.history = []    # what the model sees (user/assistant pairs)
    st.session_state.turn_index = 0


def default_provider_index() -> int:
    """Pick the first provider whose API key is present in the environment."""
    for i, name in enumerate(PROVIDERS):
        if os.getenv(PROVIDER_KEY_ENV[name]):
            return i
    return 0


def get_provider(name: str):
    cache = st.session_state.setdefault("_providers", {})
    if name not in cache:
        cache[name] = make_provider(name)
    return cache[name]


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def status_badge(status: str) -> str:
    icon, label = STATUS_LABEL.get(status, ("•", status))
    return f"{icon} `{label}`"


def render_tool_event(event: dict[str, Any]) -> None:
    result = event.get("result")
    is_error = isinstance(result, dict) and "error" in result
    st.markdown("**Args**")
    st.json(event.get("args", {}))
    st.markdown("**Error**" if is_error else "**Result**")
    if is_error:
        st.error(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        st.json(result if result is not None else {})


def render_turn_trace(turn: dict[str, Any]) -> None:
    """Rounds → tool calls → args/result. This is the audit view."""
    rounds = turn.get("rounds") or []
    events = turn.get("tool_events") or []
    st.caption(
        f"status: {status_badge(turn.get('status', '?'))} · "
        f"rounds: {len(rounds)} · tool calls: {len(events)}"
    )
    if turn.get("error"):
        st.error(turn["error"])

    for rnd in rounds:
        calls = rnd.get("tool_calls") or []
        results = rnd.get("tool_results") or []
        title = f"Round {rnd.get('round')} — " + (
            ", ".join(c["name"] for c in calls) if calls else "final answer (no tool call)"
        )
        with st.expander(title, expanded=bool(calls)):
            if rnd.get("assistant_text"):
                st.markdown("**Assistant text (this round)**")
                st.markdown(rnd["assistant_text"])
            for i, call in enumerate(calls):
                st.markdown(f"🔧 **`{call['name']}`**")
                if i < len(results):
                    render_tool_event(results[i])
                else:
                    st.json(call.get("args", {}))
                    st.warning("No result recorded for this call.")
                st.divider()


def render_message(msg: dict[str, Any]) -> None:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"] or "_(empty response)_")
        if msg["role"] == "assistant" and "turn" in msg:
            render_turn_trace(msg["turn"])


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.set_page_config(page_title="IT Helpdesk Agent", page_icon="🖥️", layout="wide")
st.title("🖥️ IT Helpdesk Agent — Northstar Labs")

with st.sidebar:
    st.header("Run config")
    provider_name = st.selectbox("Provider", PROVIDERS, index=default_provider_index())
    if not os.getenv(PROVIDER_KEY_ENV[provider_name]):
        st.warning(f"`{PROVIDER_KEY_ENV[provider_name]}` chưa được đặt trong `.env`.")
    model_input = st.text_input(
        "Model (blank = provider default)",
        value=PROVIDER_DEFAULT_MODEL[provider_name],
        key=f"model_{provider_name}",
    )
    version_label = st.text_input("Artifact version label", value="v3")
    history_window = st.number_input("History window (pairs)", min_value=0, max_value=20, value=5)
    max_tool_rounds = st.number_input("Max tool rounds", min_value=1, max_value=10, value=4)
    model = model_input.strip() or None

    if st.button("🔄 New session / reset", use_container_width=True):
        new_session(provider_name, model, version_label, int(history_window), int(max_tool_rounds))
        st.rerun()

    st.divider()
    st.header("Artifact version")
    ver = build_artifact_version(version_label, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    st.code(ver.artifact_version, language=None)
    st.markdown(f"**Prompt hash**\n`{ver.prompt_hash}`")
    st.markdown(f"**Tools hash**\n`{ver.tools_hash}`")
    st.caption(f"prompt: `{SYSTEM_PROMPT_PATH.relative_to(ROOT)}`  \ntools: `{TOOLS_PATH.relative_to(ROOT)}`")

if "transcript" not in st.session_state:
    new_session(provider_name, model, version_label, int(history_window), int(max_tool_rounds))

# If sidebar config drifted from the recording session: auto-apply when the
# session is still empty, otherwise ask for an explicit reset (keeps transcript honest).
tr = st.session_state.transcript
config_changed = (
    tr["provider"] != provider_name
    or tr["version"] != version_label
    or tr["model"] != model
    or tr["history_window"] != int(history_window)
    or tr["max_tool_rounds"] != int(max_tool_rounds)
)
if config_changed and not tr["turns"]:
    new_session(provider_name, model, version_label, int(history_window), int(max_tool_rounds))
    tr = st.session_state.transcript
elif config_changed:
    st.sidebar.warning(
        f"Session is recording with provider=`{tr['provider']}`, version=`{tr['version']}`, "
        f"model=`{tr['model']}`. Click **New session** to apply the new config."
    )

with st.sidebar:
    st.divider()
    st.header("Transcript")
    st.code(str(st.session_state.transcript_path.relative_to(ROOT)), language=None)
    st.caption(f"turns recorded: {len(tr['turns'])} · session provider: `{tr['provider']}` · model: `{tr['model']}`")

# Artifacts are loaded fresh each rerun so hash on screen == what the model gets.
system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
openai_tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))

for msg in st.session_state.messages:
    render_message(msg)

if prompt := st.chat_input("Nhập yêu cầu hỗ trợ IT..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.turn_index += 1
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, tr["history_window"]),
        {"role": "user", "content": prompt},
    ]
    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner(f"Running model/tool loop (max {tr['max_tool_rounds']} rounds)..."):
            try:
                provider = get_provider(tr["provider"])
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=tr["model"],
                    max_tool_rounds=tr["max_tool_rounds"],
                )
                turn_record.update(result)
                assistant_text = result["assistant_text"]
                st.session_state.history.append({"role": "user", "content": prompt})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})
            except Exception as exc:
                assistant_text = ""
                turn_record.update({
                    "status": "provider_error",
                    "error": f"{type(exc).__name__}: {exc}",
                })

        turn_record["ended_at"] = now_iso()
        st.markdown(assistant_text or "_(no response)_")
        render_turn_trace(turn_record)

    tr["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, tr)
    st.session_state.messages.append({"role": "assistant", "content": assistant_text, "turn": turn_record})
    st.sidebar.success(f"Transcript saved: `{st.session_state.transcript_path.name}`")
