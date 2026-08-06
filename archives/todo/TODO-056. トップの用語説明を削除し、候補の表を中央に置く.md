# TODO-056. トップの用語説明を削除し、候補の表を中央に置く

## きっかけ

TODO-055 の続き。トップ画面から移調のメニューが無くなったので、
**そこに残った用語の説明も要らない**。あわせて、候補の表が広いパネルの
左端に取り残されて見えるのを直す。

## やったこと

- `storgan.html`（トップ）— `{% include "_terms.html" %}` を削除。
  **操作するものが無い画面で先に用語を説明しても読まれない。**
  `_terms.html` を include するのは生成結果の画面だけになった
  （TODO-053 で 2 か所に置いたが、片方の理由が消えた）。
  「生成すると候補の一覧が出る」の案内は残してある
- `my.css` — `#transpose-table { margin-inline: auto; }`。
  表の幅は中身なり（TODO-055）なので、中央に置かないと左隅に寄る
- ZIP のリンクも中央（`.field__hint--center`）。表だけ中央にすると、
  その表に付いているリンクだけ遠くに離れて見える

## テスト

`test_rollbook_page_http.py`

- `test_no_transpose_ui_on_the_upload_page` — トップに `<select id="transpose">`
  も `class="terms"` も無い
- `test_terms_note_on_the_result_page` — 説明は生成結果の側にある。
  見出しと本文の一文で見る（テンプレートの HTML コメントが出力に載るので、
  語の有無では判定できない）
