# TODO-048. `ytmidilib` に 2 通目の要求書を出す（ファイルの移調）

TODO-042 の実装方針を変えるための要求。要求書
（[`docs/20260806c-ytmidilib-requests-2.md`](../../docs/20260806c-ytmidilib-requests-2.md)）
を出し、回答
（[`docs/20260806d-ytmidilib-responses-2.md`](../../docs/20260806d-ytmidilib-responses-2.md)）
で 4 項目すべて対応されたので、`0.1.0` → `0.1.1` に上げて取り込んだ。

## なぜ

TODO-042 は当初「`mido` を直接使って元の MIDI のバイト列をいじる」方針
だった。**MIDI を受け取って MIDI を返す処理は `ytmidilib` の仕事**なので、
向こうに寄せた。こちらが `mido.MidiTrack` を組み立て始めると、MIDI の
低レベル処理が 2 リポジトリに散る。

`ytmidilib 0.1.0` の `transpose(note_info, n)` では**代用できなかった**
（実測）。`NoteInfo` は絶対秒・チャンネル・note・velocity しか持たないので、
`write()` で組み立て直すと音色（`program_change`）・音量・ピッチベンド・
トラック構成・テンポ変化が消える。**元のバイト列から `note` だけずらす
API が要る。**

## 要求の骨子

```python
transpose_file(src, dst, n, clip=False)   # src / dst とも path | file-like
transpose(note_info, n, clip=False)       # 既存にも同じ引数を足す
```

- **file-like を受ける**こと（TODO-042 はディスクに残さずメモリ上で返す）。
  `mido.MidiFile` を返す形にはしない。**`mido` を公開 API に出させない**
- **範囲外の扱いを既存の `transpose()` と揃える。** `ValueError`
  （回答書 #8。「クリップは曲が変わったのに成功して返る」は妥当）。
  ファイル版だけ黙って丸めると、同じ「移調」で意味論が 2 つになる。
  `clip=True` を**呼び出し側が明示的に書く**なら、曲が変わることを承知で
  丸めたという判断が呼び出しに現れる

ほかに、打楽器チャンネル（ch 9）を移調するかどうかと、`write()` の
docstring に「何が失われるか」を書くことも要求した。

## 取り込んだタグは `0.1.1`（回答書の `0.2.0` は無い）

回答書 d は「タグ `0.2.0` を打つ」としているが、**リモートに `0.2.0` は
無かった**（2026-08-06 実測。`0.0.1` `0.0.2` `0.0.3` `0.1.0` `0.1.1`）。
中身は届いていて、**`0.1.1` = 回答書 d のコミット (`eb27a16`)** で、その
手前に `transpose_file()` / CLI の `transpose` / pytest 108 件が入っている。

版数と中身は食い違っている（API の追加と `transpose()` の非互換が
パッチ番号に入っている）が、**こちらへの影響は無い**ので `0.1.1` で
固定した。非互換は `transpose()` の ch 9 の既定（`drums=False`）だけで、
当リポジトリが `ytmidilib` から使っているのは `NoteInfo` / `Parser` /
`Player` のみ。

```toml
ytmidilib = { git = "https://github.com/ytani01/ytmidilib.git", tag = "0.1.1" }
```

**こちら側のコードは 1 行も変えていない。** 追加された API を使うのは
TODO-042 から。

## 受け入れ条件は全部満たしていた（2026-08-06 実測）

`webroot/midi/Beetoven_Sonaten_14-1m.mid`（7 トラック・4624 メッセージ）と
`webroot/midi/d-kaeru.mid`（ch 9 に 962 音）で確認した。

- **`transpose_file()`** — file-like → file-like で往復でき、`type` /
  `ticks_per_beat` / トラック数 / メッセージの種類と数が一致。
  **note 以外の 2336 メッセージはバイト単位で完全一致**し、delta time も
  変わらない（回答書 d は「1 バイトも変わらない」を非保証としているが、
  メッセージ単位では実際に変わっていない）
- **`clip`** — 既定で `ValueError`（どの音がどう外れたかがメッセージに出る）、
  そのとき `dst` は作られない。`clip=True` で 0 .. 127 に丸まり WARNING が 1 行
- **ch 9** — `transpose()` / `transpose_file()` とも既定でずらさず、
  範囲チェックの対象からも外れる。`drums=True` でずらす。`DRUM_CHANNEL` 公開
- **`write()` の docstring** — 失われるものが列挙され、`transpose_file()`
  への誘導もある

こちらのテストは 204 + ブラウザ 39 とも通り、`ruff` / `mypy` も通る
（`basedpyright` が `tests/` に出す 39 件は 0.1.0 でも同数で、この取り込みとは
無関係）。

## 使えるようになった API

| API | 内容 |
|---|---|
| `transpose_file(src, dst, n, clip=False, drums=False)` | ファイルの移調（note 以外を変更しない） |
| `transpose(note_info, n, clip=False, drums=False)` | 引数 `clip` / `drums` が増えた |
| `DRUM_CHANNEL` | 9（打楽器チャンネル） |
| `ytmidilib transpose` | CLI サブコマンド（手元で確かめる用） |
