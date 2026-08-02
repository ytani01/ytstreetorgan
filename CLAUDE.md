# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

MIDI ファイルを解析し、手回しオルガン用ロールブック（穴あけ用の紙の楽譜）を SVG で生成する。
CLI とブラウザ UI の 2 系統がある。

## コマンド

`uv` 管理。`uv sync` 後、すべて `uv run` 経由で実行する。

```bash
uv run pytest -q                          # 通常テスト（browser マーカーは除外される）
uv run pytest -m browser -q               # ブラウザテスト（実 Chromium を起動、要 playwright install）
uv run pytest tests/test_conf.py -q       # ファイル単位
uv run pytest tests/test_conf.py::TestValidateConfig::test_invalid_type   # 単体テスト
uv run pytest --cov=ytstreetorgan --cov-report=term-missing -m ""         # カバレッジ

uv run ruff check src tests               # lint（--fix で自動修正）
uv run mypy src                           # 型チェック
uv run basedpyright src                   # 型チェック（standard モード）

uv run ytstreetorgan webapp -p 10081      # Web サーバー起動 → http://localhost:10081/storgan2/
uv run ytstreetorgan rollbook FILE.mid -m 34notes   # SVG 生成
uv run ytstreetorgan parse FILE.mid -v    # MIDI 解析結果を表示（-v で可視化）
uv run ytstreetorgan play FILE.mid        # MIDI 再生
```

絞り込み、カバレッジ、ruff の設定方針、テストを書くときの注意は
`docs/Developer.md` にまとめてある。

`ytmidilib` は git 依存（`pyproject.toml` の `[tool.uv.sources]`）。上流を変更したら `uv sync --upgrade-package ytmidilib`。

バージョンは hatch-vcs が git タグから生成する。未インストールのチェックアウトで直接実行すると `__version__` が `0.0.0` になる。

## アーキテクチャ

### レイヤー分離（意図的な規約）

`__main__.py` は click のコマンド定義だけを持つ薄い層に保つ。ロジックは `apps.py` の
`RollBookApp` / `MidiApp` に置く（テスト可能にするため）。新しいサブコマンドを追加する場合も
この分離を守ること。共通オプション（`-h` / `-d` / `-V`）は `click_utils.py` の
`click_common_opts()` デコレータで付与する。

### 設定ファイル（リポジトリ外にある）

モデル設定は `storgan-conf.json`。**リポジトリには含まれていない**。`Conf` が
`.` → `~/.config` → `~/etc` → `/usr/local/etc` → `/etc` の順に探索し、最初に見つかったものを使う。
実運用の設定は `~/etc/storgan-conf.json` に置いてある。`conf/storgan.conf-dist` がテンプレート。
見つからないと `Conf.__init__` が `FileNotFoundError` を投げるので、設定に触るテストは
必ずパスを明示するかモックする。

`ModelConf` の**キーは生の JSON フィールド名**で、空白や数字始まりを含む
（`'book height'`, `'hole height'`, `'note offset'`, `'1sec'`）。Python の識別子ではないので
`conf['book height']` のように添字でアクセスする。`Conf.save()` は `.bak` を作ってから
一時ファイル経由で原子的に置換する。

### SVG 座標系

**すべての座標が負値**（`svg_square()` は `M {-x},{-y} h {-w} v {-h}`、viewBox の原点も負）。
ロールブックは右から左へ流れるため。単位は mm で、`'1sec'`（既定 50.0）が秒→mm の変換係数。
線は `vector-effect:non-scaling-stroke` + `-inkscape-stroke:hairline` を付ける
（カッティング用にヘアラインが要る）。

### 穴の扱い

- `note2scale()` はオルガンの音階に無い MIDI ノートに対して `-1` を返す。そうした音は
  **捨てずに黒の破線で描く**（`RollBook.svg()`）。演奏者が欠落を目視できるようにするため。
  scale が `-1` の穴はブックの全長（`_width`）を伸ばさない。
- 穴の長さが `'bridge threshold'` を超えると `divide_length_by_max_len()` が
  `'bridge width'` の隙間（ブリッジ）を挟んで複数に分割する。紙のブックが切れないようにする措置。
  導出は `docs/memo-divide.md` にある。

### Web 層

Tornado。URL プレフィックスは `/storgan2`（`WebServer.URL_PREFIX`）。全ハンドラは
`StorganBaseHandler` を継承し、設定を `app.settings` から取り出す。
`_url_path` の**末尾のスラッシュは必須**（`Handler1.get()` がこれと突き合わせてリダイレクトする）。

