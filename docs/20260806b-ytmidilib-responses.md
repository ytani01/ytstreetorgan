# ytmidilib: 改善要求への回答

作成: 2026-08-06 / 対象: `ytmidilib` **0.1.0**（タグ付け済み） / 宛先: `ytstreetorgan`

出典: [`20260806a-ytmidilib-requests.md`](20260806a-ytmidilib-requests.md)

**要求 #1〜#13 はすべて対応した。** 要求と違う判断をしたのは #4 / #7 / #8 の
3 点で、それぞれ理由を本文に書いた。

以下、要求書の項番 (#1〜#13) の順で回答する。

## 一覧

| # | 内容 | 回答 |
|---|---|---|
| [1](#1-tempo-指定が無い-midi-で全部の音が-0-秒になる) | tempo 既定値 | 修正した |
| [2](#2-noteinfo-の-end_time-に-int-を渡すと黙って-none-になる) | `end_time` に `int` | 修正済みだった（0.0.3 以降） |
| [3](#3-型注釈が無いpytyped-と食い違っている) | 型注釈 | 修正済みだった（0.0.3 以降） |
| [4](#4-playerplay-が音符ごとに-print-する) | `print()` をやめる | **選択肢 1（DEBUG ログ）のみ採用。`on_note` は不採用** |
| [5](#5-player-の生成だけで音声デバイスを掴む) | mixer の遅延初期化 | 対応した（`close()` / `with` も追加） |
| [6](#6-playerplay-を途中で止められない) | 停止・非同期再生 | 対応した（`stop()` / `is_playing()` / `block=`） |
| [7](#7-parserparse-の戻り値が生の-dict) | `TypedDict` | 対応済みだった。**名前は要求書に合わせ `ParsedMidi`** |
| [8](#8-midi-の書き出しが無い) | MIDI 書き出し | 対応した。**`transpose()` の範囲外は `ValueError`** |
| [9](#9-set_end_time-の例外処理が-indexerror-を取りこぼす) | `IndexError` | 修正した |
| [10](#10-ロギングを利用側から制御できない) | ロギング | 対応した |
| [11](#11-パスが-str-限定) | `os.PathLike` | 対応した |
| [12](#12-mk_visual--print_visual-が-print-直書き) | `format_visual()` | 追加した |
| [13](#13-noteinfolength-の単位が-docstring-と違う) | docstring の単位 | 修正済みだった（0.0.3 以降） |

「修正済みだった」の 4 件 (#2 / #3 / #7 / #13) は、要求書が対象とした 0.0.3 の
あとに入っていた `0e1a2ea refactor: 型ヒントを追加し、lint の指摘を解消する`
で既に解消していた。**0.0.3 のままでは直っていない**ので、いずれにせよ
`0.1.0` への更新が必要。

---

## 1. tempo 指定が無い MIDI で、全部の音が 0 秒になる

**修正した。**

`Parser.parse1()` の `cur_tempo` の初期値を `DEFAULT_TEMPO`（= 500000。
`mido.bpm2tempo(120)`）にし、`if cur_tempo:` の分岐を撤去した。
定数は `midi_parser.DEFAULT_TEMPO` として持っている。

### 受け入れ条件

- `set_tempo` の無い MIDI で `abs_time` が音符ごとに増える — **満たす**
- 480 tpb・♩=120 の四分音符で `length()` が 0.5 — **満たす**

  ```
  >>> [(x.abs_time, x.length()) for x in Parser().parse('no_tempo.mid')['note_info']]
  [(0.0, 0.5), (0.5, 0.5)]
  ```

- `set_tempo` のある MIDI で回帰しない — **満たす**。`set_tempo` を含む
  既存ファイル（pygame 同梱の `MIDI_sample.mid`）で `parse -v` の出力が
  変更前と一致することを確認した

---

## 2. `NoteInfo` の `end_time` に `int` を渡すと黙って `None` になる

**要求書の時点では既に修正済みだった。** 現在の実装:

```python
self.end_time = None if end_time is None else round(end_time, 3)
```

`isinstance()` による分岐そのものを外したので、`int` はもちろん、
`round()` を受け付ける型なら通る。**黙って `None` になる経路は無い。**
数値でない値は `round()` が `TypeError` を投げる（要求どおり、黙って
握り潰さない）。

### 受け入れ条件

- `end_time=1` と `end_time=1.0` が同じ結果 — **満たす**（どちらも `1`／`1.0`
  で、`length()` の値は同一）
- `end_time=None` は `None` のまま — **満たす**

---

## 3. 型注釈が無い（`py.typed` と食い違っている）

**要求書の時点では既に修正済みだった。** 公開 API 全体に注釈が付いている。
`NoteInfo` は要求どおりのシグネチャ:

```python
def __init__(self, abs_time: float, channel: int, note: int,
             velocity: int, end_time: float | None = None) -> None: ...
def length(self) -> float: ...
```

**`abs_time` / `channel` / `note` / `velocity` の既定値 `None` は撤去済み**
（要求どおり必須引数）。`debug` 引数も `NoteInfo` からは無くなっている
（エンティティごとにロガーを取るのをやめたため。`__init__` に `debug=` を
渡していた場合は `TypeError` になるので注意）。

`Parser.parse()` / `note2freq()` も要求書のシグネチャどおり。

### 受け入れ条件

- `NoteInfo` の 5 属性が `Unknown` にならない — **満たす**
- mypy / basedpyright で具体型に解決される — **満たす**。
  `ruff` / `mypy` / `basedpyright` の 3 つとも **エラー 0・警告 0**

---

## 4. `Player.play()` が音符ごとに `print()` する

**選択肢 1（ロガーへ回す）を採った。選択肢 2 のコールバック `on_note` は
採らなかった。**

- `play_th()` の `print(f'{now:08.3f} / {note_info}')` → `self._log.debug()`
- `play()` 末尾の `print('end music')` → `self._log.debug()`
- `mk_wav()` 後の `_log.info('len(snd)=...')` も DEBUG へ落とした

結果、**既定 (`debug=False`) では標準出力にも標準エラーにも何も出ない。**
CLI で従来の表示が欲しい場合は `-d` を付ける。

### `on_note` を採らなかった理由

要求書自身が「どちらか（両方でもよい）」としており、**要求の主眼である
「既定では何も出さない」は選択肢 1 だけで満たせる**。そのうえで、
`on_note` は発音を担うワーカースレッドから呼ぶことになり、
**利用側のコールバックがスレッド安全性を意識する必要が生じる**。
呼び出しが遅ければ再生のタイミングにも影響する。使う当てが決まる前に
この制約付きの公開 API を増やしたくなかった。

**必要になったら要求してほしい。** 実装するなら、スレッドから呼ばれる旨を
明記したうえで `play(..., on_note=...)` を足す形になる。

### 受け入れ条件

- `Player().play(parsed)` が標準出力に何も書かない — **満たす**
- `on_note` を渡したときだけ音符ごとに呼ばれる — **該当なし**（不採用のため）。
  代わりに、`ytmidilib.Player` のロガーを DEBUG にすれば同じ情報が取れる:

  ```python
  import logging
  logging.getLogger('ytmidilib.Player').setLevel(logging.DEBUG)
  ```

---

## 5. `Player()` の生成だけで音声デバイスを掴む

**対応した。**

- `Player.__init__()` から `pygame.mixer.init()` を外し、`init_mixer()` を
  新設。`mk_wav()` の冒頭で呼ぶ（初期化済みなら何もしない）
- 後始末の手段として **`close()` と、コンテキストマネージャの両方**を用意した

```python
with Player() as player:      # ここでは音声デバイスを開かない
    player.play(parsed)       # ここで初めて開く
# 抜けるときに stop() → pygame.mixer.quit()
```

`WavApp` も再生時のみ初期化するようにしたので、`wav -n`（保存のみ）は
音声デバイス不要になった。

### 受け入れ条件

- `Player()` の生成だけでは音声デバイスを開かない — **満たす**
- 音声デバイスが無い環境でも生成は成功し、`play()` で分かるエラーになる —
  **満たす**。`play()` は `block` の値によらず `mk_wav()` を呼び出しの中で
  済ませるので、**`block=False` でも `pygame.error` は `play()` から見える**
  （別スレッドに飲まれない）

### 未解決: pygame のバナー

要求書が「影響」に挙げていた **`import ytmidilib` 時の
`pygame-ce 2.5.7 ...` バナーは、まだ出る。** `Player` が import 経路にあり、
pygame が import 時点で出すためで、mixer の初期化時期とは別の話。
黙らせるには、**`import ytmidilib` より前に**環境変数を設定する:

```python
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import ytmidilib
```

（動作確認済み。）`ytmidilib` 側でこれを勝手に設定すると、利用側の pygame の
挙動まで書き換えてしまうので、ライブラリからは触らない方針にした。

---

## 6. `Player.play()` を途中で止められない

**対応した。** 要求の「できれば」の部分（非同期再生）も入れた。

```python
player.play(parsed, block=False)   # すぐ戻る
player.is_playing()                # True
player.stop()                      # 1音以内で止まる
player.play(parsed)                # 再度再生できる
```

- `stop()` — `threading.Event` を見て次の音符の前でループを抜ける。
  ワーカースレッドにも終了を伝え、`pygame.mixer.stop()` で鳴っている音も
  止める。待ちを `time.sleep()` から `Event.wait()` に変えて反応を良くした
- `play(..., block: bool = True)` — **既定値付きの追加引数**なので、
  従来の `play(parsed, pos, sec_min, sec_max)` はそのまま通る
- 再生中の `play()` は `RuntimeError`（先に `stop()` を呼ぶこと）

### 受け入れ条件

- 再生中に `stop()` で 1 音以内に止まり `play()` が返る — **満たす**
  （6 秒の MIDI を `block=False` で再生し、1 秒後に `stop()`。
  即座に戻り `is_playing()` が `False` になることを確認）
- `stop()` 後に再度 `play()` できる — **満たす**（Event を `play()` ごとに
  クリアしている）

---

## 7. `Parser.parse()` の戻り値が生の `dict`

**要求書の時点では既に `TypedDict` 化済みだった。** ただし
**クラス名を要求書に合わせて `ParsedMidi` に改名した**（元は別名だった）。

```python
class ParsedMidi(TypedDict):
    channel_set: set[int]
    note_info: list[NoteInfo]
```

`dataclass` にはしていない（要求書のとおり、既存の
`parsed['note_info']` を壊さないため）。

可視化データにも `VisualData` という `TypedDict` を用意しており、
`ParsedMidi` / `VisualData` とも `ytmidilib` から直接 import できる:

```python
from ytmidilib import ParsedMidi, VisualData
```

### 改名した理由

要求書に挙げられた名前をそのまま使うのが、要求元の型注釈をそのまま
通せるので確実だと判断した（2026-08-06、当方で決定）。
**旧名は残していない。** 旧名を import している箇所があれば直してほしい。

---

## 8. MIDI の書き出しが無い

**対応した。** 新規モジュール `midi_writer.py`。

```python
from ytmidilib import write, transpose, DEF_TICKS_PER_BEAT

write(midi_file, note_info, ticks_per_beat=480, tempo=500000)  # -> None
transpose(note_info, n)                                        # -> list[NoteInfo]
```

- `write()` — `NoteInfo` を note_on / note_off に展開し、絶対秒を
  `mido.second2tick()` で tick に戻す。全チャンネルを 1 トラックにまとめ、
  先頭に `set_tempo` を書く。**同時刻のイベントは「消音 → 発音」の順**に
  並べ、同じ note の連打が衝突しないようにしてある
- `midi_file` は `str | os.PathLike[str]`。`velocity == 0` のエントリは無視、
  `end_time` が `None` の音は長さ 0 として書く
- `transpose()` — `note` に `n` を加えた**新しいリスト**を返す。
  元のリストは変更しない

### 受け入れ条件

- `parse()` → `write()` → `parse()` で `abs_time` / `note` / `velocity` /
  `end_time` が一致 — **満たす**。和音と同一 note の連打を含むデータで、
  既定 (480 / 500000) に加え 96 / 300000、960 / 700000 でも一致を確認した

### `transpose()` の範囲外の扱い（要求と違う判断）

要求書は「0〜127 の範囲外の扱いを決めること」としていた。
**範囲外の音が 1 つでもあれば `ValueError` を投げ、移調全体を失敗させる**
ことにした（2026-08-06、当方で決定）。

```
ValueError: note out of range: 60 + 100 = 160 (channel:0 at 0.000)
```

クリップ（127 に丸める）や、その音だけ捨てる案も考えたが、
**どちらも「曲が変わったのに成功して返る」**。移調の可否は利用側が
判断する仕事（要求書の言うとおり）なので、判断材料になるよう
どの音がどう外れたかをメッセージに入れて失敗させる形にした。
リストを走査してから新リストを作るので、**例外時に元のリストは無傷**。

利用側でクリップしたい場合は、`transpose()` を呼ぶ前に自前で範囲を
確かめるか、`NoteInfo` を作り直してほしい。

---

## 9. `set_end_time()` の例外処理が `IndexError` を取りこぼす

**修正した。**

- `except KeyError` → `except (KeyError, IndexError)`
- 警告メッセージに channel / note / 時刻を含めた

対応する note_on が無い note_off を含む MIDI で、警告を出して読み飛ばし、
残りの音符が正しく解析されることを確認した。

---

## 10. ロギングを利用側から制御できない

**対応した。** 要求どおり、**ライブラリはハンドラを付けない。**

- `get_logger()` から `addHandler()` と `propagate = False` を外し、
  レベル設定だけにした
- ロガー名を `inspect.stack()` ベースから**パッケージ名ベース**へ変更。
  `ytmidilib.Parser` / `ytmidilib.Player` のようになり、名前で絞り込める
  （`__name__` を渡した場合はそのまま使う）。`inspect.stack()` を呼ばなく
  なったので軽くもなった
- ハンドラの設定は `my_logger.init_handler()` に切り出し、CLI
  (`__main__.py` の click group) からのみ呼ぶ

つまり **`import ytmidilib` だけではハンドラが付かず**、利用側の
`logging.basicConfig()` の書式に従う。個別に黙らせる／喋らせるのも
標準の作法でできる:

```python
logging.getLogger('ytmidilib').setLevel(logging.WARNING)
logging.getLogger('ytmidilib.Player').setLevel(logging.DEBUG)
```

**注意:** `init_handler()` は `ytmidilib` ロガーに `propagate = False` を
設定するので、**ライブラリとして取り込む側は呼ばないこと。**

---

## 11. パスが `str` 限定

**対応した。** `Parser.parse()` の型注釈と docstring を
`str | os.PathLike[str]` にした。`pathlib.Path` をそのまま渡せる。

ついでに `Wav.save()` も同じにした（`wave.open()` の型定義が `str` しか
受けないので、内部で `os.fspath()` を挟んでいる）。
`midi_writer.write()` は最初から `str | os.PathLike[str]`。

**`str()` への変換は不要になった。**

---

## 12. `mk_visual()` / `print_visual()` が `print()` 直書き

**対応した。**

```python
v_data = parser.mk_visual(parsed['note_info'])
text = parser.format_visual(v_data, parsed['channel_set'])   # -> str
parser.print_visual(v_data, parsed['channel_set'])           # 従来どおり
```

`print_visual()` は `format_visual()` の結果を `print()` するだけの薄い
ラッパーにしたので、**既存の呼び出しは壊れない**。内部の
`_print_note_ruler()` も `_format_note_ruler()`（`list[str]` を返す）に
変えてある。

`parse -v` の出力が変更前と完全一致することを diff で確認した。

---

## 13. `NoteInfo.length()` の単位が docstring と違う

**要求書の時点では既に修正済みだった。** `[msec]` → `[sec]`。

あわせて、`end_time` が `None` のときの挙動も変わっている。
**`TypeError` ではなく `0.0` を返す**（docstring にも明記）。
`Parser.parse()` は必ず `end_time` を埋めるので、要求元の使い方には影響しない。

---

## 移行のために

### 必要なタグ

**タグ `0.1.0` を打った。ここへ更新してほしい。**
要求元はタグ `0.0.3` で固定しているが、`0.0.3` には #2 / #3 / #7 / #13 の
修正も入っていないので、`0.1.0` にしないと今回の対応は 1 つも入らない。

バージョンは `hatch-vcs` により git タグから決まる。

### 挙動が変わるもの（`0.0.3` から）

| 箇所 | 変更 | 利用側の対応 |
|---|---|---|
| `Player.play()` の出力 | 音符ごとの行と `end music` が出なくなる | 表示が欲しければロガーを DEBUG に |
| mixer の初期化 | `Player()` ではなく `play()` 時 | 音声デバイスのエラーが出る場所が変わる |
| ロガー | ハンドラを付けなくなった／名前が `ytmidilib.*` に | 出力が欲しければ利用側で `basicConfig()` 等 |
| `parse()` の戻り値の型名 | `ParsedMidi` に改名 | 旧名を import していれば変更 |
| `NoteInfo.__init__` | `debug` 引数が無い／前 4 引数が必須 | `debug=` を渡していれば削除 |
| `NoteInfo.length()` | `end_time is None` で `0.0`（旧: `TypeError`） | 通常は影響なし |

`ParsedMidi` の中身（`channel_set` / `note_info`）と `NoteInfo` の属性、
`Parser.parse()` / `mk_visual()` / `print_visual()` / `Player.play()` の
呼び出し形は**すべて従来どおり**。要求書の「互換性の方針」の表にある API は
全て確認済み。

### 追加された API

```python
from ytmidilib import (Parser, NoteInfo, ParsedMidi, VisualData, Player,
                       write, transpose, DEF_TICKS_PER_BEAT, Wav, note2freq)
```

| API | 内容 |
|---|---|
| `write(midi_file, note_info, ticks_per_beat=480, tempo=500000)` | MIDI 書き出し |
| `transpose(note_info, n) -> list[NoteInfo]` | 移調（範囲外は `ValueError`） |
| `DEF_TICKS_PER_BEAT` | 480 |
| `Player.play(..., block=True)` | `False` で非同期再生 |
| `Player.stop()` / `Player.is_playing()` | 停止・状態取得 |
| `Player.close()` / `with Player() as p:` | mixer の後始末 |
| `Player.init_mixer()` | mixer の明示的な初期化（通常は不要） |
| `Parser.format_visual(v_data, channel_set) -> str` | 可視化を文字列で取得 |
| `ParsedMidi` / `VisualData` | `TypedDict` |
| `ytmidilib.my_logger.init_handler()` | **アプリ専用。ライブラリ利用側は呼ばない** |

### 品質

`ruff check src/` / `mypy src/` / `basedpyright` の 3 つとも
**エラー 0・警告 0**。
