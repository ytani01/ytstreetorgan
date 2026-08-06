# ytmidilib への改善要求・機能追加要求

作成: 2026-08-06 / 対象: `ytmidilib` 0.0.3 / 要求元: `ytstreetorgan`（MIDI の解析と再生を `ytmidilib` に任せている）

**この文書だけで作業できるように書いてある。** 要求元のソースや文書を
参照する必要は無い。実装の順序や採否は `ytmidilib` 側で決めてよい。

## 一覧

| # | 内容 | 種別 | 優先度 |
|---|---|---|---|
| [1](#1-tempo-指定が無い-midi-で-全部の音が-0-秒になる) | tempo 指定が無い MIDI で全部の音が 0 秒になる | 不具合 | **最優先** |
| [2](#2-noteinfo-の-end_time-に-int-を渡すと黙って-none-になる) | `NoteInfo` の `end_time` に `int` を渡すと黙って `None` になる | 不具合 | **高** |
| [3](#3-型注釈が無い-pytyped-と食い違っている) | 型注釈が無い（`py.typed` と食い違っている） | 改善 | **高** |
| [4](#4-playerplay-が音符ごとに-print-する) | `Player.play()` が音符ごとに `print()` する | 改善 | **高** |
| [5](#5-player-の生成だけで音声デバイスを掴む) | `Player()` の生成だけで音声デバイスを掴む | 改善 | 中 |
| [6](#6-playerplay-を途中で止められない) | `Player.play()` を途中で止められない | 機能追加 | 中 |
| [7](#7-parserparse-の戻り値が生の-dict) | `Parser.parse()` の戻り値が生の `dict` | 改善 | 中 |
| [8](#8-midi-の書き出しが無い) | MIDI の書き出しが無い | 機能追加 | 中 |
| [9](#9-set_end_time-の例外処理が-indexerror-を取りこぼす) | `set_end_time()` の例外処理が `IndexError` を取りこぼす | 不具合 | 中 |
| [10](#10-ロギングを利用側から制御できない) | ロギングを利用側から制御できない | 改善 | 低 |
| [11](#11-パスが-str-限定) | パスが `str` 限定 | 改善 | 低 |
| [12](#12-mk_visual--print_visual-が-print-直書き) | `mk_visual()` / `print_visual()` が `print()` 直書き | 改善 | 低 |
| [13](#13-noteinfolength-の単位が-docstring-と違う) | `NoteInfo.length()` の単位が docstring と違う | 不具合 | 低 |

---

## 1. tempo 指定が無い MIDI で、全部の音が 0 秒になる

**種別: 不具合 / 優先度: 最優先**

### 現状

`Parser.parse1()` は `cur_tempo = None` から始め、`set_tempo` メッセージを
読むまで `delta_sec` を 0 のままにする。

```python
cur_tempo = None
for msg in merged_tracks:
    delta_sec = 0
    if cur_tempo:
        delta_sec = mido.tick2second(msg.time, tpb, cur_tempo)
    abs_time += delta_sec
```

MIDI の仕様では、`set_tempo` が無いときの既定は **500000 μsec/beat
（♩=120）**。これを適用していない。

### 再現（2026-08-06、0.0.3 で実測）

`set_tempo` を含まない MIDI（480 tpb、四分音符 2 つ）を解析する:

```
start:0000.000 channel:00 note:060 velocity:100
start:0000.000 channel:00 note:062 velocity:100
```

**すべて `abs_time` = 0、`end_time` = `abs_time` で `length()` が 0。**

### 影響

時刻・長さを使う処理がすべて破綻する（再生も、解析結果を図や譜面に
変換する用途も）。DAW が書き出す MIDI にはたいてい `set_tempo` が入って
いるので普段は表面化しないが、手書きや単純な変換で作られた MIDI では
確実に壊れる。

### 要求

`cur_tempo` の初期値を `500000` にする（`mido.bpm2tempo(120)`）。

### 受け入れ条件

- `set_tempo` の無い MIDI で、`abs_time` が音符ごとに増える
- 480 tpb・♩=120 の四分音符なら `length()` が 0.5 になる
- `set_tempo` のある MIDI の結果は変わらない（回帰しない）

---

## 2. `NoteInfo` の `end_time` に `int` を渡すと黙って `None` になる

**種別: 不具合 / 優先度: 高**

### 現状

```python
self.end_time = None
if isinstance(end_time, float):
    self.end_time = round(end_time, 3)
```

`isinstance(end_time, float)` は `int` を弾く。`NoteInfo(0.0, 0, 60, 100, end_time=1)`
は **例外も警告も出さずに `end_time = None`** になる（実測済み）。

`abs_time` は `round(abs_time, 3)` を無条件に呼ぶので `int` でも通る。
**同じ「秒」を表す 2 つの引数で扱いが違う。**

### 要求

- `int` も受け付ける（`isinstance(end_time, (int, float))`、または
  `end_time is not None` で判定して `float()` に通す）
- 受け付けられない値が来たら、黙って `None` にせず `TypeError` にする

### 受け入れ条件

- `end_time=1` と `end_time=1.0` が同じ結果になる
- `end_time=None`（未確定）は従来どおり `None` のまま

---

## 3. 型注釈が無い（`py.typed` と食い違っている）

**種別: 改善 / 優先度: 高**

### 現状

`py.typed` を同梱している＝**型付きパッケージだと宣言している**。
しかし中身に注釈がほぼ無い（`-> ` が全 7 ファイルで 4 個だけ）。

```python
class NoteInfo:
    def __init__(self, abs_time=None, channel=None, note=None,
                 velocity=None, end_time=None, debug=False):
```

### 影響

利用側で `note` / `velocity` / `end_time` が `Unknown | None` と推論され、
型検査が通らない（要求元では basedpyright が 11 件のエラーを出している）。
`py.typed` があるぶん、注釈が無いより悪い（利用側が型を補えない）。

### 要求

公開 API に型注釈を入れる。少なくとも次の 3 つ。

```python
class NoteInfo:
    abs_time: float
    channel: int
    note: int
    velocity: int
    end_time: float | None

    def __init__(self, abs_time: float, channel: int, note: int,
                 velocity: int, end_time: float | None = None,
                 debug: bool = False) -> None: ...

    def length(self) -> float: ...


class Parser:
    def parse(self, midi_file: str | os.PathLike[str],
              channel: Sequence[int] | None = None) -> ParsedMidi: ...


def note2freq(note: int) -> float: ...
```

**`abs_time` / `channel` / `note` / `velocity` の既定値 `None` は外したい。**
現状 `abs_time=None` で生成すると `round(None, 3)` が `TypeError` になるので、
**既定値 `None` は実際には使えない**（呼べば必ず落ちる）。省略できるように
見えるのは嘘なので、必須引数にするのが正しい。

### 受け入れ条件

- `NoteInfo` の 5 つの属性が `Unknown` にならない
- 型検査器（mypy / basedpyright）で `NoteInfo` の属性が具体型に解決される

---

## 4. `Player.play()` が音符ごとに `print()` する

**種別: 改善 / 優先度: 高**

### 現状

`Player.play_th()` が、鳴らした音符ごとに標準出力へ 1 行出す。

```python
self.play_sound(note_info, sec_min, sec_max)
print('%08.3f / %s' % (now, note_info))
```

`play()` の末尾にも `print('end music')` がある。

### 影響

利用側の CLI 出力が音符の行で埋まる（実測 146 行）。
利用側で `sys.stdout` を差し替えて黙らせるのは筋が悪い
（出力の形が変われば黙って壊れる、`play()` 内の他の出力もまとめて
奪ってしまう）。ライブラリが標準出力を占有していると、サーバーからの
利用や、出力をパイプで受ける使い方ができない。

### 要求

次のどちらか（両方でもよい）。

1. **`print()` をやめ、ロガーの DEBUG / INFO に回す**
2. **進捗のコールバックを受け取れるようにする**
   （`play(..., on_note=None)`。`None` なら何も出さない）

既定は「何も出さない」にしてほしい。CLI（`ytmidilib.__main__`）が
表示したいなら、コールバックを渡す側でやればよい。

### 受け入れ条件

- `Player().play(parsed)` が標準出力に何も書かない
- `on_note` を渡したときだけ、音符ごとに呼ばれる

---

## 5. `Player()` の生成だけで音声デバイスを掴む

**種別: 改善 / 優先度: 中**

### 現状

`Player.__init__()` が `pygame.mixer.init()` を呼ぶ。

### 影響

- 利用側が `Parser` と `Player` をまとめて生成する作りだと、
  **再生しないときでも音声デバイスを開く**
- 音声デバイスの無い環境（サーバー、SSH 越し）で生成しただけで失敗しうる
- テストで `Player` を触りたくないのに触ってしまう
- `import ytmidilib` の時点で pygame のバナー（`pygame-ce 2.5.7 ...`）が
  標準出力に出る（pygame 側の挙動だが、`Player` が import 経路にあるため必ず出る）

### 要求

- `pygame.mixer.init()` を **`play()` の最初か、遅延初期化**に移す
- 後始末（`pygame.mixer.quit()`）の手段を用意する
  （`close()` か、コンテキストマネージャ対応）

### 受け入れ条件

- `Player()` を生成しただけでは音声デバイスを開かない
- 音声デバイスが無い環境でも `Player()` の生成は成功し、`play()` で
  分かるエラーになる

---

## 6. `Player.play()` を途中で止められない

**種別: 機能追加 / 優先度: 中**

### 現状

`play()` は全部鳴らし終わるまで返らない。停止・一時停止の手段が無い。
`pos_sec` で開始位置は指定できるが、始めたら最後まで。

### 影響

CLI なら Ctrl-C で済むが、GUI や Web UI から再生させるときに手が無い。

### 要求

- `stop()`（次の音符の前で抜ける）
- できれば `play(..., block=False)` で別スレッド再生し、`is_playing()` で
  状態を見られるようにする

### 受け入れ条件

- 再生中に `stop()` を呼ぶと、1 音以内で止まって `play()` が返る
- `stop()` 後に再度 `play()` できる

---

## 7. `Parser.parse()` の戻り値が生の `dict`

**種別: 改善 / 優先度: 中**

### 現状

```python
out_data = {'channel_set': self._channel_set, 'note_info': data3}
```

### 影響

利用側は `parsed_data['note_info']` のように**文字列のキーで引く**ので、
型検査もエディタの補完も効かず、綴りの間違いが実行時まで分からない。

### 要求

`TypedDict` にする。**既存の呼び出しを壊さない**ので望ましい。

```python
class ParsedMidi(TypedDict):
    channel_set: set[int]
    note_info: list[NoteInfo]
```

`dataclass` にする場合は破壊的変更なので、[互換性の方針](#互換性の方針)を参照。

---

## 8. MIDI の書き出しが無い

**種別: 機能追加 / 優先度: 中**

### 背景

要求元は「曲全体を移調して MIDI として書き出し、ダウンロードさせる」
機能を作ろうとしている。いま `ytmidilib` は読む側しか無いので、
書き出しは利用側で `mido` を直接叩くことになる。**`mido` は `ytmidilib`
経由の間接依存**なので、そのためだけに直接依存を増やすことになる。

### 要求

`list[NoteInfo]`（＋チャンネル情報）から MIDI ファイルを書き出す API。

```python
def write(midi_file: str | os.PathLike[str],
          note_info: Sequence[NoteInfo],
          ticks_per_beat: int = 480,
          tempo: int = 500000) -> None: ...
```

**`parse()` → `write()` で往復できること**が肝心。あわせて、移調を
`ytmidilib` 側で用意してくれるとなお良い（`transpose(note_info, n) ->
list[NoteInfo]`。純粋に `note` へ加算するだけ。0〜127 の範囲外の扱いを
決めること）。ただし**どう移調するかの判断は利用側の仕事**なので、
そこまでは要らない。

### 受け入れ条件

- `parse()` した結果を `write()` し、もう一度 `parse()` して、
  `abs_time` / `note` / `velocity` / `end_time` が（丸め誤差の範囲で）一致する

---

## 9. `set_end_time()` の例外処理が `IndexError` を取りこぼす

**種別: 不具合 / 優先度: 中**

### 現状

```python
try:
    idx2 = note_start[key].pop(0)
except KeyError as ex:
    ...ignored
```

`note_start[key]` が **空のリスト**のとき、`pop(0)` が投げるのは
`IndexError` で、`KeyError` では捕まらない。空リストは、対応する
`note_on` より `note_off` が多いときにできる（キーは `pop()` 後に
`if not note_start[key]` で消しているが、消える前に別の `note_off` が
来る経路がある）。壊れた MIDI で**未捕捉の例外**になる。

### 要求

`except (KeyError, IndexError)` にする。ついでに、警告メッセージに
どの音符（channel / note / 時刻）かを入れてほしい。

---

## 10. ロギングを利用側から制御できない

**種別: 改善 / 優先度: 低**

### 現状

`my_logger.get_logger()` が、モジュール共有の `StreamHandler` を毎回
`addHandler()` し、`propagate = False` を設定する。

```python
logger.propagate = False
logger.addHandler(CONSOLE_HANDLER)
logger.setLevel(INFO)
```

### 影響

- `propagate = False` なので、**利用側のロギング設定が一切効かない**
- ロガー名が `midi_parser.py.Parser` のように**呼び出し元のファイル名**から
  作られる（`inspect.stack()[1]`）ので、名前で絞り込めない
- 同じ名前で `get_logger()` を繰り返し呼ぶと `addHandler()` が重なり、
  同じ行が複数回出る余地がある

### 要求

**ライブラリはハンドラを付けない**（`logging.getLogger(__name__)` を返し、
`propagate` はそのまま）。ハンドラを付けるのは実行可能ファイル
（`ytmidilib.__main__`）の仕事にする。
`debug=True` で DEBUG にしたいなら、レベルだけ設定する（ハンドラは足さない）。

---

## 11. パスが `str` 限定

**種別: 改善 / 優先度: 低**

`Parser.parse()` に `Path` を渡せない（`mido.MidiFile()` 自体は受け付けるが、
docstring と型が `str` を要求している）。内部で `Path` を使っている利用側は、
呼び出しのたびに `str()` へ変換している。

`str | os.PathLike[str]` を受けられるようにしてほしい。

---

## 12. `mk_visual()` / `print_visual()` が `print()` 直書き

**種別: 改善 / 優先度: 低**

`print_visual()` は組み立てた行をその場で `print()` する。
文字列として受け取れないので、**画面以外（Web、ファイル、テスト）に
出せない。**

`format_visual(v_data, channel_set) -> str` を足し、`print_visual()` は
それを `print()` するだけにしてほしい（既存の呼び出しは壊れない）。

---

## 13. `NoteInfo.length()` の単位が docstring と違う

**種別: 不具合（文書） / 優先度: 低**

```python
def length(self):
    """
    length: float
        length of note [msec]      # ← 実際は sec
    """
    return self.end_time - self.abs_time
```

`abs_time` / `end_time` はどちらも秒なので、差も秒。`[sec]` に直すこと。

あわせて、`end_time` が `None` のとき `TypeError` になる点も
docstring に書くか、`None` を返すようにしてほしい（**挙動は変えず
文書だけ直すのでも構わない**。利用側は `Parser.parse()` が必ず
`end_time` を埋めることを前提にしている）。

---

## 互換性の方針

要求元が実際に使っているのは次だけ。**ここが壊れなければ、
残りは自由に変えてよい。**

| API |
|---|
| `Parser()` / `Parser.parse(midi_file, channel)` |
| `Parser.mk_visual()` / `Parser.print_visual()` |
| `NoteInfo`（`abs_time` / `channel` / `note` / `velocity` / `end_time` / `length()` / `__str__`） |
| `Player()` / `Player.play(parsed, pos, sec_min, sec_max)` |
| `Player.DEF_RATE` / `Player.SEC_MIN` / `Player.SEC_MAX` |

- **1・2・3・9・10・11・13 は挙動を壊さない**（型と不具合の修正）。
  そのまま入れてよい
- **4・7 は出力や戻り値の形が変わる**が、利用側はタグ `0.0.3` で固定した
  ので不意打ちにならない。**そのまま入れてよい**（直したらタグを打つこと）
- 5・6・8・12 は追加なので影響しない
