# TODO-074. `book`（ビューアに渡す諸元）が型で守られていない

## きっかけ

`book` は素の `dict` で、「**項目を増やすときは両方を直すこと**」を
コメントと往復テストだけで縛っていた（`Handler1._book_of()` と
`storage.book_from_svg()`）。

## やったこと

`storage.py` に `BookInfo`（TypedDict）を足し、2 か所の戻り値にした。

**`total=True` のまま、値のほうを `X | None` にしてある。** キーは必ず
全部ある（テンプレートが `book['width']` の形で読む）が、値は揃わない。

- `created` は `book_from_svg()` が `None` を入れて、呼び出し側が
  `mtime_text()` で埋める
- `width` などは、**属性が無い古い SVG** では読めない

置き場所を `storage.py` にしたのは、`book_from_svg()` がそこにあり、
`handler1.py` が元から `storage` を import しているため。

往復テスト（全項目の一致を見るもの）はそのまま残した。型は片側の
**付け忘れ**を拾い、テストは**値の食い違い**を拾う。役割が違う。

## テスト

新しいテストは足していない。`mypy src` が `_book_of()` の返す辞書を
`BookInfo` と突き合わせるようになった（キーを 1 つ落とせば落ちる）。

結果: `pytest -q` 292 passed、`ruff check src tests` と `mypy src` は
問題なし。
