# TODO-083. `ytmidilib` 0.3.0 を取り込み、試聴の一時ファイルを無くす

## きっかけ

`ytmidilib` 0.3.0 で `write()` の第 1 引数が
`str | os.PathLike[str] | BinaryIO` になった（TODO-065 の要求と回答。
挙動と出力バイト列は `0.2.1` から変わらない）。`playable_midi_bytes()`
（`audition.py`）が「一時ディレクトリを作って書いて読み戻して消す」
4 手でやっていたものが、`io.BytesIO` 1 つで済むようになった。

## やったこと

- `uv sync --upgrade-package ytmidilib` で `0.3.0` を取り込んだ
  （`pyproject.toml` の `tag` も `"0.3.0"` に変更）
- `audition.py` の `playable_midi_bytes()` を、
  `tempfile.TemporaryDirectory` 経由の書き出し・読み戻しから
  `io.BytesIO` 1 つに差し替えた。呼ぶ側の戻り値（`bytes`）は変わらない
- docstring から一時ファイルの説明（3 段落目）を削り、
  `io.BytesIO` をそのまま返す旨に直した

## テスト

- `uv run pytest -q` → 297 件すべて成功
- `uv run ruff check src tests` / `uv run mypy src` → 問題なし
- `uv pip show ytmidilib` で `Version: 0.3.0` を確認
  （タグ直後に `0.0.4.dev20+g...` のような版化けが起きる現象は今回は無かった）
