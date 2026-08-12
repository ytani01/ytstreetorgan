# TODO-067. 設定項目 base_note を廃止する

## きっかけ

TODO-064 で機種設定の入力を音名（国際標準）に切り替えたあと、2026-08-12 に
`base_note` の使われ方を確かめたところ、**足して引いているだけ**になっていた。
`note_offsets()` が `midi(name) - base_note` を返し、使う側がそれに
`base_note` を足し戻す。

| 場所 | 実際の式 | 打ち消したあと |
|---|---|---|
| `rollbook.py` `note2scale()` | `base_note + offset == midi_note` | `midi(name) == midi_note` |
| `transpose.py` `playable_notes()` | `{base_note + off for off in ...}` | `{midi(name)}` |
| `transpose.py` `model_note_range()` | `(base_note + min(offsets), base_note + max(offsets))` | `(min(midi), max(midi))` |

つまり `base_note` にどんな値を入れても結果は変わらない。例外は
`model_note_range()` が `notes` の空のとき `(base_note, base_note)` を返す
1 か所だけで、トラックが 1 本も無い機種の話なので実質意味は無かった。

そこで、設定項目を削除するだけでなく、**この打ち消し合いも解消する**ことにした。
`note_offsets()` という関数自体が不要になり、「半音単位のオフセット」という
中間の概念が消える。

## 決めごと

**設定に `base_note` が残っていても黙って無視する。**
`NUMERIC_FIELDS` から外すだけにして、`validate_config()` は通す。設定
エディタで保存すれば自然に消える。

旧形式（`'note name'` / `'note offset'` の並行配列、`'offset'` を持つ辞書の
リスト）を弾くのとは扱いが違う。あちらは**読み方が変わる**ので弾くしかないが、
`base_note` は**余分なキーが 1 つ残るだけで結果が変わらない**ので、エラーに
する理由が無い。TODO-022（設定エディタが未知のキーを黙って落とす。対応しない）
と同じ扱いに揃えた。

## やったこと

サーバー側:

- `conf.py` — `ModelConf` から `base_note` を削除。`NUMERIC_FIELDS` からも
  外し、「残っていても黙って無視する」ことをコメントに書いた。
  **`note_offsets()` は関数ごと削除**
- `rollbook.py` — `note2scale(midi_note, notes)`（引数 `base_note` を削除）。
  中身は `note_name_to_midi(name) == midi_note` を探すだけになった
- `transpose.py` — `playable_notes()` は `{note_name_to_midi(name) ...}`、
  `model_note_range()` は `(min, max)`
- `apps.py` — `_convert_for_model()` の `base_note` の取り出しと
  `note2scale()` の呼び出しを追従

**`model_note_range()` は `notes` が空のとき `(0, 0)` を返す**ことにした
（以前は `(base_note, base_note)`）。この戻り値は `transpose_candidates()` が
探す移調量の範囲を決めるためだけに使われ、鳴らせる音が 1 つも無ければどの
移調量でも結果は同じになる。例外にすると呼ぶ側に受け止める場所が無く、
トラックが 0 本の機種のためだけに扱いが増えるので、値を返す形のままにした。

画面:

- `config_editor.html` — 「基準の音」の入力欄を削除。音階マッピングは音名の
  表から直接始まる
- `config_editor.js` — フィールドの対応と型変換から `base_note` を削除
- `storgan.js` — 機種の諸元の一覧から「基準の音」の行を削除

**「基準の音」という語は画面から完全に消えた。**

設定と文書:

- `conf/storgan-conf.json`（テンプレート）と `~/etc/storgan-conf.json`
  （実運用）から全機種の `base_note` を削除
- `CLAUDE.md` — 用語の表から「基準の音」を削除。設定ファイルの節を
  「穴の位置は音名だけで決まる」に書き直し、`base_note` が残っていても
  読めることを、旧形式（読めない）と区別して明記

## テスト

- `tests/test_conf.py` — `note_offsets` を試す一連のテストを削除。
  **`base_note` が残っている設定でも `validate_config()` が通ることを見る
  テストを足した**（`test_base_note_is_ignored`）
- `tests/test_rollbook.py` — `note2scale()` を 2 引数に。
  `test_model_note_range_without_tracks` は `(0, 0)` を期待する形に
- `tests/test_main.py` / `tests/test_config_handler.py` /
  `tests/browser/test_config_editor.py` — `base_note` への言及を削除

結果: `pytest -q` 291 passed、`pytest -m browser -q` 45 passed、
`ruff check src tests` と `mypy src` は問題なし。設定エディタの画面も
ブラウザで確かめた。

## 分担

サブエージェント（Agent Team）を編成した。定義は
[archives/agents/TODO-067/](../agents/TODO-067/) にある。
