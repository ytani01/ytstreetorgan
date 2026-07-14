# Plan: my_logger.py → mylog.py (loguru) 移行

## 概要
Python 標準 `logging` モジュールを使った `my_logger.py` の `get_logger()` を、
loguru ベースの `mylog.py` に移行し、`my_logger.py` を削除する。

---

## Phase 1: テスト作成と移行実施

### Task 1.1: テスト基盤の作成
- [x] `tests/` ディレクトリを作成
- [x] `tests/conftest.py` を作成（共通フィクスチャ）
- [x] `tests/test_mylog.py` を作成（`mylog.py` の動作確認テスト）

### Task 1.2: `rollbook.py` の移行
- [~] `rollbook.py` から `from .my_logger import get_logger` を削除
- [~] `from loguru import logger` に置き換え
- [~] `self._log = get_logger(...)` のパターンをすべて `logger` 直接使用に置き換え
- [~] テスト実行で動作確認

### Task 1.3: `handler1.py` の移行
- [ ] `handler1.py` から `from .my_logger import get_logger` を削除
- [ ] `from loguru import logger` に置き換え
- [ ] `self._mylog = get_logger(...)` のパターンをすべて `logger` 直接使用に置き換え
- [ ] テスト実行で動作確認

### Task 1.4: `webapp.py` の移行
- [ ] `webapp.py` から `from .my_logger import get_logger` を削除
- [ ] `from loguru import logger` に置き換え
- [ ] `self._log = get_logger(...)` のパターンをすべて `logger` 直接使用に置き換え
- [ ] テスト実行で動作確認

### Task 1.5: `__main__.py` の移行
- [ ] `__main__.py` から `from .my_logger import get_logger` を削除
- [ ] `from loguru import logger` に置き換え
- [ ] `log = get_logger(...)` のパターンをすべて `logger` 直接使用に置き換え
- [ ] 各 CLI コマンド関数で `loggerInit(debug)` が呼ばれていることを確認（既存の呼び出しを活用）
- [ ] テスト実行で動作確認

### Task 1.6: `my_logger.py` の削除
- [ ] `my_logger.py` への参照がすべてなくなったことを確認
- [ ] `my_logger.py` を削除
- [ ] テスト実行で動作確認

---

## Phase 2: 品質確認

### Task 2.1: 全テスト実行・カバレッジ確認
- [ ] `CI=true uv run pytest --cov=ytstreetorgan --cov-report=term-missing` 実行
- [ ] カバレッジ >80% を確認

### Task 2.2: 型チェック・Lint
- [ ] `uv run ruff check src/` 実行
- [ ] `uv run mypy src/` または `uv run basedpyright src/` 実行
