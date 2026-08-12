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

| コマンド | 対象 | 件数 | 所要（手元での目安） |
|---|---|---|---|
| `uv run pytest` | 通常テスト | 163 | 約 25 秒 |
| `uv run pytest -m browser` | ブラウザテスト | 35 | 約 20 秒 |
| `uv run pytest -m ""` | 両方 | 198 | 約 45 秒 |

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
uv run pytest -m browser                                # 全部（ヘッドレス）
PWDEBUG=1 uv run pytest -m browser tests/browser/test_config_editor.py::test_save_persists_edited_value
uv run pytest -m browser --headed --slowmo 1000         # 動きを目で追う
uv run pytest -m browser --tracing on                   # トレースを記録
```

**`--headed` だけではブラウザがほぼ見えない。** テスト 1 本が 2〜3 秒で終わるため、
ウィンドウが一瞬で開いて閉じる。ブラウザは実際に起動しているので、見たい場合は
下のいずれかを使う。

- **`PWDEBUG=1`（おすすめ）** — Playwright Inspector が開き、**1 ステップずつ停止**する。
  セレクタの確認や DOM の調査ができる。タイムアウトも無効化されるので、
  じっくり見るならこれ。テストは 1 本に絞って実行すること。
- **`--headed --slowmo 1000`** — 各操作の間に 1 秒待つ。通しの動きを眺めたいとき向け。
- **`--tracing on`** — 実行後に `test-results/` へトレースが残る。
  `uv run playwright show-trace <trace.zip>` でタイムライン・スクリーンショット・
  DOM スナップショットを後から確認できる。あとから落ちた原因を追うとき向け。

失敗の原因がセレクタなら `PWDEBUG=1`、タイミングなら `--tracing on` が早い。

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

## タグを打つ

版は **hatch-vcs が git タグから作る**ので、タグを打つこと自体が版を上げる
操作になる（`docs/tech-stack.md`）。`v` は付けず、注釈付きタグにする
（過去のタグはすべてこの形で、`develop` の上にある）。

```bash
git tag -a 0.6.1 -m "..."               # メッセージはそのコミットのものを使う
uv sync --reinstall-package ytstreetorgan   # ← これを省かない
```

**`uv sync --reinstall-package ytstreetorgan` を必ず通すこと。** タグを
打っただけでは `.venv` の中は古い版のままで、`uv run ytstreetorgan --version`
も画面のフッターも古い版を出し続ける。`uv` は「もう入っている」と見なして
入れ直さないので、`uv sync` や `uv run` を素で叩いても直らない。

- **`uv.lock` は変わらない。** `ytstreetorgan` の項目は
  `source = { editable = "." }` だけで `version` 行を持たない（動的な版
  なので lock に書かれない）。タグを打っても `git status` はきれいなまま
- `--reinstall-package` は**インストールの段階にだけ効く**。依存の解決や
  lock の更新には関係しない
- `uv pip install -e .` でも版は直る（`[tool.uv.sources]` も読まれるので
  `ytmidilib` を git から取ってくる）。ただし **`uv.lock` を経由せずに
  その場で解決し直す**うえ、dev 依存が入らない。使わない

## テストを書くときの注意

### 中身のある MIDI は `tests/data/` のものを使うこと

`tests/conftest.py` の `SAMPLE_MIDI` / `LONG_MIDI` / `IN_SCALE_MIDI` から
引く。**`webroot/midi/` から読まないこと。** あちらは実行時の作業用で
`.gitignore` 済みなので、クローン直後は落ちるか、存在を確かめる書き方に
していると**何も検証しないまま「成功」と表示される**（TODO-081）。

`tests/data/*.mid` は `tests/data/make_midi.py` が mido で合成したもので、
リポジトリで追跡している。どの MIDI が何を試すためのものかは、その
docstring にある。作り直すのは次のとおり（中身は変わらない）。

```bash
uv run python tests/data/make_midi.py
```

**音を変えると期待値が動く。** テストは「この機種では破線が出る」
「`bridge_threshold` を小さくすると分割後の穴が 2 倍以上になる」といった
性質に依っているので、変えたら `pytest` を通して確かめること。

### HTTP テストは `WebAppTestCase` を継承すること

`tests/webapp_base.py` の `WebAppTestCase` が、**`webroot` をテストごとに
一時ディレクトリへ複製する**。アップロードや削除を試すので、実物の
`webroot/` を渡すと `webroot/midi/` と `webroot/svg/` に書き込まれ、
途中で落ちれば消し残る（実際そうなっていた）。

- 置き場に何か置きたいときは `setup_files()` を上書きする
- `PORT` と `SERVER_KWARGS`（`debug` / `size_limit`）は subclass が決める
- 後片付けは `addCleanup` 任せ。`tearDown` は書かない
- 送る MIDI の中身は `tests/data/` から読む（複製先は空で始まるため）

### ブラウザテストのアップロードは `upload_midi()` を使うこと

`tests/browser/conftest.py` にある。ページを開き、ファイルを選び、
同名ダイアログが出たら答え、**生成結果が出るまで待つ**。

待たずに次へ進むと、サーバーが書き終える前に履歴を読みにいって落ちる。
送信そのものが止まる場合（上限超えなど）は `wait_result=False` で呼ぶ。

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
