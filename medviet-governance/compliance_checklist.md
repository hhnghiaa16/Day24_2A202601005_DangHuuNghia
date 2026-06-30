# Checklist tuân thủ Nghị định 13/2023 - Nền tảng MedViet AI

## A. Lưu trữ dữ liệu tại Việt Nam

- [x] Dữ liệu bệnh nhân được thiết kế để lưu trên hạ tầng đặt tại Việt Nam.
- [x] Dữ liệu sao lưu phải nằm trong vùng lưu trữ tại Việt Nam hoặc vùng được phê duyệt cho dữ liệu cá nhân của người dùng Việt Nam.
- [x] Mọi luồng chuyển dữ liệu ra ngoài Việt Nam phải được ghi log và bị chặn bằng chính sách OPA nếu dữ liệu có phân loại `restricted`.

## B. Đồng ý rõ ràng của người dùng

- [x] Hệ thống phải thu thập đồng ý trước khi dùng dữ liệu bệnh nhân cho huấn luyện hoặc đánh giá mô hình AI.
- [x] Hệ thống phải hỗ trợ rút lại đồng ý và yêu cầu xóa dữ liệu theo quyền được xóa.
- [x] Bản ghi đồng ý phải có mã bệnh nhân, mục đích xử lý, thời điểm đồng ý và phiên bản điều khoản đồng ý.

## C. Thông báo vi phạm dữ liệu trong 72 giờ

- [x] Có kế hoạch ứng phó sự cố: phân loại sự cố, cô lập hệ thống bị ảnh hưởng, bảo toàn bằng chứng và thông báo cho DPO.
- [x] Có cảnh báo tự động khi phát hiện truy cập bất thường, nhiều lần bị từ chối quyền hoặc nhiều yêu cầu vào dữ liệu PII thô.
- [x] Quy trình thông báo phải hỗ trợ báo cáo tới cơ quan có thẩm quyền trong vòng 72 giờ kể từ khi phát hiện vi phạm.

## D. Bổ nhiệm cán bộ bảo vệ dữ liệu

- [x] Đã chỉ định Data Protection Officer (DPO).
- [x] Thông tin liên hệ DPO: `dpo@medviet.example`.

## E. Kiểm soát kỹ thuật đã triển khai

| Yêu cầu ND13 | Kiểm soát kỹ thuật | Trạng thái | Phụ trách |
| --- | --- | --- | --- |
| Giảm thiểu dữ liệu | Nhận diện và ẩn danh PII bằng Presidio với recognizer tùy chỉnh cho CCCD, số điện thoại, email và tên tiếng Việt | Hoàn thành | Nhóm AI |
| Kiểm soát truy cập | RBAC bằng Casbin và chính sách truy cập dữ liệu bằng OPA | Hoàn thành | Nhóm nền tảng |
| Mã hóa dữ liệu | Envelope encryption bằng AES-256-GCM cho dữ liệu nhạy cảm trên môi trường local | Hoàn thành | Nhóm hạ tầng |
| Chất lượng dữ liệu | Kiểm tra `patient_id`, khoảng kết quả xét nghiệm, danh sách bệnh hợp lệ, số dòng và rò rỉ PII sau ẩn danh | Hoàn thành | Nhóm dữ liệu |
| Audit logging | Ghi log người dùng, vai trò, tài nguyên, hành động, thời điểm, quyết định cấp quyền và mã trạng thái cho API được bảo vệ | Dự kiến triển khai production | Nhóm nền tảng |
| Phát hiện vi phạm | Cảnh báo Prometheus/Grafana khi có nhiều lỗi 401/403, truy cập PII thô bất thường hoặc hành vi export dữ liệu | Dự kiến triển khai production | Nhóm bảo mật |

## F. Chính sách truy cập dữ liệu

| Vai trò | Quyền được phép | Quyền bị chặn |
| --- | --- | --- |
| `admin` | Đọc dữ liệu thô, dữ liệu đã ẩn danh, thống kê tổng hợp và xóa dữ liệu khi cần | Không áp dụng trong phạm vi bài lab |
| `ml_engineer` | Đọc/ghi `training_data`, `model_artifacts`; đọc dữ liệu đã ẩn danh | Không được xóa `production_data`; không được đọc dữ liệu PII thô |
| `data_analyst` | Đọc `aggregated_metrics`; ghi `reports` | Không được đọc dữ liệu PII thô |
| `intern` | Đọc/ghi `sandbox_data` | Không được truy cập dữ liệu production |

## G. Kết quả kiểm tra và báo cáo

| Hạng mục | File báo cáo | Kết quả |
| --- | --- | --- |
| Unit test PII và ẩn danh | `reports/test_results.txt` | Đã chạy trong thư mục `medviet-governance`; 6 test pass |
| Static security scan | `reports/bandit_report.json` | Bandit không phát hiện lỗi bảo mật trong `src` |
| Secret scan | `reports/trufflehog_report.txt` | Không có secret verified được phát hiện; file output rỗng là kết quả chấp nhận được khi không có finding |
| OPA policy input mẫu | `reports/opa_input_delete.json` | Input kiểm tra trường hợp `ml_engineer` xóa `production_data`; chính sách kỳ vọng trả về `false` |

Lưu ý: thư mục `reports` ở root workspace có một lần chạy nhầm vị trí nên `pytest` không collect test. Bộ báo cáo đúng để nộp nằm trong `medviet-governance/reports`.

## H. Công việc cần làm khi đưa lên production

| Khu vực | Giải pháp production |
| --- | --- |
| Quản lý consent | Lưu bản ghi đồng ý trong bảng append-only; chỉ cho phép dùng dữ liệu huấn luyện khi consent còn hiệu lực |
| Quản lý khóa | Thay `.vault_key` local bằng HSM/KMS; xoay vòng KEK định kỳ; audit mọi thao tác giải mã |
| Audit logging | Gửi quyết định phân quyền và log truy cập API vào hệ thống log bất biến, có retention theo chính sách tuân thủ |
| Ứng phó vi phạm | Thiết lập trực on-call, checklist thu thập bằng chứng, luồng thông báo DPO và mẫu báo cáo 72 giờ |
| Lưu trữ dữ liệu | Giới hạn object storage, database, backup và analytics trong vùng Việt Nam hoặc vùng được phê duyệt |
