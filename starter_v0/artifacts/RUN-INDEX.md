# Run index — toàn bộ kết quả lưu trong repository

Ngày kiểm tra: 15/09/2026. Chỉ dùng metric khi measured = total và provider errors = 0. Run lỗi vẫn giữ để audit; không xem accuracy trên tập đo thiếu là thành tích. `REPORT.md` chỉ rõ run được chọn và phân tích tool errors. Nhãn v3 lịch sử có nhiều hash; không gộp thành một thí nghiệm.

| Run | Artifact | Model | Đo được | PASS | Provider errors | Metric hợp lệ |
|---|---|---|---:|---:|---:|---|
| [v0_B_base_gemini_20260914T194127148505.json](../runs/v0_B_base_gemini_20260914T194127148505.json) | `v0+pe995a3010607+teb3e2243f237` | gemini-3.5-flash | 9/30 | 9 | 21 | Không |
| [v0_B_base_openrouter_20260914T185445775805.json](../runs/v0_B_base_openrouter_20260914T185445775805.json) | `v0+p233ec2cecfdf+teb3e2243f237` | deepseek/deepseek-chat | 30/30 | 24 | 0 | Có; vẫn cần review tool results |
| [v0_B_base_openrouter_20260914T195508787746.json](../runs/v0_B_base_openrouter_20260914T195508787746.json) | `v0+p233ec2cecfdf+teb3e2243f237` | openai/gpt-4o-mini | 30/30 | 20 | 0 | Có; vẫn cần review tool results |
| [v1_B_base_gemini_20260914T194926495776.json](../runs/v1_B_base_gemini_20260914T194926495776.json) | `v1+pe995a3010607+teb3e2243f237` | gemini-3.5-flash | 10/30 | 10 | 20 | Không |
| [v1_B_base_openrouter_20260914T195138027077.json](../runs/v1_B_base_openrouter_20260914T195138027077.json) | `v1+pe995a3010607+teb3e2243f237` | openai/gpt-4o-mini | 30/30 | 22 | 0 | Có; vẫn cần review tool results |
| [v2_B_base_openrouter_20260914T204426044480.json](../runs/v2_B_base_openrouter_20260914T204426044480.json) | `v2+pe1758b24d374+tf582f7e60d56` | openai/gpt-4o-mini | 30/30 | 27 | 0 | Có; vẫn cần review tool results |
| [v3_B_adversarial_openrouter_20260915T002402016045.json](../runs/v3_B_adversarial_openrouter_20260915T002402016045.json) | `v3+pd5c3082edac0+tf582f7e60d56` | openai/gpt-4o-mini | 12/12 | 9 | 0 | Có; vẫn cần review tool results |
| [v3_B_base_openrouter_20260914T204601052881.json](../runs/v3_B_base_openrouter_20260914T204601052881.json) | `v3+p6e4a3faa6ea0+tf582f7e60d56` | openai/gpt-4o-mini | 30/30 | 28 | 0 | Có; vẫn cần review tool results |
| [v3_B_base_openrouter_20260914T235434688157.json](../runs/v3_B_base_openrouter_20260914T235434688157.json) | `v3+paa268c1c647a+tf582f7e60d56` | openai/gpt-4o-mini | 30/30 | 26 | 0 | Có; vẫn cần review tool results |
| [v3_B_base_openrouter_20260914T235646569301.json](../runs/v3_B_base_openrouter_20260914T235646569301.json) | `v3+pe4caddc6f720+tf582f7e60d56` | openai/gpt-4o-mini | 30/30 | 26 | 0 | Có; vẫn cần review tool results |
| [v3_B_base_openrouter_20260914T235835235923.json](../runs/v3_B_base_openrouter_20260914T235835235923.json) | `v3+p740de3cbeb15+tf582f7e60d56` | openai/gpt-4o-mini | 30/30 | 26 | 0 | Có; vẫn cần review tool results |
| [v3_B_base_openrouter_20260915T002305157981.json](../runs/v3_B_base_openrouter_20260915T002305157981.json) | `v3+pd5c3082edac0+tf582f7e60d56` | openai/gpt-4o-mini | 30/30 | 26 | 0 | Có; vẫn cần review tool results |
| [v3_B_extension_openrouter_20260915T002415807091.json](../runs/v3_B_extension_openrouter_20260915T002415807091.json) | `v3+pd5c3082edac0+tf582f7e60d56` | openai/gpt-4o-mini | 10/10 | 6 | 0 | Có; vẫn cần review tool results |
| [v3_B_group_openrouter_20260914T235048015497.json](../runs/v3_B_group_openrouter_20260914T235048015497.json) | `v3+p6e4a3faa6ea0+tf582f7e60d56` | openai/gpt-4o-mini | 10/10 | 5 | 0 | Có; vẫn cần review tool results |
| [v3_B_group_openrouter_20260914T235342812672.json](../runs/v3_B_group_openrouter_20260914T235342812672.json) | `v3+paa268c1c647a+tf582f7e60d56` | openai/gpt-4o-mini | 10/10 | 5 | 0 | Có; vẫn cần review tool results |
| [v3_B_group_openrouter_20260914T235625791890.json](../runs/v3_B_group_openrouter_20260914T235625791890.json) | `v3+pe4caddc6f720+tf582f7e60d56` | openai/gpt-4o-mini | 10/10 | 9 | 0 | Có; vẫn cần review tool results |
| [v3_B_group_openrouter_20260914T235759036554.json](../runs/v3_B_group_openrouter_20260914T235759036554.json) | `v3+p740de3cbeb15+tf582f7e60d56` | openai/gpt-4o-mini | 10/10 | 7 | 0 | Có; vẫn cần review tool results |
| [v3_B_group_openrouter_20260915T002346402389.json](../runs/v3_B_group_openrouter_20260915T002346402389.json) | `v3+pd5c3082edac0+tf582f7e60d56` | openai/gpt-4o-mini | 10/10 | 9 | 0 | Có; vẫn cần review tool results |
| [v4_B_adversarial_openrouter_20260915T003120173000.json](../runs/v4_B_adversarial_openrouter_20260915T003120173000.json) | `v4+p0da57cbd1a3c+t8dae25f11a3f` | openai/gpt-4o-mini | 4/12 | 4 | 8 | Không |
| [v4_B_base_openrouter_20260915T003058556556.json](../runs/v4_B_base_openrouter_20260915T003058556556.json) | `v4+p0da57cbd1a3c+t8dae25f11a3f` | openai/gpt-4o-mini | 30/30 | 30 | 0 | Có; vẫn cần review tool results |
| [v4_B_extension_openrouter_20260915T003122980773.json](../runs/v4_B_extension_openrouter_20260915T003122980773.json) | `v4+p0da57cbd1a3c+t8dae25f11a3f` | openai/gpt-4o-mini | 0/10 | 0 | 10 | Không |
| [v4_B_group_openrouter_20260915T003111897869.json](../runs/v4_B_group_openrouter_20260915T003111897869.json) | `v4+p0da57cbd1a3c+t8dae25f11a3f` | openai/gpt-4o-mini | 10/10 | 6 | 0 | Có; vẫn cần review tool results |
| [v5_B_adversarial_openrouter_20260915T003420721389.json](../runs/v5_B_adversarial_openrouter_20260915T003420721389.json) | `v5+p01e8b16874c3+t8dae25f11a3f` | openai/gpt-4o-mini | 3/12 | 3 | 9 | Không |
| [v5_B_adversarial_openrouter_20260915T003615885643.json](../runs/v5_B_adversarial_openrouter_20260915T003615885643.json) | `v5+p01e8b16874c3+t8dae25f11a3f` | openai/gpt-4o-mini | 12/12 | 12 | 0 | Có; vẫn cần review tool results |
| [v5_B_base_openrouter_20260915T003357927235.json](../runs/v5_B_base_openrouter_20260915T003357927235.json) | `v5+p01e8b16874c3+t8dae25f11a3f` | openai/gpt-4o-mini | 30/30 | 29 | 0 | Có; vẫn cần review tool results |
| [v5_B_extension_openrouter_20260915T003423745796.json](../runs/v5_B_extension_openrouter_20260915T003423745796.json) | `v5+p01e8b16874c3+t8dae25f11a3f` | openai/gpt-4o-mini | 0/10 | 0 | 10 | Không |
| [v5_B_extension_openrouter_20260915T003630659260.json](../runs/v5_B_extension_openrouter_20260915T003630659260.json) | `v5+p01e8b16874c3+t8dae25f11a3f` | openai/gpt-4o-mini | 10/10 | 9 | 0 | Có; vẫn cần review tool results |
| [v5_B_group_openrouter_20260915T003413025567.json](../runs/v5_B_group_openrouter_20260915T003413025567.json) | `v5+p01e8b16874c3+t8dae25f11a3f` | openai/gpt-4o-mini | 10/10 | 8 | 0 | Có; vẫn cần review tool results |

Lỗi 402 trong v4/v5 là giới hạn credit/in-flight của OpenRouter. Sau khi giảm `max_tokens` và chạy lại tuần tự, adversarial/extension v5 đã có run đo đủ. Trường `provider_max_tokens` ghi cấu hình cho các run mới; các run cũ không có trường này. Account ID trong các thông báo provider lỗi mới đã được thay bằng `[REDACTED_ACCOUNT_ID]` trước khi đưa vào submission; metrics và tool traces không bị thay đổi.
