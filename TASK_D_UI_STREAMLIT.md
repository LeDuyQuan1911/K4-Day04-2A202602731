# NHIỆM VỤ CỦA BẠN — Người D: UI Developer (Streamlit)

## Bối cảnh
Đây là bài Lab Day 04 — xây dựng IT Helpdesk Agent cho công ty giả lập Northstar Labs. Bạn là thành viên D trong nhóm 5 người.
**Việc của bạn**: Xây một giao diện chat bằng Streamlit để demo agent.

## Bạn CHỈ được tạo/sửa các file này:
```
starter_v0/app.py              ← TẠO MỚI (file chính)
starter_v0/requirements.txt    ← THÊM 1 DÒNG: streamlit>=1.30.0
```
KHÔNG sửa bất kỳ file nào khác để tránh merge conflict.

## Setup trước khi làm
```powershell
cd starter_v0
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install "streamlit>=1.30.0"
cp .env.example .env
# Điền API key vào .env (OpenRouter/OpenAI/Anthropic/Gemini)
```

## Trước tiên: Đọc hiểu các file quan trọng
1. `starter_v0/chat.py` — chứa hàm `run_model_tool_loop()` mà UI PHẢI tái sử dụng
2. `starter_v0/agent.py` — agent chính
3. `starter_v0/versioning.py` — hàm `build_artifact_version()` để lấy version + hash
4. `starter_v0/artifacts/system_prompt.md` — system prompt
5. `starter_v0/artifacts/tools.yaml` — tool declarations

## Nhiệm vụ cụ thể

Tạo file `starter_v0/app.py` — một trang chat Streamlit với các yêu cầu:

### UI PHẢI hiển thị:
1. **Chat messages**: user input và agent response
2. **Tool calls**: mỗi lần agent gọi tool, hiển thị:
   - Tên tool (VD: `inspect_device`)
   - Arguments (VD: `{"asset_id": "LT-318", "check": "vpn"}`)
   - Tool result hoặc error
3. **Artifact version**: hiển thị version string + prompt hash + tools hash (dùng `build_artifact_version`)
4. **Round/status**: hiển thị trạng thái hiện tại

### Quy tắc quan trọng:
- **BẮT BUỘC** tái sử dụng `run_model_tool_loop` từ `chat.py`. KHÔNG viết agent loop mới.
- Dùng `st.chat_input()` và `st.chat_message()` cho giao diện chat
- Dùng `st.sidebar` để hiển thị version info
- Dùng `st.expander` hoặc `st.json` để hiển thị tool calls chi tiết

### Gợi ý cấu trúc code:
```python
import streamlit as st
from pathlib import Path
from env_loader import load_lab_env
from versioning import build_artifact_version

# Load environment
load_lab_env(Path.cwd())

# Page config
st.set_page_config(page_title="IT Helpdesk Agent", page_icon="🖥️", layout="wide")
st.title("🖥️ IT Helpdesk Agent — Northstar Labs")

# Sidebar: version info
ver = build_artifact_version(
    "v3",
    Path("artifacts/system_prompt.md"),
    Path("artifacts/tools.yaml")
)
st.sidebar.markdown(f"**Version**: `{ver.artifact_version}`")
st.sidebar.markdown(f"**Prompt hash**: `{ver.prompt_hash[:12]}`")
st.sidebar.markdown(f"**Tools hash**: `{ver.tools_hash[:12]}`")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Nếu có tool_calls, hiển thị trong expander
        if "tool_calls" in msg:
            for tc in msg["tool_calls"]:
                with st.expander(f"🔧 {tc['name']}"):
                    st.json(tc.get("arguments", {}))
                    if "result" in tc:
                        st.markdown("**Result:**")
                        st.json(tc["result"])

# Chat input
if prompt := st.chat_input("Nhập yêu cầu hỗ trợ IT..."):
    # Thêm user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gọi agent — TÁI SỬ DỤNG run_model_tool_loop
    # Đọc chat.py để hiểu cách gọi hàm này đúng cách
    # ... implement phần gọi agent ở đây ...

    # Hiển thị response
    with st.chat_message("assistant"):
        st.markdown(response_text)
```

### Provider setup:
Đọc file `chat.py` để biết cách khởi tạo provider. Agent hỗ trợ: openrouter, openai, anthropic, gemini.
Có thể thêm dropdown ở sidebar để chọn provider.

## Test
```powershell
cd starter_v0
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```
Mở browser tại `http://localhost:8501`, thử gửi: "VPN có hoạt động không?" và xem tool calls hiển thị.

## Khi xong
```powershell
git add starter_v0/app.py starter_v0/requirements.txt
git commit -m "feat(ui): add Streamlit chat UI with tool call display"
git push -u origin contrib/<YOUR_GITHUB_USERNAME>
```
Tạo Pull Request vào branch main của repo chung.

## Lưu ý
- KHÔNG sửa `chat.py`, `agent.py` hay bất kỳ file nào khác
- UI đơn giản nhưng trace rõ tool behavior quan trọng hơn UI đẹp mà không audit được
- Đảm bảo hiển thị đầy đủ: tool name, args, result, version
