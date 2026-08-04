# E. URL prefix の扱いを整理

テストの `/storgan2` 直書き 12 箇所を排除し、テスト全体を既定値以外の
prefix（`/storgan-test`）で動かすようにした。テンプレートや JS が prefix を
直書きすると `test_static_assets_load` が落ちる（実際に壊して検証済み）。

**併せて発覚した問題を修正**: `test_config_handler` の add/delete テストが
`~/etc/storgan-conf.json`（利用者の実設定）を書き換えていた。
`tests/conftest.py` の autouse fixture で `Conf.SEARCH_PATH` を一時ディレクトリに
差し替え、全テストから実設定を隔離した。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
