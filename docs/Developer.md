# Developer Guide

lint とテストの実行方法。

## セットアップ

```bash
uv sync                        # 依存関係の取得（dev グループを含む）
uv run playwright install chromium   # ブラウザテストを走らせる場合のみ
```

`uv run` 経由で実行すれば仮想環境の有効化は不要。以降のコマンドはすべて
リポジトリのルートで実行する。

## テスト

テストは 2 系統ある。**ブラウザテストは既定では走らない。**

| コマンド | 対象 | 件数 | 所要 |
|---|---|---|---|
| `uv run pytest` | 通常テスト | 80 | 約 5 秒 |
| `uv run pytest -m browser` | ブラウザテスト | 5 | 約 8 秒 |
| `uv run pytest -m ""` | 両方 | 85 | 約 12 秒 |

`pyproject.toml` の `addopts = "-m 'not browser'"` により、`uv run pytest` は
ブラウザテストを除外する。実 Chromium を起動して桁違いに遅いため。

### 絞り込み

```bash
uv run pytest tests/test_conf.py                    # ファイル単位
uv run pytest tests/test_conf.py::TestValidateConfig # クラス単位
uv run pytest tests/test_conf.py::TestValidateConfig::test_invalid_type
uv run pytest -k "validate"                          # 名前で絞る
uv run pytest -x                                     # 最初の失敗で止める
uv run pytest -q --collect-only                      # 実行せず一覧だけ
```

### カバレッジ

```bash
uv run pytest --cov=ytstreetorgan --cov-report=term-missing -m ""
```

`-m ""` を付けないとブラウザテストが除外され、Web 層のカバレッジが落ちる。

### ブラウザテスト

`tests/browser/` に Playwright で書いてある。`conftest.py` の `live_server`
fixture が実サーバーを空きポートで起動する。

```bash
uv run pytest -m browser                    # 全部
uv run pytest -m browser --headed           # ブラウザを表示して実行
uv run pytest -m browser --slowmo 500       # 各操作を 0.5 秒遅延（目視確認用）
uv run pytest -m browser --tracing on       # トレースを記録（失敗調査用）
```

失敗を調べるときは `--headed --slowmo 500` が手っ取り早い。

## lint と型チェック

```bash
uv run ruff check src tests          # lint
uv run ruff check --fix src tests    # 自動修正（安全なものだけ）
uv run mypy src                      # 型チェック
uv run basedpyright src              # 型チェック（standard モード）
```

`mypy` / `basedpyright` の対象は `src` のみ。`tests` は `py.typed` マーカーが
無いことによる指摘が出るため対象外にしている。

### ruff の設定方針

有効にしているルール（`pyproject.toml` の `[tool.ruff.lint]`）:

```
E4, E5, E7, E9  pycodestyle（import, 行長, 文, 実行時エラー）
F               pyflakes（未使用 import、未定義名など）
I               import の並び順
UP              新しい文法への置き換え
B               bugbear（可変デフォルト引数などの罠）
W               空白まわり
PTH             os.path ではなく pathlib を使う
```

`line-length = 88`。ruff のデフォルト（`E4,E7,E9,F`）は未使用 import 程度しか
拾わず、`B006`（可変デフォルト引数）のような実害のあるものを取りこぼすため広げてある。

除外は `[tool.ruff.lint.per-file-ignores]` に理由付きで書いてある。
**新しく除外を足すときは理由をコメントで残すこと。**

### unsafe fix について

`ruff check --fix` は安全な修正のみ適用する。`--unsafe-fixes` を付けると
`%` 書式の f-string 化などもまとめて直せるが、**型注釈を壊すことがある**。

過去に `B006` の unsafe fix が `channel: list = []` を
`channel: list = None`（`| None` なし）に書き換え、型チェックが落ちた実績がある。
`--unsafe-fixes` を使ったら必ず `mypy` と `basedpyright` を通すこと。

## 一括で回す

コミット前はこれを通す。

```bash
uv run ruff check src tests && \
uv run mypy src && \
uv run basedpyright src && \
uv run pytest -m ""
```

## テストを書くときの注意

### 利用者の実設定を壊さないこと

`WebServer` と `ConfigHandler` は `Conf()` を**引数なしで**生成する。
`Conf` は `.` → `~/.config` → `~/etc` → … の順に `storgan-conf.json` を探すため、
何もしないとテストが `~/etc/storgan-conf.json`（利用者の実設定）を読み書きする。

`tests/conftest.py` の `isolate_user_config`（autouse, session スコープ）が
`Conf.SEARCH_PATH` を一時ディレクトリに差し替えて防いでいる。**このフィクスチャは
消さないこと。** 実際にテストが実設定を書き換えていた時期がある。

### ブラウザテストは必ず最後に走る

`pytest-playwright` の fixture はメインスレッドにイベントループを残す。
先に実行すると、後続の tornado `AsyncHTTPTestCase` が
`Cannot run the event loop while another loop is running` で落ちる。

`tests/conftest.py` の `pytest_collection_modifyitems` が `browser` マーカーの
テストを末尾に並べ替えて回避している。順序に依存する仕組みなので、
`-p no:randomly` 相当の並べ替えを入れる場合は注意。

### URL prefix を直書きしないこと

テストは既定値（`/storgan2`）ではなく `/storgan-test` で走る
（`tests/conftest.py` の `TEST_URL_PREFIX`）。テンプレートや JS が prefix を
直書きしていると `tests/browser/test_rollbook_page.py::test_static_assets_load`
が 404 を検出して落ちる。テンプレートでは `{{urlprefix}}`、JS では
`window.URL_PREFIX` を使う。
