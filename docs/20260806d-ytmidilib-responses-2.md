# ytmidilib: 改善要求（2 通目）への回答 — MIDI ファイルの移調

作成: 2026-08-06 / 対象: `ytmidilib` **0.2.0**（タグ付け予定） / 宛先: `ytstreetorgan`

出典: [`20260806c-ytmidilib-requests-2.md`](20260806c-ytmidilib-requests-2.md)

**要求 #1〜#4 はすべて対応した。** 要求と違う判断をしたのは #1 の実装方式と
受け入れ条件の一部（「1 バイトも変わらない」）、および #3 の既定値の 3 点で、
それぞれ理由を本文に書いた。

要求書に無い追加として、**CLI サブコマンド `ytmidilib transpose`** と、
**`tests/` の新設（pytest・108 テスト）** を入れた。後者は「確認した」の
根拠をリポジトリに残すためで、今回の受け入れ条件はすべて自動テストになっている。

## 一覧

| # | 内容 | 回答 |
|---|---|---|
| [1](#1-元の-midi-を保ったまま移調する-api-が無い) | `transpose_file()` の新設 | 対応した。**実装方式は要求書の案と違う**／「1 バイトも変わらない」は保証しない |
| [2](#2-範囲外の扱いを-transpose-と-transpose_file-で-1-つにする) | `clip` 引数 | 要求どおり対応した（両方に同じ規則） |
| [3](#3-打楽器チャンネル-ch-9-を移調するかどうか) | `drums` 引数 | 対応した。**`transpose()` も既定 `False`**（0.1.0 から挙動が変わる） |
| [4](#4-write-で何が失われるかが-docstring-から読み取れない) | `write()` の docstring | 対応した |
| — | [CLI サブコマンド `transpose`](#追加-cli-サブコマンド-transpose) | 要求書に無い追加 |
| — | [テストの整備](#追加-テストを整備した) | 要求書に無い追加 |

---

## 1. 元の MIDI を保ったまま移調する API が無い

**対応した。** `midi_writer.py` に `transpose_file()` を新設し、
`ytmidilib` から直接 import できるようにした。

```python
from ytmidilib import transpose_file

def transpose_file(src: str | os.PathLike[str] | BinaryIO,
                   dst: str | os.PathLike[str] | BinaryIO,
                   n: int,
                   clip: bool = False,
                   drums: bool = False) -> None: ...
```

`src` / `dst` はパスと file-like の両方を受ける。`str | os.PathLike[str]` か
どうかで分岐し、パスなら `mido.MidiFile(filename=...)` / `save(filename=...)`、
それ以外は `file=` に渡す。要求元の用途（メモリ上で作って HTTP の
レスポンスに載せる）はこれで完結する:

```python
import io
from ytmidilib import transpose_file

buf = io.BytesIO()
with open('orig.mid', 'rb') as f:
    transpose_file(f, buf, 2)
data = buf.getvalue()      # import mido は不要
```

**公開 API に `mido` の型は出していない**（引数・戻り値とも `mido` 非依存）。
要求書の「`mido` の型を公開 API に出さないこと」はそのまま守っている。

### 実装方式（要求書の案と違う判断）

要求書は「新しい `MidiFile` を組み立て直す」案（`mido.MidiFile(type=...,
ticks_per_beat=...)` を作り、トラックごとにメッセージを写す）を挙げていたが、
**読み込んだ `MidiFile` をその場で書き換えて保存する**方式にした
（2026-08-06、当方で決定）。

```python
midi_obj = mido.MidiFile(filename=...)   # あるいは file=
for track in midi_obj.tracks:
    for msg in track:
        if msg.type in ('note_on', 'note_off'):
            msg.note = ...               # note だけ書き換える
midi_obj.save(...)
```

理由は、**引き継ぎ漏れが原理的に起きない**こと。組み立て直す案では、
写すべき属性（`type` / `ticks_per_beat` / `charset` / トラック構成）を
コード側で列挙することになり、列挙から漏れたものが黙って落ちる。要求書の
コード片は `type` と `ticks_per_beat` を写しているが、たとえば `charset` は
写していない。**「note 以外は変更しない」を、コードの網羅性ではなく
「そもそも触らない」で担保したかった。**

外から見える振る舞いは要求書の案と同じで、受け入れ条件も満たしている。

### 「1 バイトも変わらない」は保証しない（受け入れ条件の一部）

受け入れ条件に **「`note` 以外は 1 バイトも変わらない」** とあったが、
**これは保証しない**（2026-08-06、当方で決定）。`mido` で読んで書き直す以上、
running status の使い方や delta time の符号化が元と変わりうるためで、
バイト列の一致を保証するには MIDI のバイナリを自前で走査する実装に
なる。それは `mido` を使う意味を失わせるので採らなかった。

**括弧の中に書かれていた基準** —— メッセージの種類と数、トラック数、
`ticks_per_beat`、`type` の一致 —— **を確認基準とした。** 要求書の再現例と
同じ構成の MIDI（テンポ変化 2 つ・2 トラック・`program_change` /
`control_change` / `track_name` / `time_signature`・ch 9 あり）で確認して
あり、自動テストとして残っている（`tests/test_midi_writer.py`）。

実用上の意味は変わらないはずだが、**バイト列そのものを比較する検証を
組んでいる場合は落ちる。** 該当するなら教えてほしい。

### 受け入れ条件

- テンポ変化・複数トラック・`program_change` / `control_change` を含む
  MIDI で、**メッセージの種類と数・トラック数・`ticks_per_beat`・`type` が
  一致** — **満たす**（バイト単位の一致は上記のとおり非保証）
- `note` が指定した半音数だけずれている — **満たす**
- `src` / `dst` に `io.BytesIO` を渡して往復できる — **満たす**
- 利用側が `import mido` せずに使い切れる — **満たす**

---

## 2. 範囲外の扱いを `transpose()` と `transpose_file()` で 1 つにする

**要求どおり対応した。** 両方に `clip: bool = False` を足した。

```python
transpose(note_info, n, clip=False, drums=False) -> list[NoteInfo]
transpose_file(src, dst, n, clip=False, drums=False) -> None
```

- **既定 `clip=False`** — 範囲外の音が 1 つでもあれば `ValueError`。
  0.1.0 の `transpose()` と同じ挙動で、引数を省いた呼び出しは壊れない
- `clip=True` — 0 .. 127 に丸める。**実際に丸めたときだけ WARNING を 1 行**

```
WARNING clipped 3 note(s) into 0 .. 127
```

音符ごとではなく件数の 1 行。丸めが 1 個も起きなければ何も出さない。

**意味論が 2 つにならないよう、判定はモジュール内のヘルパー
`_shift_note()` に集約した。** `transpose()` と `transpose_file()` は同じ
関数を呼ぶので、範囲チェック・クリップ・ch 9 の扱いが食い違うことがない。

`ValueError` のメッセージは、どの音がどう外れたかが分かる形:

```
ValueError: note out of range: 60 + 100 = 160 (channel:0 at 0.000)  # transpose()
ValueError: note out of range: 60 + 100 = 160 (channel:0)           # transpose_file()
```

（`transpose_file()` は `NoteInfo` を経由しないので絶対秒を持たない。
位置情報の有無だけが違う。）

**`ValueError` のとき `dst` には何も書かない。** 書き換えを全部済ませてから
`save()` するので、途中まで書かれたファイルが残ることはない
（`transpose()` が元のリストを無傷で残すのと同じ性質）。

### 受け入れ条件

- `transpose(..., clip=False)` と引数を省いた `transpose(...)` が
  0.1.0 と同じ挙動 — **満たす**（範囲外で `ValueError`、元のリストは無傷）
- `clip=True` で 0 .. 127 に丸まり、WARNING が 1 行 — **満たす**
- `transpose_file()` も同じ規則 — **満たす**（`_shift_note()` で共通化）

---

## 3. 打楽器チャンネル（ch 9）を移調するかどうか

**対応した。** `drums: bool = False` を両方に足し、docstring にも書いた。

- **`drums=False`（既定）で channel 9 をずらさない**
- `drums=True` で全チャンネルをずらす（0.1.0 の `transpose()` と同じ）
- チャンネル番号は定数 `DRUM_CHANNEL`（= 9）として公開した

### 既定値をどちらにしたか（要求書が判断を委ねた点）

要求書は「`transpose()` は互換を優先して既定 `True` にする判断もありうる」と
していたが、**`transpose()` / `transpose_file()` とも既定 `False` にした**
（2026-08-06、当方で決定）。

理由は、**2 つの関数で既定値が違うこと自体が、要求書の言う「同じ名前で
意味論が 2 つ」に当たる**と考えたため。要求書自身が「`transpose()` を
まだ使っていないので、こちらの都合で言えばどちらでもよい」と書いており、
互換より一貫性を採った。

**これにより `transpose()` の挙動が 0.1.0 から変わる。**
0.1.0 で ch 9 も含めて全チャンネルをずらしていた呼び出しがあれば、
`drums=True` を明示してほしい（移行の表を参照）。

### ch 9 は範囲チェック・クリップの対象からも外した（要求書に無い判断）

`drums=False` のとき、ch 9 の音は**ずらさないだけでなく、範囲チェックにも
かけない。** たとえば ch 9 に note 127 がある MIDI を `+12` で移調しても、
`clip=False` のまま `ValueError` にならない。

**ずらさない音のせいで移調全体が失敗するのは筋が通らない**と判断した。
`clip=True` のときも、ch 9 は丸めの件数に数えない（丸める必要が無いため）。
docstring に明記してある。

### 受け入れ条件

- channel 9 の扱いが docstring に書いてある — **満たす**
  （`transpose()` / `transpose_file()` の両方。「ずらさない音は範囲チェック・
  クリップの対象からも外れる」ことも含む）
- `transpose()` と `transpose_file()` で扱いが同じ — **満たす**
  （既定値・意味論とも同一。実装も `_shift_note()` で共通）

---

## 4. `write()` で何が失われるかが docstring から読み取れない

**対応した。** 要求書の文案とほぼ同じ内容を、箇条書きにして入れた。

```
**`NoteInfo` が持たないものは書き出されない。** 具体的には:

- `program_change` (音色) — すべて既定の音色になる
- `control_change` (音量・ペダルなど)
- `pitch_bend`
- メタメッセージ (`track_name` / `time_signature` など)
- トラック構成 (全チャンネルが 1 トラックに潰れる)
- テンポ変化 (引数 `tempo` の `set_tempo` 1つに潰れる)

したがって `parse()` → `write()` は「元のファイルに戻る」往復では
ない。元のファイルを保ったまま移調したい場合は `transpose_file()`
を使う。
```

要求書の「音色が全部デフォルトになる」という指摘を、`program_change` の
行にそのまま書いた（何が消えるかより、**何が起きるか**が分かるほうが
気づけるため）。`transpose_file()` への誘導も入っている。

### 受け入れ条件

- `write()` の docstring に失われるものが列挙されている — **満たす**

---

## 追加: CLI サブコマンド `transpose`

**要求書には無い追加。** `transpose_file()` の薄いラッパー。

```
ytmidilib transpose SRC DST N [--clip/-c] [--drums/-D] [--debug/-d]
```

```console
$ ytmidilib transpose orig.mid out.mid 2
orig.mid -> out.mid: +2 semitone(s)

$ ytmidilib transpose orig.mid out.mid -2      # 負の値も通る
orig.mid -> out.mid: -2 semitone(s)

$ ytmidilib transpose orig.mid out.mid 100
Error: note out of range: 60 + 100 = 160 (channel:0) .. use --clip
$ echo $?
1
```

- 引数・オプションは `transpose_file()` に 1 対 1 で対応する
  （`-D` の既定 off ＝ ライブラリ側の既定と同じ）
- `N` が負の値でもオプションと誤解されないよう、このサブコマンドだけ
  `ignore_unknown_options=True`
- 範囲外の `ValueError` は `click.ClickException` に包み、`.. use --clip` を
  添えて**トレースバック無しの 1 行**で出す（終了コード 1）

`ytmidilib -h` に `transpose` が並ぶ。**利用側の実装には不要**だが、
手元で移調結果を確かめるときに使える。

---

## 追加: テストを整備した

**要求書には無い追加。** 1 通目 (`0.1.0`) までの確認は使い捨てスクリプトに
よる手動確認で、セッションが終われば消えていた。**回答書に「確認した」と
書く以上、その根拠をリポジトリに残す**ことにした。

`tests/` を新設し、`uv run pytest` で **108 テストが 0.2 秒**で回る。

| ファイル | テスト数 |
|---|---|
| `tests/test_midi_utils.py` | 7 |
| `tests/test_midi_parser.py` | 26 |
| `tests/test_midi_writer.py` | 32 |
| `tests/test_midi_player.py` | 20 |
| `tests/test_wav_utils.py` | 9 |
| `tests/test_cli.py` | 14 |

**今回の受け入れ条件は、すべて `tests/test_midi_writer.py` に自動テストとして
入っている**（メッセージ構成の一致、`io.BytesIO` の往復、`clip` の規則、
ch 9 の扱い、元のリストを壊さないこと、`ValueError` 時に `dst` へ書かないこと）。
1 通目の #8（`write()`）の往復一致も同様。

方針として、**音声デバイスを使うテストは書いていない**（`Player.play()` /
`mk_wav()` / `Wav.play()`）。デバイスの無い環境でも 108 件すべて通ることを
`SDL_AUDIODRIVER=no-such-driver` で確認してある。

MIDI ファイルはバイナリを置かず、`conftest.py` の fixture が `mido` で
組み立てる。**要求元が再現に使ったのと同じ構成の MIDI**（テンポ変化 2 つ・
2 トラック・`program_change` / `control_change` / `track_name` /
`time_signature`・ch 9）が `rich_midi_file` fixture にある。

---

## 移行のために

### 必要なタグ

**タグ `0.2.0` を打つ。ここへ更新してほしい。**
要求元は `tag = "0.1.0"` で固定しているので、更新するまで挙動は変わらない。

バージョンは `hatch-vcs` により git タグから決まる。要求書が触れていた
`uv` の git キャッシュの件（`0.0.4.dev20+g...` になる現象）については、
**タグを打ったら `git push --tags` まで済ませる。** 済んでいるかどうかは
リモートで確認できるので、もし再発したら知らせてほしい。

### 挙動が変わるもの（`0.1.0` から）

| 箇所 | 変更 | 利用側の対応 |
|---|---|---|
| `transpose()` の ch 9 | 既定でずらさなくなった（`drums=False`） | 全チャンネルをずらしたければ `drums=True` |
| `transpose()` の範囲チェック | ch 9 は対象外になった | 通常は影響なし |

**これだけ。** 要求書の「互換性の方針」の表にある API
（`Parser` / `NoteInfo` / `Player` 系）は**すべて従来どおり**で、
`transpose()` を使っていないなら移行作業は無い。

### 追加された API

```python
from ytmidilib import transpose_file, DRUM_CHANNEL
```

| API | 内容 |
|---|---|
| `transpose_file(src, dst, n, clip=False, drums=False)` | ファイルの移調（note 以外を変更しない） |
| `transpose(note_info, n, clip=False, drums=False)` | 引数 `clip` / `drums` が増えた |
| `DRUM_CHANNEL` | 9（打楽器チャンネル） |
| `ytmidilib transpose` | CLI サブコマンド |

`0.1.0` 時点の公開 API は次のとおり（変更なし）:

```python
from ytmidilib import (Parser, NoteInfo, ParsedMidi, VisualData, Player,
                       write, transpose, transpose_file,
                       DEF_TICKS_PER_BEAT, DRUM_CHANNEL, Wav, note2freq)
```

### 品質

- `uv run pytest` — **108 passed**（カバレッジ 80%。`Player` の再生経路を
  意図的にテストしていないぶん低く出る）
- `ruff check src/ tests/` / `mypy src/ tests/` / `basedpyright` の 3 つとも
  **エラー 0・警告 0**
