# Judge audit — Core M2

Nguồn số liệu: [analysis_core.json](../src/reports/analysis_core.json), khóa `judge`, sinh bằng `lab9.evidence`. FAIL là lớp dương: precision đo tỷ lệ cảnh báo đúng; recall đo phần lỗi tìm được. Không dùng accuracy thay cho recall.

| Tiêu chí | n | TP / FP / FN / TN | κ | Precision | Recall | Observed → Rogan–Gladen | Quyết định |
|---|---|---|---|---|---|---|---|
| tone_ok | 100 | 24 / 4 / 6 / 66 | 0.757 | 0.857 | 0.800 | 0.280 → 0.300 | Đạt floors; đủ điều kiện dùng cho tone trong phạm vi replay đã kiểm. |
| helpful | 100 | 9 / 0 / 21 / 70 | 0.375 | 1.000 | 0.300 | 0.090 → 0.300 | Loại khỏi gate; κ < 0.6 và R < 0.7. |

Floors: κ ≥ 0.6, P ≥ 0.8, R ≥ 0.7. Kappa không xác định khi expected agreement bằng 1 phải FAIL calibration. Rogan–Gladen hiệu chỉnh tỷ lệ lỗi của quần thể; nó không sửa từng quyết định sai của judge. Vì vậy helpful vẫn bị loại dù tỷ lệ đã hiệu chỉnh là 0.300.

## Audit bất đồng và hành động sửa rubric

Các kết luận dưới dựa trên reply và note trong CSV công khai. Chưa có người gán nhãn mới độc lập. Giữ nguyên CSV tham chiếu để kết quả tái lập; sửa rubric hoặc nhãn cần một phiên bản calibration mới.

| Case | Judge / người | Ai đúng theo bằng chứng hiện có? | Hành động |
|---|---|---|---|
| H-008 | PASS / FAIL | Người: xưng “em”, dùng “nha” quá suồng sã. | Tách thân thiện khỏi xưng hô phù hợp; thêm ví dụ âm tính này. |
| H-017 | PASS / FAIL | Người theo note: “bạn ơi”, “nha” không phù hợp khách lớn tuổi. | Cung cấp ngữ cảnh người nhận khi chấm; không suy tuổi từ reply riêng lẻ. |
| H-029 | PASS / FAIL | Người: “không cần nhắn thêm” là giọng ra lệnh. | Chấm toàn câu; “Dạ, vui lòng” không tự động làm câu lịch sự. |
| H-042 | FAIL / PASS | Người: trả lời ngắn nhưng đủ ý, không cần xin lỗi mọi lần. | Bỏ yêu cầu xin lỗi bắt buộc cho lời xác nhận đã xử lý. |
| H-051 | FAIL / PASS | Người: thuật ngữ “refund” được phép trong ngữ cảnh này. | Cho phép thuật ngữ nghiệp vụ đã thống nhất, tránh phạt tiếng Anh tự động. |
| H-063 | PASS / FAIL | Người: hứa “sẽ hoàn thêm” ngoài kết quả hệ thống. | Tách tiêu chí không hứa vượt quyền; kiểm tiền bằng code, không giao judge tone. |
| H-070 | PASS / FAIL | Người: emoji cười không phù hợp khiếu nại. | Thêm ví dụ emoji theo ngữ cảnh, không chỉ kiểm từ lịch sự. |
| H-081 | FAIL / PASS | Note công khai nói judge đúng và nhãn người đọc nhầm ticket. | Đưa vào hàng đợi phân xử; giữ số liệu nhãn gốc trong báo cáo, tạo nhãn phiên bản mới sau review. |
| H-088 | FAIL / PASS | Người: lặp “Dạ” do lỗi gõ chưa đủ để coi tone thất bại. | Phân biệt lỗi gõ nhỏ với thiếu tôn trọng. |
| H-094 | PASS / FAIL | Người theo note: tiếng Việt mất dấu, văn phong dịch máy. | Thêm chuẩn chất lượng tiếng Việt; không quy mọi câu không dấu thành sai ngữ nghĩa tiền. |
| HL-015 | PASS / FAIL | Người: reply 55.000, note ledger 40.000. | Đối chiếu ledger bằng `ReplyLedgerConsistent`; lời văn lịch sự không bù tiền sai. |
| HL-016 | PASS / FAIL | Người: reply 55.000, ledger 35.000 dù xin lỗi rất dài. | Rubric helpful phải yêu cầu đúng kết quả trước khi xét độ dài và đồng cảm. |
| HL-020 | PASS / FAIL | Người: reply 90.000, ledger 120.000. | Kiểm tiền bằng code, bổ sung cả thiếu tiền và thừa tiền. |
| HL-028 | PASS / FAIL | Người: reply 50.000, ledger 35.000; xin lỗi lặp lại che lỗi. | Không dùng độ dài làm proxy cho hữu ích. |
| HL-035 | PASS / FAIL | Người: reply 50.000, ledger 35.000. | Thêm cặp câu cùng tone, khác số tiền; helpful không được PASS khi fact sai. |

## Kết luận sử dụng

Tone chỉ đủ điều kiện về calibration; harness hiện không có judge tone online cho từng trial, nên không tuyên bố tone đã tham gia gate release. Helpful bỏ sót 21/30 lỗi, dù precision 1.0: dùng nó để quyết định merge sẽ cho nhiều câu trả lời tiền sai đi qua. Tiền, approval và scope tiếp tục được kiểm bằng code/ledger.

Hai CSV đều công khai và là replay, chưa có held-out người mới. Rubric sửa theo bảng trên phải được hiệu chỉnh lại trên tập mới trước khi áp dụng cho production; không chỉnh nhãn gốc chỉ để nâng κ.

Tái hiện:

```powershell
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

Lệnh tone exit 0; lệnh helpful exit 1 là kết quả mong đợi.
