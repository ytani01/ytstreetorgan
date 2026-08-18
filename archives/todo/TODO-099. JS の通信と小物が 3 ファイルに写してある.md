# TODO-099. JS の通信と小物が 3 ファイルに写してある

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

- `history.js` の `postDelete()` と `config_editor.js` の `postConfig()`
  が、URL 以外は 1 文字も違わなかった
- `通信エラーが発生しました: ${err}` を `showAlert()` に渡す `.catch()`
  が 5 か所
- `const $ = id => document.getElementById(id);` が `history.js` /
  `config_editor.js` / `viewer.js` の 3 つ
- 機種セレクタの引き継ぎ（`ModelStore.pick()` で初期値を決め、`change` で
  `save()`）が `storgan.js` / `history.js` / `config_editor.js` の 3 つ

## やったこと

`webroot/static/js/api.js` を新しく作った。

- `window.$` — `document.getElementById()` の短縮形
- `window.StorganApi.postJSON(url, payload)`
- `window.StorganApi.reportError(err)` — 通信に失敗したときの知らせ

**`alert.js` に相乗りさせなかった。** あちらは「知らせの出し方」だけの
モジュールとして切り出した経緯があり、通信を混ぜると役割が 2 つになる。

`model_store.js` に `ModelStore.wire(select, onChange)` を足し、
`storgan.js` と `history.js` を差し替えた。**`config_editor.js` は
`wire()` を使っていない**（`save()` を呼ぶ場所が `change` ハンドラでは
なく `loadModelIntoForm()` の中で、他の 2 つと違うため）。

**`.catch()` の中の後始末は消していない。** `config_editor.js` の保存は
`setBusy()` を戻し、機種の追加は `closeDialog()` を呼んでから
`reportError(err)` を呼ぶ。`reportError()` は文面を出すだけの関数に
してある。

`webroot/templates/` の 3 ページに `{{ static_url('js/api.js') }}` の行を
足した。読み込む順は `alert.js` → `api.js` → `model_store.js` → 画面ごと。

**画面の見た目・操作・文言は変えていない。**

## サブエージェント

TODO-088 で用意した `.claude/agents/` の定義をそのまま使った
（複製は作っていない）。TODO-095〜099 で共通の分担は次のとおり。

- `core`（opus / high）— TODO-095・096・097・098。4 つとも `src/` の
  Python で、095 と 096 は `base_handler.py` を共有するので同じ担当が順に
- `web`（sonnet / medium）— TODO-099。`webroot/static/js/` だけなので
  `core` と並列で動かした
- `tests`（sonnet / medium）— 最後に 1 体。両方が終わってから追従と検査。
  途中で回すと、落ちた原因がどちらの未追従なのか分からなくなる

並列にしたのは、触るファイルが重ならなかったため（TODO-067 と同じ）。
`docs` は編成しなかった（動作も画面も変えないので追従が出ない見込み
だった。結果として `CLAUDE.md` に土台の助けの表を 1 つ足したが、
これは統括が行った）。

## テスト

`uv run pytest -q`（303 件）、`uv run pytest -m browser -q`（49 件）、
`uv run ruff check src tests`、`uv run mypy src` がすべて通った。

ブラウザでは、機種設定の追加・保存・削除と、履歴の削除を実際に動かして
確かめた（コンソールにエラーなし、確認に使ったファイルと設定は元に戻し、
差分が無いことを確認済み）。
