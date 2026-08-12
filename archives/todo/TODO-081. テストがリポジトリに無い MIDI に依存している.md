# TODO-081. テストがリポジトリに無い MIDI に依存している

## きっかけ

テストが `webroot/midi/` の `holy.mid` / `d-kaeru.mid` / `sounstest.mid` を
読んでいた。ここは実行時の作業用で `.gitignore` 済み（`git ls-files` に
出るのは `.dummy` だけ）なので、クローン直後は次の 2 通りに壊れる。

- `tests/webapp_base.py` の `SAMPLE_MIDI` とブラウザテストは、存在を
  確かめずに読むので落ちる
- `tests/test_rollbook.py` などは `if not midi_file.exists(): return` で、
  **何も検証しないまま「成功」と表示される**（`pytest.skip` ではない）

期待値は固定の数値ではなく相対的な条件なので、合成した MIDI で
置き換えられる。**実曲の MIDI は追跡しない**（出所がはっきりしないため）。

## やったこと

### `tests/data/` に、合成した MIDI を生成スクリプトごと置いた

`tests/data/make_midi.py` が mido で 3 本作る。SMF に日時は入らないので、
作り直しても同じ中身になる（`git status` はきれいなまま）。
`.gitignore` の `*.mid` に `!tests/data/*.mid` を足して追跡している。

| ファイル | 何のためのものか |
|---|---|
| `sample.mid` | 中身のある MIDI が要るとき全般。C 長調の半音上（C# 長調）で、-1 半音で `'20notes a'` の音階に収まる。`'34notes'` では D#4 だけが音階に無い |
| `long-notes.mid` | 長い音（分割される）と、同じ高さの重なり（統合される）を含む。全長 2350mm |
| `in-scale.mid` | 全部の音が `'20notes a'` の音階にある（±0 で 100%）。どう移調しても改善しない場合 |

テストが依っている性質は 3 つ。

- 機種の音階に無い音を含む（破線が出る。`off_scale_note_count > 0`）
- `bridge_threshold` の違い（`'20notes'` の 50.0 と `'20notes a'` の 2.7）で
  分割後の数が大きく変わる（`long-notes.mid` で 76 と 608）
- ビューアのテスト用に、高さを合わせた状態で横に大きくはみ出す全長

パスは `tests/conftest.py` の `SAMPLE_MIDI` / `LONG_MIDI` / `IN_SCALE_MIDI`
に 1 か所だけ置き、`tests/webapp_base.py` と `tests/browser/conftest.py` は
そこから引く。

### 黙ったスキップを無くした

`if not midi_file.exists(): return` を全部削除した（`tests/test_rollbook.py`
の 9 か所と `tests/test_storage.py` の 1 か所）。ファイルは必ずあるので、
条件そのものが要らない。

### 期待値を新しい MIDI に合わせた

- `RollBook('20notes a', transpose='auto')` の 1 位は `-24`（旧 `holy.mid`
  の「調そのままで 2 オクターブ下」）から `-1`（半音 1 つ下げると
  C 長調に収まる）へ
- ±0 を下回る行に印が付くのは、`'34notes'` の `+1` から `+2` へ
- 上限を超えるアップロードのテストは、`sample_midi` の大きさに頼るのを
  やめて、その場で 5000 バイトのファイルを作るようにした。**送る前に
  止まるので、中身は MIDI でなくてよい**

置き場に置くファイルの名前として使っていた `holy.mid` も `sample.mid` に
改めた（`transposed_midi_name()` の結果が元の名前から決まるので、
`holy.t+3.mid` のような期待値も一緒に動く）。

### 文書

- `docs/Developer.md` に「中身のある MIDI は `tests/data/` のものを使うこと」
  を足し、「送る MIDI の中身はリポジトリの `webroot/midi/` から読む」を直した
- `tests/CLAUDE.md` の「守ること」を 4 つにした
- `CLAUDE.md` の分割の説明にあった数（音符 1033・実線 339 → 339 と 967）を、
  `long-notes.mid` の実測値（69・68 → 76 と 608）に差し替えた

## テスト

- `uv run pytest -q` → 297 件すべて成功
- `uv run pytest -m browser -q` → 49 件すべて成功
- `uv run ruff check src tests` / `uv run mypy src` → 問題なし
- `git ls-files tests/data` に `.mid` 3 本と `make_midi.py` が出ること
  （`.gitignore` の否定が効いていること）を確かめた
