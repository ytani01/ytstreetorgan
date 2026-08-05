# ytmidilib への要求書（2 通目）— MIDI ファイルの移調

作成: 2026-08-06 / 対象: `ytmidilib` **0.1.0** / 要求元: `ytstreetorgan`

**この文書だけで作業できるように書いてある。** 要求元のソースや文書を
参照する必要は無い。実装の順序や採否は `ytmidilib` 側で決めてよい。

前回（[`20260806a`](20260806a-ytmidilib-requests.md) →
[回答](20260806b-ytmidilib-responses.md)）で 13 項目すべてに対応してもらい、
`0.1.0` を取り込んだ。**その `0.1.0` を実際に使おうとして分かったことが
今回の要求。**

## 一覧

| # | 内容 | 種別 | 優先度 |
|---|---|---|---|
| [1](#1-元の-midi-を保ったまま移調する-api-が無い) | 元の MIDI を保ったまま移調する API が無い | 機能追加 | **最優先** |
| [2](#2-範囲外の扱いを-transpose-と-transpose_file-で-1-つにする) | 範囲外の扱いを 2 つの `transpose` で 1 つにする | 改善 | **高** |
| [3](#3-打楽器チャンネル-ch-9-を移調するかどうかが決まっていない) | 打楽器チャンネル（ch 9）を移調するかどうか | 改善 | 中 |
| [4](#4-write-で何が失われるかが-docstring-から読み取れない) | `write()` で何が失われるかが docstring に無い | 改善 | 低 |

**#1 と #2 は 1 つの設計として決めてほしい**（#2 は #1 の引数の話）。
#3 も #1 の仕様の一部だが、独立して判断できるので分けた。

---

## 1. 元の MIDI を保ったまま移調する API が無い

**種別: 機能追加 / 優先度: 最優先**

### 現状

`0.1.0` で入った `transpose()` は `list[NoteInfo]` を受け取る。
ファイルを移調するには `parse()` → `transpose()` → `write()` と回すことに
なるが、**`NoteInfo` は絶対秒・チャンネル・note・velocity しか持たない**
ので、`write()` で組み立て直した時点で他が全部消える。

### 再現（2026-08-06、0.1.0 で実測）

テンポ変化・2 トラック・音色指定・音量指定を含む MIDI を往復させた。

```python
parsed = Parser().parse('orig.mid')
write('out.mid', transpose(parsed['note_info'], 2))
```

```
元:   type=1 tracks=2  {track_name:1, set_tempo:2, time_signature:1,
                        program_change:2, control_change:1,
                        note_on:3, note_off:3, end_of_track:2}
往復: type=1 tracks=1  {set_tempo:1, note_on:3, note_off:3, end_of_track:1}
```

失われたもの:

| 消えたもの | 何が起きるか |
|---|---|
| `program_change` | **音色が全部デフォルトになる。これが一番痛い** |
| `control_change` | 音量・ペダルなどが消える |
| `pitch_bend` | 消える（上の例には入れていないが同様） |
| `track_name` / `time_signature` / その他メタ | 消える |
| トラック構成 | 全チャンネルが 1 トラックに潰れる |
| テンポ変化 | 単一の `set_tempo` に潰れる |

**演奏時間は一致する**（0.750s → 0.750s）。絶対秒から tick に戻すので
辻褄は合い、聞こえる音の高さと長さは正しい。**壊れるのは音色と構造。**

これは `write()` の不具合ではない。`NoteInfo` にその情報が無いのだから
当然で、**「ファイルを移調する」を `NoteInfo` 経由でやろうとしたのが
無理筋**、という話。

### こちらへの影響

要求元は「解析した曲を、選んだ調で MIDI として持ち帰る」機能を作ろうと
している（他の曲と合わせて演奏する、別の道具に読み込ませる用途）。
**利用者が上げた MIDI をそのまま移調して返したい。** 音色が消えては
使い物にならない。

`mido` を直接使えば要求元だけで実装できる（`MidiFile` を読んで
`note_on` / `note_off` の `note` だけずらす）。だが**それは MIDI の
低レベル処理を 2 リポジトリに散らかすことになる**ので、
`ytmidilib` に置きたい。「MIDI を受け取って MIDI を返す」処理は
MIDI ライブラリの仕事だと考えている。

### 要求

**元のバイト列から `note` だけをずらす関数**を足してほしい。

```python
def transpose_file(src, dst, n: int, clip: bool = False) -> None:
    """MIDI ファイルを移調する。note 以外は変更しない。"""
```

- `src` / `dst` は **`str | os.PathLike[str]` に加えて file-like も
  受けること**（`mido.MidiFile(file=...)` と `MidiFile.save(file=...)` が
  そのまま対応している）。要求元は**ディスクに書かずメモリ上で作って
  HTTP のレスポンスに載せる**ので、`io.BytesIO` を渡せることが要る
- `note_on` / `note_off` の `note` だけをずらし、**他のメッセージ・
  トラック構成・`ticks_per_beat`・ファイルの type はそのまま**
- `clip` は #2 を参照

想定している中身（要求元で動作を確認したもの。そのまま使ってよい）:

```python
mf = mido.MidiFile(src)
out = mido.MidiFile(type=mf.type, ticks_per_beat=mf.ticks_per_beat)
for track in mf.tracks:
    new_track = mido.MidiTrack()
    for msg in track:
        if msg.type in ('note_on', 'note_off'):
            msg = msg.copy(note=msg.note + n)   # 範囲の扱いは #2
        new_track.append(msg)
    out.tracks.append(new_track)
out.save(dst)
```

### `mido` の型を公開 API に出さないこと

「`mido.MidiFile` を返す関数」でも同じことはできるが、**それをやると
利用側が `mido` に依存する**。`ytmidilib` は `NoteInfo` で `mido` を
隠しているのだから、そこは崩さないでほしい。

`dst` に file-like を受ければ、利用側は `BytesIO` を渡して
`getvalue()` するだけで済み、`mido` を import せずに完結する。
**これが file-like を要求する一番の理由。**

### 受け入れ条件

- 上の再現に使ったような MIDI（テンポ変化・複数トラック・
  `program_change` / `control_change` あり）を `transpose_file()` に通すと、
  **`note_on` / `note_off` の `note` 以外は 1 バイトも変わらない**
  （メッセージの種類と数、トラック数、`ticks_per_beat`、`type` が一致）
- `note` は指定した半音数だけずれている
- `src` / `dst` に `io.BytesIO` を渡して往復できる
- 利用側が `import mido` せずに使い切れる

---

## 2. 範囲外の扱いを `transpose()` と `transpose_file()` で 1 つにする

**種別: 改善 / 優先度: 高**

### 現状

`0.1.0` の `transpose()` は、移調の結果 0〜127 を外れる音が 1 つでもあれば
`ValueError` を投げる。

回答書の理由づけ（クリップも切り捨ても「曲が変わったのに成功して返る」）
には**同意している**。移調の可否は利用側が判断する仕事だという整理も
そのとおりだと思う。

### こちらへの影響

要求元の用途では**丸めたい**。ダウンロードする MIDI は「元の曲をその調で
持ち帰るもの」で、端の音が数個潰れても実用上は困らない。移調の候補は
機種の音域に合わせて選ばれるので、そもそも範囲外はまず出ない。
**出たときに機能全体が失敗するほうが困る。**

ここで `transpose_file()` だけ黙って丸めると、**同じ「移調」という名前で
意味論が 2 つになる**。それは避けたい。

### 要求

**両方に同じ引数を足して、方針を 1 つにする。**

```python
def transpose(note_info, n: int, clip: bool = False) -> list[NoteInfo]: ...
def transpose_file(src, dst, n: int, clip: bool = False) -> None: ...
```

- **既定は `clip=False`（＝いまどおり `ValueError`）。** 互換を壊さないし、
  「黙って曲が変わらない」という現在の方針が既定のままになる
- `clip=True` のときだけ 0〜127 に丸める。**利用側が明示的に書いたときに
  だけ曲が変わる**ので、「承知のうえで丸めた」という判断が呼び出しに現れる
- `clip=True` で実際に丸めたときは **WARNING を 1 行**出してほしい
  （音符ごとではなく「n 個の音を丸めた」の 1 行。要求元は再生も解析も
  しないバッチ処理でこれを呼ぶので、件数だけ分かれば十分）

### 受け入れ条件

- `transpose(..., clip=False)` と、引数を省いた `transpose(...)` が
  いまと同じ挙動（範囲外で `ValueError`、元のリストは無傷）
- `clip=True` で 0〜127 に丸まり、WARNING が 1 行出る
- `transpose_file()` も同じ規則で動く

---

## 3. 打楽器チャンネル（ch 9）を移調するかどうかが決まっていない

**種別: 改善 / 優先度: 中**

### 現状

`0.1.0` の `transpose()` は全チャンネルの `note` をずらす。
MIDI の慣習では **channel 9（0 始まり）は打楽器で、`note` は音の高さでは
なく楽器の種類**（38 = スネア、42 = クローズドハイハット …）。
ここをずらすと、**曲を移調したつもりでドラムの楽器が入れ替わる。**

### こちらへの影響

要求元（手回しオルガン）に打楽器は無いので、**実害は無い**。
ただし利用者が上げる MIDI にドラムトラックが入っていることはあり、
その MIDI をそのまま移調して返す機能なので、**返した MIDI のドラムが
別の楽器に化ける**ことはありうる。

### 要求

**決めて、docstring に書いてほしい。** 決め方はそちらに任せる。
要求元としては、次が素直だと思う。

```python
def transpose_file(src, dst, n, clip=False, drums: bool = False) -> None:
```

- 既定 `drums=False` で **channel 9 はずらさない**（音楽的にはこちらが正しい）
- `drums=True` で従来どおり全チャンネルをずらす

`transpose()`（`NoteInfo` 版）にも同じ引数があると揃う。ただし
**こちらは既定を変えると `0.1.0` からの挙動が変わる**ので、
互換を優先して既定 `True`（＝ずらす）にする判断もありうる。
**どちらでもよいので、2 つの関数で食い違わないことと、docstring に
明記されていることだけ守ってほしい。**

### 受け入れ条件

- channel 9 をどう扱うかが docstring に書いてある
- `transpose()` と `transpose_file()` で扱いが同じ（既定値が違うなら、
  違う理由が docstring に書いてある）

---

## 4. `write()` で何が失われるかが docstring から読み取れない

**種別: 改善 / 優先度: 低**

### 現状

`write()` の docstring はこうなっている。

```
絶対秒を tick に戻し、note_on / note_off の並びに展開する。
全チャンネルを 1 トラックにまとめる。
```

「1 トラックにまとめる」とは書いてあるが、**`program_change` や
`control_change` が消えることは書いていない。** `NoteInfo` にそれらが
無いことを知っていれば導けるが、`parse()` → `write()` を「読んで書き戻す」
往復だと思って使うと、**音色が消えたことに気づかないまま出荷しうる。**

### こちらへの影響

実際に #1 の実測をするまで気づかなかった。docstring を読んだだけでは
「元のファイルに戻る」と誤解する余地がある。

### 要求

docstring に、**`NoteInfo` に無いものは書き出されない**ことを明記してほしい。
`transpose_file()`（#1）ができたら、そちらへの誘導も 1 行あるとよい。

```
note_on / note_off だけを書き出す。`NoteInfo` が持たないもの
（program_change などの音色、control_change、pitch_bend、メタ
メッセージ、トラック構成、テンポ変化）は**書き出されない**。
元のファイルを保ったまま移調したい場合は `transpose_file()` を使う。
```

### 受け入れ条件

- `write()` の docstring に、失われるものが列挙されている

---

## 互換性の方針

要求元が使っているのは次だけ。**ここが壊れなければ、残りは自由に
変えてよい。**

| API |
|---|
| `Parser()` / `Parser.parse(midi_file, channel)` |
| `Parser.mk_visual()` / `Parser.print_visual()` |
| `NoteInfo`（`abs_time` / `channel` / `note` / `velocity` / `end_time` / `length()` / `__str__`） |
| `Player()` / `Player.play(parsed, pos, sec_min, sec_max)` |
| `Player.DEF_RATE` / `Player.SEC_MIN` / `Player.SEC_MAX` |

- **#1・#4 は追加と文書なので、何も壊さない**
- **#2 は既定値を `clip=False` にする限り壊さない**
- **#3 だけ、`transpose()` の既定を `drums=False` にすると挙動が変わる。**
  要求元は `transpose()`（`NoteInfo` 版）をまだ使っていないので、
  **こちらの都合で言えばどちらでもよい**

`0.0.3` → `0.1.0` のときと同じく、**直したらタグを打ってほしい**
（`0.2.0` など）。要求元は `tag = "0.1.0"` で固定しているので、
タグが増えるまでこちらの挙動は変わらない。

### タグを打つときの注意（要求元でつまずいた点）

`0.1.0` を取り込むとき、**タグを打った直後に `uv` 側でバージョンが
`0.0.4.dev20+g...` として入る**現象に当たった。`uv` の git キャッシュ
（`~/.cache/uv/git-v0/db/`）に新しいタグの ref が入らず、`hatch-vcs` の
`git describe` が古いタグからの距離を返すため。**`ytmidilib` 側の
問題ではない**が、タグを打ったら `git push --tags` まで済んでいることを
確かめてもらえると、こちらで原因の切り分けがしやすい。
