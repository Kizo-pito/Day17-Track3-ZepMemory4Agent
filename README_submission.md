# Lab 17 Submission

## Ket qua va phan tich benchmark

Student memory dat **11/11 PASS (100%)**, trong khi no-memory dat **2/11 (18,2%)**. Khong co layer nao co hit rate thap nhat rieng: short-term, long-term, episodic, semantic va mixed deu dat 100%. Query retrieve nhieu token nhat la **E02** voi 910 token; E08 dung sau voi 885 token.

E07 can ket hop long-term va semantic memory: long-term cung cap preference **Python** cua Minh, con semantic graph cung cap quy tac retry **Idempotency-Key**. Budget manager trim tung layer theo 10/4/3/3 va uu tien short-term -> long-term -> episodic -> semantic.

Memory-enabled giam trung binh 23,8% token so voi full source context. No-memory giam 81,8% nhung chi pass 18,2% vi retrieval rong: token reduction cao khong co y nghia neu evidence hit rate thap.

## Cau hoi thuc hanh

Trong bo test nay, **long-term memory** quan trong nhat vi truc tiep quyet dinh bon case E02, E03, E08, E09 va dong gop cho E07. Zep Context Block tu dong tong hop facts, episodes va recency qua session, doi lai phu thuoc dich vu managed, latency va chi phi. Redis nhanh, ro TTL/KV; Qdrant linh hoat cho vector retrieval, nhung phai tu quan ly ingestion, metadata, conflict, provenance, isolation va compaction.

Guardrail chong memory poisoning: chi ingest khi user da opt-in; redact PII; tach namespace theo `user_id`; chi cho schema/provenance hop le vao durable memory; khong bien noi dung retrieved thanh instruction; danh dau do tin cay, freshness va contradiction; gioi han quyen heartbeat; cho phep audit/delete/verify.

E08 the hien recency theo scope: Python van dung cho demo ORCHID-27, nhung cap nhat moi bat buoc TypeScript + NestJS cho BLUEBIRD-42. E10 cho thay compaction van giu durable constraint `REVIEW-DEADLINE-1600`, Friday 16:00 sau khi cac raw turn cu bi evict; buffer don thuan se tang token va cuoi cung mat constraint khi cat lich su.
