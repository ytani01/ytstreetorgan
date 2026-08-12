# TODO-076. `Handler1._render()` が候補の表示ロジックまで抱えている

## きっかけ

`_render()` は引数が 10 個、`render_page()` へ渡す値が 20 個あった。
うち `notices` / `show_transpose_table` / `zero_note_pct` / `zero_sec_pct` /
`has_worse` は**候補だけから決まる**のに、ハンドラの中でしか作れないので、
テストが HTTP 経由になっていた。

## やったこと

`transpose.py` に切り出した。

- `TransposeView`（NamedTuple） — `notices` / `show_table` /
  `zero_note_pct` / `zero_sec_pct`
- `transpose_view(candidates)` — 候補（`None` も可）から上の 4 つを作る

`_render()` は `view = transpose_view(candidates)` の 1 行になり、
`render_page()` へ `view.notices` の形で渡す。

- **`has_worse` は無くなった**（TODO-077 で、印の説明を画面に出さないと
  決めたため）。この項目が挙げた 5 つのうち残ったのは 4 つ
- **「呼ぶ側に作らせず 1 か所でまとめて作る」（TODO-043）は守った。**
  置き場所をハンドラから `transpose.py` へ移しただけで、呼ぶ側には
  散らしていない
- 置き場所が `transpose.py` なのは、候補を作るのも並べるのも注記を書くのも
  そこだから。`rollbook.py` を import しないという決めごとにも触れない

## テスト

`tests/test_rollbook.py` に、**HTTP を通さない**単体テストを 4 つ足した。

- `test_transpose_view_without_candidates` — `None` も空リストも、
  表は出さず ±0 の成績は 0.0
- `test_transpose_view_shows_the_table_when_something_improves`
- `test_transpose_view_hides_the_table_without_improvement` — 改善が
  無ければ表は出さず、文だけ出す（TODO-041）
- `test_transpose_view_notices_come_from_the_rows_on_screen`

**候補は空でなければ ±0 の行を含んでいること**（`select_transpose_rows()`
が必ず残す）。`transpose_notices()` が元からその前提で書いてあり、
±0 が無い候補を渡すと `StopIteration` になる。前提を
`transpose_view()` の docstring に明記した。

結果: `pytest -q` 296 passed、`ruff check src tests` と `mypy src` は
問題なし。
