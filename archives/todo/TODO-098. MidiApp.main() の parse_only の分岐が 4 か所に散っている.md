# TODO-098. `MidiApp.main()` の `parse_only` の分岐が 4 か所に散っている

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

`apps.py` の `MidiApp.main()` が `if self._parse_only:` を 4 回書いて
いた（候補の表、音符の一覧を print、その else の DEBUG ログ、最後の
`return`）。`parse` と `play` で何が違うのかが、上から下まで読まないと
分からなかった。

## やったこと

`if self._parse_only:` を 1 か所（早期 return）に集約した。

- `_print_parsed(parsed_data)` — `parse` のときだけ出すもの
  （機種と移調の 1 行 ＋ 候補の表 ＋ 音符 1 つずつの一覧 ＋ 共通ぶん）
- `_print_channels(parsed_data)` — `channel_set=` と `-v` の可視化。
  **`parse` でも `play` でも同じものを出す**ので分岐の外

**`parse` と `play` をクラスに割らなかった。** 解析までは同じ手順で、
違うのは「そのあと出すか鳴らすか」だけ。分けると
`_convert_for_model()` を持ち回すことになる。

注釈に `ytmidilib.ParsedMidi` を使った。

## サブエージェント

`core`（opus / high）が実装した。分担の全体は TODO-099 に書いてある。

## テスト

`uv run pytest -q`（303 件）、`uv run pytest -m browser -q`（49 件）、
`uv run ruff check src tests`、`uv run mypy src` がすべて通った。

`uv run ytstreetorgan parse FILE.mid -m 34notes` を実行し、出力の順序と
文面が変わっていないことを確かめた。
