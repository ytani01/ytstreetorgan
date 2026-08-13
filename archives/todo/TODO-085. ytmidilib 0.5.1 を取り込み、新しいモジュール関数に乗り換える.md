# TODO-085. `ytmidilib` 0.5.1 を取り込み、新しいモジュール関数に乗り換える

## きっかけ

`ytmidilib` が 0.3.0 → 0.5.1 に上がった。向こうの TODO-016 で
`Parser` のメソッドがモジュールレベルの関数（`parse()` / `mk_visual()` /
`print_visual()` / `mk_event_list()`）へ切り出され、可視化は
`midi_visual.py` に独立した。`Parser` は関数を呼ぶだけのクラスとして
互換のために残っているが、状態を持たない。

破壊的変更は無かった。`NoteInfo` が dataclass 化され
（`__post_init__` で時刻を小数第 3 位に丸める、`==` が内容比較、
ハッシュ不可）、`DEFAULT_TEMPO` などの定数と `__version__` が公開された。

## やったこと

- `pyproject.toml` の `tag` を `"0.3.0"` → `"0.5.1"` にし、
  `uv sync --upgrade-package ytmidilib` で取り込んだ
- `apps.py` の `self._parser`（`Parser()`）を無くし、
  `parse()` / `mk_visual()` / `print_visual()` をモジュール関数として
  直接呼ぶように変更した
- `rollbook.py` の `self._midi_parser`（`Parser()`）を無くし、
  `parse()` を直接呼ぶように変更した
- `docs/tech-stack.md` の `ytmidilib` の記述を更新した
  （タグの版、`Parser(debug=)` → `parse(debug=)`、モジュール関数への
  切り出しの経緯を追記）
- `tests/test_main.py` / `tests/test_rollbook.py` の
  `@patch('...Parser')` を `@patch('...parse')` に合わせて直した
  （`Parser` インスタンスをモックする形から、関数を直接モックする形へ）

## テスト

- `uv run pytest -q` → 297 件すべて成功
- `uv run pytest -m browser -q` → 49 件すべて成功
- `uv run ruff check src tests` / `uv run mypy src` → 問題なし
- `uv run ytstreetorgan parse tests/data/sample.mid -v` で解析・可視化を確認
- `uv run ytstreetorgan rollbook tests/data/sample.mid -m 34notes -o ...` で
  SVG 生成を確認
