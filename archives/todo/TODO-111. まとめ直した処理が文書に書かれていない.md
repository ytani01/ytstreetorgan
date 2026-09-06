# TODO-111. まとめ直した処理（TODO-097〜099）が文書に書かれていない

作成: 2026-09-07
決着: 2026-09-07

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | docs + verifier |
| 実施 | Opus 5 / effort high | main のみ |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 5,470 | 46,689 | 100% |
| 合計 |  |  | 5,470 | 46,689 | 概算 $0.9 |

- 始点のコミットのあとに TODO-110 の作業が挟まっているので、
  `--since '2026-09-07 04:58:07'`（TODO-110 の完了コミットの時刻）で切った
- 変えたのは `webroot/CLAUDE.md` 1 ファイルだけになったので、担当を分けず
  main で完結させた（利用者と着手前に決めた）

## きっかけ

develop へのマージのときの調査で見つけた。文書と実装の食い違いではなく、
もともとどこにも書いていない（分岐前の `CLAUDE.md` にも無かった）。

- `webroot/static/js/api.js`（TODO-099）— `history.js` と
  `config_editor.js` から通信を集めた先。知らないと同じものをまた書く
- `Handler1.post()` の分割（TODO-097）と、`MidiApp.main()` の
  `parse_only` の集約（TODO-098）

## やったこと

`webroot/CLAUDE.md` に「JS のファイル構成（TODO-099）」の節を足した
（「フロントエンド」と「確認の出し方」の間）。書いたのは次の 6 点。

- サーバーとの JSON のやり取りは `StorganApi.postJSON()` を通し、
  画面ごとの JS に `fetch` を書かない
- `reportError()` は文面を出すだけで、後始末は呼ぶ側
- 通信を `alert.js` に混ぜない（役割が 2 つになる）
- `window.$` も `api.js` にある
- 読み込む順は `alert.js` → `api.js` → `model_store.js` → 画面ごと。
  `storgan.html` だけ `alert.js` を読んでいないので、そこでは
  `reportError()` を呼べない
- 機種セレクタの配線は `ModelStore.wire()`。`config_editor.js` だけ使わない

使い回す 3 本（`alert.js` / `api.js` / `model_store.js`）の対応表も添えた。

## `docs/Architecture.md` には書かないと決めた

`Handler1.post()` の分割（TODO-097）と `MidiApp.main()` の `parse_only` の
集約（TODO-098）は書かない。

**どちらもモジュールの中の分け方であって、モジュールをまたぐ決めごとでは
ないため。** `docs/Architecture.md` に載っているのは、依存の向き、設定
ファイルの探索順、SVG の座標系、ハンドラの分割と URL のような、複数の
モジュールにまたがる約束ごとで、1 つの関数の内部の切り分けはその粒度より
細かい。書くと、関数を直すたびに文書も直す必要が出る。

分割の意図は、それぞれの archives（TODO-097 / TODO-098）と、コードの
docstring に残っている。

## テスト

`webroot/CLAUDE.md` だけの変更で、コードは触っていない。書いた内容が実装と
合っていることは、次を読んで確かめた。

- `webroot/static/js/api.js` — `postJSON()` / `reportError()` / `window.$`
- `webroot/templates/{storgan,history,config_editor}.html` の
  `<script>` の並び（`storgan.html` に `alert.js` が無いこと）
- `webroot/static/js/model_store.js` の `wire()` と、
  `config_editor.js` が `wire()` を呼んでいないこと
- `$` の定義が `api.js` の 1 か所だけで、`viewer.js` が 13 か所で
  使っていること