- `Handler1` — MIDI アップロード → SVG 生成 → プレビュー
- `Download` — `webroot/svg/` からのダウンロード
- `ConfigHandler` — `/storgan2/config` のモデル設定エディタ。`?api=1` で JSON を返す

`webroot` / `workdir` は `WebServer` が `Path` に正規化し、`app.settings` にも
`Path` のまま渡す。各ハンドラは `self._webroot / 'svg' / fname` のように組み立てる。

`webroot/midi/` と `webroot/svg/` は実行時に書き込まれる作業ディレクトリ（`.gitignore` 済み）。

テンプレート内で URL を組み立てるときは、必ず `{{urlprefix}}` を使う（JS からは
`window.URL_PREFIX`）。直書きすると prefix を変えたときに 404 になる。
テストは既定値以外の prefix で走らせているので、直書きすると
`tests/browser/test_rollbook_page.py::test_static_assets_load` が落ちる。

静的ファイル（CSS / JS / favicon）は `{{ static_url('css/my.css') }}` を使う。
prefix が付くうえに `?v=<hash>` が付くので、更新したときに古いキャッシュを
掴まれない。

`autoreload=True` **だけでは `.py` しか反映されない**（テンプレートは
`compiled_template_cache`、`?v=<hash>` は `static_hash_cache` が握っている）。
かつて再起動せずに「直したのに変わらない」と悩んだ実績が二度あるので、
`WebServer` はこの 2 つも `False` にしてある。**再起動は不要**。
消すと元の落とし穴に戻る。

### フロントエンド

Pico.css v2.1.1 を `webroot/static/css/pico.min.css` に**同梱**している。
CDN は 1 本も読まない（ローカルで動かす道具なので、ネットに繋がっていなくても
レイアウトが崩れないこと）。jQuery / Bootstrap / Font Awesome への依存も無く、
アイコンはインライン SVG、フォントはシステムフォント。

`webroot/static/css/my.css` の**トークンは `:root:root` で定義している**。
Pico が配色を `:root:not([data-theme=dark])`（詳細度 (0,2,0)）で書いているため、
素の `:root` では後から読み込んでも負ける。実際に負けて Pico 既定の水色のままに
なっていた。同じ理由で、**Pico はボタン要素の中で `--pico-color` を上書きする**
ので、自前のコントロールの色は `--hole` のような独自トークンから直接指定する。

モーダルは `<dialog>` +`showModal()`（Pico が素で面倒を見る）。

### ロールブックのビューア

`storgan.js` の後半。**transform で拡縮していない。SVG の描画サイズ
（`.svgbox > svg` の `height: calc(var(--book-h) * var(--z))`）そのものを変える。**
こうするとブラウザ標準のスクロールがそのまま効き、スクロールバーが全体の中の
現在位置を示す。SVG が mm 単位で出力されているので倍率 1.0 が原寸になる。
汎用の panzoom ライブラリは transform ベースで、縦横比 33:1 のロールブックでは
スクロールバーが消えて現在位置を見失うので使わない。

- **初期表示は右端**（`viewBox` が負で、曲の先頭が x=0 側 = 右端にあるため）。
  既定の倍率は「高さ合わせ」。「全体」だと 7% になって何も読めない
- ブックの寸法は `RollBook` の `width` / `height` / `hole_count` / `mm_per_sec`
  から取る。**SVG 文字列からは取り出せない**ので `Handler1._render()` が
  `book` として別に渡し、テンプレートが `window.BOOK_DATA` に出している

### ブラウザテスト

`tests/browser/` に Playwright で書いてある。`conftest.py` の `live_server`
fixture が実サーバーを空きポートで起動する。

**`tests/conftest.py` の `isolate_user_config` は消さないこと。** `WebServer` と
`ConfigHandler` は `Conf()` を引数なしで生成するため、これが無いとテストが
`~/etc/storgan-conf.json`（利用者の実設定）を書き換える。実際に書き換えていた。

### ロギング

loguru を `mylog.py` 経由で使う。各 CLI コマンドの先頭で `loggerInit(debug)` を呼び、
他のモジュールでは `from loguru import logger` でグローバル logger を使うだけ。
例外は `exmsg(e)` で整形する。標準 `logging` は使わない。

## 注意

- `RollBookApp` は `-o` 未指定のとき `~/Desktop/<MIDIファイル名>.svg` に出力する
  （`apps.py` の `DEF_OUT_DIR`）。`-o` を指定した場合はそのパスをそのまま使う。
- `archives/` は過去の計画書を記録として残しているだけで、**現行仕様ではない**。
  実装の根拠として参照しないこと。
