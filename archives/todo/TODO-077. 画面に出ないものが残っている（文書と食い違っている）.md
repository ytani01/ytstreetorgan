# TODO-077. 画面に出ないものが残っている（文書と食い違っている）

## きっかけ

`webroot/CLAUDE.md` は「用語の説明（`_terms.html`）は候補の表と同じ場所に
置く」（TODO-056）と書いているのに、実際には出ていなかった。`has_worse`
の説明（TODO-051）も、文書には残っているのに画面には出ない。

## 決めごと

**全部消して、出さないほうに揃えた。** 文書もそれに合わせた。
（片方だけ直すと、また同じ食い違いが残るため。）

## やったこと

- `has_worse` — `Handler1._render()` の計算と `render_page()` への
  引数を削除。`storgan.html` ではコメントの中にしかなかった
- `webroot/templates/_terms.html` — **どこからも include されていなかった**
  ので削除（`git rm`）
- `storgan.html` のコメントアウトされた塊 3 つを削除
  （`.legend` の中身、候補の表の説明、`notices` の 2 つ目のループ）。
  中身が全部コメントだった `<div class="legend">` も一緒に削除した
- `my.css` — 使われていない `.viewer-foot`（3 規則）と、上で使い手が
  無くなった `.legend`（2 規則）を削除。`.readout` のコメントが
  「全長・演奏時間は `.viewer-foot` にある」と書いていたのを
  `.viewer-head` に直した（実際そちらにある）
- `webroot/CLAUDE.md` の TODO-056 / TODO-051 の記述を、
  「出さないと決めた」に書き直した
- `storgan.html` の残るコメントに、**足したくなったらどこに書くか**を
  記した（説明を画面に出す気になったときの置き場所）

## テスト

`tests/test_rollbook_page_http.py::test_terms_note_on_the_result_page` を
`test_transpose_panel_on_the_result_page` に改名し、**生成結果の画面にも
用語の説明が出ない**ことを見るようにした（`class="terms"` が無い）。
アップロードの画面を見る `test_no_transpose_ui_on_the_upload_page` は
元から同じ確認をしていたので、これで両方の画面が守られる。

結果: `pytest -q` 292 passed、`pytest -m browser -q` 49 passed、
`ruff check src tests` と `mypy src` は問題なし。
