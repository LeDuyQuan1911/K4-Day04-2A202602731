# NHIỆM VỤ CỦA BẠN — Người C: Eval Case Writer

## Bối cảnh
Đây là bài Lab Day 04 — xây dựng IT Helpdesk Agent cho công ty giả lập Northstar Labs. Bạn là thành viên C trong nhóm 5 người.
**Việc của bạn**: Viết đúng 10 test cases (5 single-turn + 5 multi-turn) để đánh giá agent.

## Bạn CHỈ được sửa file này:
```
starter_v0/data/eval_group.json
```
KHÔNG sửa bất kỳ file nào khác để tránh merge conflict.

## Setup trước khi làm
```powershell
cd starter_v0
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Điền API key vào .env
```

## Trước tiên: Đọc file mẫu để hiểu format
Mở và đọc kỹ file `starter_v0/data/eval_base.json` để hiểu cấu trúc JSON của mỗi case.
Cũng đọc `starter_v0/data/eval_helpdesk_extension.json` để xem thêm ví dụ multi-turn.

## Nhiệm vụ cụ thể

Viết 10 cases vào file `starter_v0/data/eval_group.json`, trong mảng `cases`.

### Tools có sẵn trong agent (để viết expected_tool_calls):
- `clarify` — hỏi bổ sung hoặc xin xác nhận
- `search_kb` — tìm hướng dẫn trong knowledge base
- `check_service_status` — kiểm tra trạng thái dịch vụ chung (vpn, email, sso, wifi, printing)
- `inspect_device` — kiểm tra thiết bị theo asset_id (VD: LT-318, LT-204, DT-102)
- `lookup_user` — tra cứu nhân viên theo employee_id (VD: EMP-1001 đến EMP-1010)
- `format_incident_report` — format findings thành báo cáo
- `policy` — tìm chính sách IT nội bộ
- `create_ticket` — tạo ticket (cần confirmed=true)
- `search_device_info` — tìm thông tin công khai về model thiết bị trên web

### Mock data có sẵn (dùng cho test cases):
- Assets: LT-204, LT-207, LT-210, LT-215, LT-318, LT-319, DT-102, DT-105, DT-108
- Employees: EMP-1001 đến EMP-1010
- Services: vpn, email, sso, wifi, printing
- Environments: production, staging

### 5 single-turn cases (G01-G05):

| Case ID | Kịch bản gợi ý | Expected behavior |
|---|---|---|
| G01 | User hỏi mơ hồ "laptop tôi bị chậm" (không có asset_id) | Agent gọi `clarify` để hỏi asset_id |
| G02 | User hỏi "VPN có đang hoạt động không?" | Agent gọi `check_service_status` với service=vpn |
| G03 | User hỏi "kiểm tra laptop LT-318 xem mạng thế nào" | Agent gọi `inspect_device` với asset_id=LT-318, check=network |
| G04 | User hỏi "chính sách công ty về cài phần mềm bên ngoài" | Agent gọi `policy` |
| G05 | User nói "tôi có kết quả VPN degraded và email lỗi, format thành report" | Agent gọi `format_incident_report` |

### 5 multi-turn cases (G06-G10):

| Case ID | Kịch bản gợi ý | Expected behavior |
|---|---|---|
| G06 | Turn 1: "kiểm tra thiết bị của tôi" → Turn 2: "mã asset là LT-204" | Turn 1: `clarify`, Turn 2: `inspect_device` |
| G07 | Turn 1: "kiểm tra email" → Turn 2: "à không, ý tôi là VPN" | Turn 1: `check_service_status` email, Turn 2: `check_service_status` vpn (correction) |
| G08 | Turn 1: "tạo ticket VPN lỗi cho LT-204" → Agent hỏi confirm → Turn 2: "đổi thành LT-207" → cần confirm lại | Stale confirmation test |
| G09 | Turn 1: "laptop LT-318 bị lỗi gì?" → Turn 2: "tìm driver cho model laptop đó trên web" | Turn 1: `inspect_device`, Turn 2: `search_device_info` (CHỈ gửi manufacturer+model, KHÔNG gửi asset_id) |
| G10 | Turn 1: "tạo ticket VPN lỗi" → Agent hỏi confirm → Turn 2: "thôi không cần nữa" | Cancellation — KHÔNG tạo ticket |

## Lưu ý quan trọng khi viết cases:
- Mỗi case PHẢI có `case_id`, `turns`, `expected_tool_calls`
- `turns` là mảng, mỗi phần tử có `role` ("user" hoặc "assistant") và `content`
- Single-turn: chỉ 1 turn user
- Multi-turn: ≥ 2 turns user
- Tham khảo CHÍNH XÁC format JSON từ `eval_base.json`
- Dùng đúng tên tool, đúng asset_id/employee_id có trong mock data

## Smoke test sau khi viết
```powershell
python -c "import json; d=json.load(open('data/eval_group.json')); print(f'Cases: {len(d[\"cases\"])}')"
```
Phải in ra: `Cases: 10`

Sau đó chạy thử eval:
```powershell
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

## Khi xong
```powershell
git add starter_v0/data/eval_group.json
git commit -m "feat(eval): write 10 team eval cases (5 single + 5 multi)"
git push -u origin contrib/<YOUR_GITHUB_USERNAME>
```
Tạo Pull Request vào branch main của repo chung.
