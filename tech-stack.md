# Tech Stack

## 言語・ランタイム
- Python >= 3.13
- パッケージ管理: `uv`

## 主要ライブラリ
- **click**: CLI インターフェース
- **tornado**: Web サーバー
- **pygame-ce**: MIDI 再生
- **ytmidilib**: MIDI パース・再生 (git依存)
- **loguru >= 0.7.3**: ログ管理（標準 `logging` モジュールの代替）

## ロギング設計
- **使用モジュール**: `mylog.py`（loguru ベース）
- **初期化**: エントリポイント（`__main__.py` の各 CLI コマンド）で `loggerInit(debug)` を呼び出す
- **各モジュールでの使用**: `from loguru import logger` でグローバル logger を使用
- **ログレベル**: `logLevel(debug)` で `DEBUG` / `INFO` を切り替え
- **廃止予定**: `my_logger.py`（Python 標準 `logging` ベース）は削除予定

## 開発ツール
- **テスト**: pytest, pytest-cov
- **型チェック**: basedpyright, mypy
- **Lint**: ruff, flake8
