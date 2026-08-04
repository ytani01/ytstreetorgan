# テストを書くときの注意

`tests/` 配下を触るときだけ読み込まれる（ルートの `CLAUDE.md` は常時読み込み）。

## ブラウザテスト

`tests/browser/` に Playwright で書いてある。`conftest.py` の `live_server`
fixture が実サーバーを空きポートで起動する。

**`tests/conftest.py` の `isolate_user_config` は消さないこと。** `WebServer` と
`ConfigHandler` は `Conf()` を引数なしで生成するため、これが無いとテストが
`~/etc/storgan-conf.json`（利用者の実設定）を書き換える。実際に書き換えていた。
（この禁止事項はルートの `CLAUDE.md` にも書いてある。）

## HTTP テスト

`tests/webapp_base.py` の `WebAppTestCase` を継承する。**`webroot` を
テストごとに一時ディレクトリへ複製する**ので、リポジトリの `webroot/` は
汚れない（アップロードや削除を試すため。実際に汚していた）。

- 置き場に何か置きたいときは `setup_files()` を上書きする
- `PORT` と `SERVER_KWARGS`（`debug` / `size_limit`）は subclass が決める
- 後片付けは `addCleanup` 任せ。`tearDown` を書かない
