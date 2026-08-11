# Vale social fixture

Not a real post. Exercises `vale/.vale-social.ini`, where `TamMai.Emoji`
is switched off and every other rule stays on. `selftest.py` asserts the
counts; fixing this file's prose is what breaks the test.

`TamMai.Emoji = NO` is the fragile part: Vale ignores an unrecognised
key silently, so a typo would leave the rule armed. Asserting zero emoji
hits is not enough on its own to prove the switch works — a wholly
broken config scores zero on every rule too. The banned word and the
intensifier below must keep firing in the same run, which is what
separates "emoji suppressed" from "config dead".

<!-- TamMai.Emoji: 0 here, 2 under the doc config -->

We shipped it in three weeks. 🚀

Numbers that moved: 40% fewer timeouts. ✨

<!-- TamMai.BannedWords x1 — slop is worse on LinkedIn, not better -->

We leverage the platform to ship faster.

<!-- TamMaiVI.Intensifiers x1 -->

Tính năng này vô cùng hữu ích cho nhóm.

## Clean control lines

Neither may produce an alert.

Máy chủ chạy Ubuntu 24.04 và cần 8 GB RAM.

The server listens on port 8080 and writes logs to /var/log/app.
