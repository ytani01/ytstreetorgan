# テストを書くときの注意

`tests/` 配下を触るときだけ読み込まれる（ルートの `CLAUDE.md` は常時読み込み）。

**守ること 3 つ。** 使い方の詳細と、ブラウザテストの走らせ方は
`docs/Developer.md`「テストを書くときの注意」にある。

1. **`tests/conftest.py` の `isolate_user_config` は消さないこと。**
   `WebServer` と `ConfigHandler` は `Conf()` を引数なしで生成するため、
   これが無いとテストが `~/etc/storgan-conf.json`（利用者の実設定）を
   書き換える。実際に書き換えていた
   （この禁止事項はルートの `CLAUDE.md` にも書いてある）
2. **HTTP テストは `tests/webapp_base.py` の `WebAppTestCase` を継承する。**
   実物の `webroot/` を渡すと、アップロードや削除がそこに書かれる
   （複製を使えば汚れない。実際に汚していた）
3. **ブラウザテストのアップロードは `tests/browser/conftest.py` の
   `upload_midi()` を使う。** 生成結果を待たずに次へ進むと、書き終える
   前に履歴を読みにいって落ちる
