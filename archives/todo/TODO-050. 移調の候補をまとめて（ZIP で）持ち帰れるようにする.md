# TODO-050. 移調の候補をまとめて（ZIP で）持ち帰れるようにする

## きっかけ

TODO-042 で行ごとに MIDI を持ち帰れるようにしたが、候補は最大 7 行あり
（TODO-041 の絞り込みで改善する 5 個 ＋ ±0）、全部欲しいときに 7 回
押すことになる。1 つの ZIP にまとめて返す。

## 作ったもの

`transpose.py`

- `transposed_midi_zip_bytes(src, semitones_list)` — 1 件ずつの
  `transpose_midi_bytes()` を回して `zipfile` に詰めるだけ。中身の名前は
  `transposed_midi_name()`（`holy.t+3.mid`）で 1 件版と揃えてある
- `transposed_zip_name(name)` — `holy.transposed.zip`。**中に何の調が
  入っているかは名前に入れない**（符号付き半音数が 7 個並ぶと読めない）
- 圧縮は `ZIP_DEFLATED`。既定の `ZIP_STORED` だと 7 個ぶんがそのままの
  大きさになる

`handler1.py` / `webapp.py`

- `DownloadTransposedMidiZip` — `/download/midi-transpose-zip/<name>?t=-5,0,3`
- **半音数はクエリで受け取る。** サーバー側で候補を作り直さない
  （元のファイル・機種・絞り込みを引き直すことになる）。1 件版と同じく
  「名前 ＋ 半音数」だけから作れる形に揃えた
- 重複は最初のほうを残して削除する（`dict.fromkeys`）。同じ名前の要素が
  2 つ入った ZIP を作らないため
- `MAX_ITEMS = 32` で頭打ち。外から `t=0,1,2,...` を好きなだけ投げられると、
  1 リクエストで何百回も移調させられる
- **保存しない**のは 1 件版と同じ（`webroot/midi/` を太らせない）

`storgan.html` / `my.css`

- 表の下に「すべての候補の MIDI をダウンロード（ZIP）」（`#transpose-zip`）。
  `t=` には表の行の順で半音数を並べる
- アイコンと字を並べるので `.btn-row.btn-labeled` を足した
  （`.btn-row` は `all: unset` で inline のまま。`.btn-icon` は字の無い版）

## テスト

- `tests/test_midi_transpose.py` — `TestTransposedMidiZipBytes`（名前と順、
  中身が 1 件版と同じ）、`TestDownloadTransposedMidiZip`（全候補・
  ファイル名・重複削除・保存しない・404 / 400・多すぎる場合）
- `tests/browser/test_rollbook_page.py::test_transpose_table_offers_all_candidates_as_zip`
  — ボタンの `t=` の数が表の行数と一致し、実際に落とすと ZIP が
  行数ぶん入っている
