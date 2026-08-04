# Tech Stack

`pyproject.toml` が正。ここはその要約と、なぜそれを選んでいるかの覚え書き。

## 言語・ランタイム

- Python >= 3.13
- パッケージ管理: `uv`（すべて `uv run` 経由で実行する）
- バージョンは **hatch-vcs が git タグから生成**する（ビルドは hatchling）。
  **未インストールのチェックアウトで直接実行すると `__version__` が
  `0.0.0` になる**（画面のフッターにもそう出る）

## 主要ライブラリ

| ライブラリ | 用途 |
|---|---|
| **click** | CLI |
| **tornado** | Web サーバー（テンプレートも tornado のもの） |
| **ytmidilib** | MIDI の解析と再生。**git 依存**（`[tool.uv.sources]`） |
| **pygame-ce** | MIDI 再生の実体（ytmidilib が使う） |
| **loguru** >= 0.7.3 | ログ。標準 `logging` は使わない |

上流の `ytmidilib` を直したら `uv sync --upgrade-package ytmidilib`。

## フロントエンド

**外部 CDN は 1 本も読まない。** ローカルで動かす道具なので、ネットに
繋がっていなくてもレイアウトが崩れないこと。

- **Pico.css v2.1.1** を `webroot/static/css/pico.min.css` に同梱
- jQuery / Bootstrap / アイコンフォントへの依存は無い。**アイコンは
  インライン SVG**、フォントはシステムフォント
- ビルド工程は無い。`webroot/static/js/*.js` を素の JS で書いて、
  テンプレートから `static_url()` で読む

詳しくは `webroot/CLAUDE.md`。

## ロギング設計

- **入口**: `mylog.py`（loguru の薄い包み）
- **初期化**: 各 CLI コマンドの先頭で `loggerInit(debug)` を 1 度だけ呼ぶ
- **各モジュール**: `from loguru import logger` でグローバル logger を使う
- **書式**: `logger.debug('x={}', x)` の形にする（f-string にしない。
  レベルで抑止されるときに整形しなくて済む）
- **例外**: `exmsg(e)` で 1 行に整形する

## 開発ツール

| ツール | 用途 |
|---|---|
| **pytest** / **pytest-cov** | テストとカバレッジ |
| **pytest-playwright** | ブラウザテスト（`-m browser`。実 Chromium を起動する） |
| **ruff** | lint と import の並べ替え（flake8 は使っていない） |
| **mypy** / **basedpyright** | 型チェック（対象は `src` のみ） |

実行方法は `docs/Developer.md`。
