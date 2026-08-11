# Vale fixture

Not documentation. Every violation below is planted, and `selftest.py`
asserts the exact per-rule counts. Do not "clean up" this file — fixing
its prose is what breaks the test.

Each rule's expected hits are noted in the comment above its block.

<!-- TamMai.BannedWords x2, TamMai.Emoji x1 -->

We leverage the platform to seamlessly ship features. 🚀

<!-- TamMai.Fillers x2, TamMai.Substitutions x1 -->

It's worth noting that you should utilize the API.

It is worth noting that the uncontracted form must fire too.

<!-- TamMaiVI.Fillers: line-start "Việc" -->

Việc cấu hình rất đơn giản.

<!-- TamMaiVI.Fillers: bullet-start "Việc" -->

- Việc triển khai mất hai ngày.

<!-- TamMaiVI.Fillers: "nhằm mục đích" -->

Chúng tôi làm điều này nhằm mục đích giảm chi phí.

<!-- TamMaiVI.Fillers: "một cách dễ dàng" -->

Bạn có thể cài đặt một cách dễ dàng.

<!-- TamMaiVI.Intensifiers: "vô cùng" mid-sentence -->

Tính năng này vô cùng hữu ích cho nhóm.

<!-- TamMaiVI.Fillers: "đóng vai trò quan trọng" -->

Cache đóng vai trò quan trọng trong hệ thống.

## Clean control lines

Neither line below may produce an alert. They guard against false
positives on ordinary Vietnamese and English technical prose.

Máy chủ chạy Ubuntu 24.04 và cần 8 GB RAM.

The server listens on port 8080 and writes logs to /var/log/app.

## Code scoping control

Vale's default markdown scoping skips these; no alert may come from
either. This is what makes BlockIgnores/TokenIgnores unnecessary.

Inline: `leverage --seamlessly --robust`

```
We leverage a robust utilize thing. 🚀
Việc này nhằm mục đích test.
```
