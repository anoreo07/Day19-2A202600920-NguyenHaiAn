# Reflection — Lab 19

**Tên:** Nguyen Hai An
**Cohort:** A20
**Path đã chạy:** lite

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

BM25 thắng ở `exact` queries (96.7% vs 88.7% semantic) nhờ khớp chính xác thuật ngữ kỹ thuật verbatim. Semantic và hybrid mạnh ở `mixed` queries nhờ kết hợp cả ngữ nghĩa và từ khóa (hybrid đạt 100.0%). Ở `paraphrase` queries, cả hai giảm điểm do mô hình `bge-small-en` tối ưu tiếng Anh nên recall tiếng Việt yếu.

Không dùng hybrid khi:
1. Yêu cầu độ trễ cực thấp (< 2ms) vì chạy hai retrievers và RRF tăng overhead.
2. Tra cứu mã SKU, ID, tên riêng hoặc thuật ngữ chuyên ngành thuần túy: Dùng pure BM25.
3. Tìm kiếm thuần ngữ nghĩa phi cấu trúc (cảm xúc, đa phương tiện): Dùng pure vector.

---

## Điều ngạc nhiên nhất khi làm lab này

Sự kết hợp đơn giản qua Reciprocal Rank Fusion (RRF) giúp hybrid đạt độ chính xác 100% đối với các truy vấn hỗn hợp (mixed) và có hiệu năng trung bình cao nhất.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với:
