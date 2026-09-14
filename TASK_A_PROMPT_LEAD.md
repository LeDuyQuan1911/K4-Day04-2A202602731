# NHIỆM VỤ CỦA BẠN — Người A: Prompt Architect / Nhóm trưởng

## Bối cảnh
Đây là bài Lab Day 04 — xây dựng IT Helpdesk Agent cho công ty giả lập Northstar Labs. Bạn là **nhóm trưởng** (Người A) trong nhóm 5 người.
**Việc của bạn**: Cải tiến `system_prompt.md` để agent chọn đúng tool, hỏi đúng câu, và không làm bậy.

## Bạn CHỈ được sửa/tạo các file này:
```
starter_v0/artifacts/system_prompt.md   ← SỬA (việc chính)
starter_v0/artifacts/version_log.csv    ← CẬP NHẬT metric mỗi version
TEAMMATES.md                            ← TẠO/SỬA (điền info 5 người)
```
KHÔNG sửa `tools.yaml`, `eval_group.json`, `app.py`, `REPORT.md` phần B4a/B5/B6 — đó là việc của người B, C, D, E.

## Đã làm xong
- ✅ Fork repo, setup env, điền API key
- ✅ Chạy eval v0 baseline: **66.7%** (20/30 PASS)
- ✅ Cải tiến prompt v1: **73.3%** (22/30 PASS)  
- ✅ Push v0 + v1 runs lên repo
- ✅ Tạo `version_log.csv` với data v0 + v1

## Còn phải làm

### 1. Điền TEAMMATES.md
Mở file `TEAMMATES.md` ở thư mục gốc, điền đầy đủ info 5 thành viên (họ tên thật, MSSV thật, GitHub username thật, vai trò).

### 2. Cải tiến system_prompt.md v2

**8 cases vẫn FAIL ở v1:**

| Case | Loại lỗi | Mô tả |
|---|---|---|
| H02_device_routing | wrong_tool | Routing thiết bị cụ thể sai tool |
| H03_kb_routing | wrong_tool | Routing knowledge base sai tool |
| H13_parallel_status_and_device | wrong_tool | Cần gọi cả check_service_status VÀ inspect_device nhưng thiếu |
| H10_missing_asset | missing_info | User không cho asset ID nhưng agent không hỏi lại |
| H11_missing_employee | missing_info | User không cho employee ID nhưng agent không hỏi lại |
| H19_ambiguous_environment | missing_info | Environment mơ hồ (production hay staging) nhưng agent không hỏi |
| H12_confirm_before_ticket | wrong_boundary | Agent tạo ticket mà không xin confirm trước |
| M05_ticket_confirmation | wrong_boundary | Confirm flow cho ticket bị sai |

**Hypothesis v2**: Thêm ví dụ cụ thể cho multi-tool scenarios và nhấn mạnh mạnh hơn về missing info + confirmation sẽ giảm wrong_tool và missing_info errors.

**Gợi ý sửa v2:**
- Thêm rule: Khi user hỏi về cả dịch vụ chung VÀ thiết bị cụ thể → gọi CẢ `check_service_status` VÀ `inspect_device`
- Nhấn mạnh: Nếu user nói "laptop tôi" hoặc "máy tôi" mà KHÔNG cho asset ID → BẮT BUỘC dùng `clarify` hỏi asset ID trước
- Nhấn mạnh: Nếu user nói "nhân viên" mà KHÔNG cho employee ID → BẮT BUỘC dùng `clarify` hỏi employee ID trước
- Thêm rule: Khi environment không rõ (user không nói production hay staging) → dùng `clarify` hỏi hoặc mặc định production
- Nhấn mạnh mạnh hơn: `create_ticket` BẮT BUỘC phải có bước `clarify` confirm TRƯỚC. Không bao giờ gọi `create_ticket` với `confirmed: true` ở lần đầu tiên

### 3. Chạy eval v2
Sau khi sửa prompt v2:
```powershell
cd starter_v0
.\.venv\Scripts\Activate.ps1
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
```

### 4. Cải tiến system_prompt.md v3
Dựa trên failures còn lại từ v2, tiếp tục cải tiến. V3 là version cuối cùng.

Sau khi sửa prompt v3, chạy eval:
```powershell
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

### 5. Cập nhật version_log.csv
File: `starter_v0/artifacts/version_log.csv`
Format: `version,author,changed_artifact,artifact_version,prompt_hash,tools_hash,reason,hypothesis,metric_name,metric_before,metric_after,run_file`

Thêm dòng v2 và v3 với metric thực tế sau khi chạy eval.

### 6. Review và merge PR của team
Khi 4 thành viên push branch lên:
- Review PR của B (tools.yaml), C (eval_group.json), D (app.py), E (REPORT.md)
- Merge bằng **merge commit** (KHÔNG squash) để giữ commit của từng người
- Kiểm tra `git log --format="%h | %an <%ae> | %s"` — đảm bảo 5 người đều có commit

### 7. Viết self-reflection
Trong `REPORT.md` phần C2, viết mục riêng của bạn:
```markdown
### [Họ tên] — [MSSV]
- **Vai trò/phần việc được nhận:** A — Prompt Architect / Lead
- **Những gì tôi đã thay đổi trong repo chung:** Cải tiến system_prompt.md qua 3 versions...
- **File hoặc artifact liên quan:** system_prompt.md, version_log.csv
- **Commit hash hoặc pull request:** ...
- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:** ...
- **Khó khăn tôi gặp và cách tôi xử lý:** ...
- **Điều tôi học được từ phần việc này:** ...
- **Nếu làm lại, tôi sẽ cải thiện điều gì:** ...
```

### 8. Push và nộp bài
```powershell
git add starter_v0/artifacts/system_prompt.md starter_v0/artifacts/version_log.csv TEAMMATES.md
git commit -m "feat(prompt): final v3 system prompt with all improvements"
git push origin main
```
Nộp URL repo lên VLearn. Nhắc 4 thành viên cùng nộp cùng URL.

## Lưu ý
- KHÔNG hard-code case IDs trong prompt
- KHÔNG copy nguyên văn từ eval cases vào prompt
- Giữ prompt concise — không viết quá dài
- Mỗi version phải có hypothesis cụ thể, không sửa bừa
- KHÔNG commit `.env`, API key, `.venv`, cache, generated tickets
