# ytmidilib への要求書（3 通目）— `write()` を file-like に対応させる

作成: 2026-08-12 / 対象: `ytmidilib` **0.2.1** / 要求元: `ytstreetorgan`

**この文書だけで作業できるように書いてある。** 要求元のソースや文書を
参照する必要は無い。実装の順序や採否は `ytmidilib` 側で決めてよい。

これまでの経緯:

| 通 | 要求書 | 回答書 | 取り込んだ版 |
|---|---|---|---|
| 1 | [`20260806a`](20260806a-ytmidilib-requests.md) | [`20260806b`](20260806b-ytmidilib-responses.md) | `0.1.0` |
| 2 | [`20260806c`](20260806c-ytmidilib-requests-2.md) | [`20260806d`](20260806d-ytmidilib-responses-2.md) | `0.1.1` |

**今回は 1 件だけ。** 2 通目の #1 で `transpose_file()` に入れてもらった
file-like 対応を、`write()` にも同じように入れてほしい、という話。

## 一覧

| # | 内容 | 種別 | 優先度 |
|---|---|---|---|
| [1](#1-write-が-file-like-を受けない) | `write()` が file-like を受けない | 改善 | 中 |

---

## 1. `write()` が file-like を受けない

**種別: 改善 / 優先度: 中**

### 現状

同じパッケージの中で、MIDI を書き出す 2 つの関数の受け付ける型が
食い違っている（`0.2.1` で実測）。

```python
def transpose_file(src: str | os.PathLike[str] | BinaryIO,
                   dst: str | os.PathLike[str] | BinaryIO,
                   n: int, clip: bool = False, drums: bool = False) -> None: ...

def write(midi_file: str | os.PathLike[str], note_info: list[NoteInfo],
          ticks_per_beat: int = DEF_TICKS_PER_BEAT,
          tempo: int = DEFAULT_TEMPO) -> None: ...
```

`transpose_file()` は 2 通目の #1 で file-like を受けるようになった。
その理由（要求元はディスクに書かずメモリ上で作って HTTP の
レスポンスに載せる）は **`write()` にもそのまま当てはまる**のに、
`write()` だけがパスしか受けない。

### こちらへの影響

要求元は「その機種で実際に鳴る音だけを、ブラウザで試聴する」機能を
持っている。鳴らす音は `NoteInfo` のリストとして手元にあるので、
それを `write()` で MIDI にして HTTP のレスポンスに載せる。

**この経路はディスクに何も残さない**（試聴用の MIDI は保存しない、
という決めごとがある）。ところが `write()` がパスしか受けないので、
いまはこうなっている。

```python
with tempfile.TemporaryDirectory(prefix='storgan-audition-') as tmp_dir:
    tmp_path = Path(tmp_dir) / 'audition.mid'
    write(tmp_path, note_info)
    data = tmp_path.read_bytes()
```

書いたものは戻る前に消えるので実害は出ていないが、**一時ディレクトリを
作って書いて読み戻して消す、という 4 手が「バイト列が欲しい」だけの
ために要る。** 同じ用途で `transpose_file()` を使っている隣の経路は
`io.BytesIO` 1 つで済んでいる（2 通目の成果）。

### 要求

**`write()` の第 1 引数に file-like も受け付けてほしい。**

```python
def write(midi_file: str | os.PathLike[str] | BinaryIO,
          note_info: list[NoteInfo],
          ticks_per_beat: int = DEF_TICKS_PER_BEAT,
          tempo: int = DEFAULT_TEMPO) -> None: ...
```

中身は `transpose_file()` の末尾にある分岐と同じでよい。
`mido.MidiFile.save()` が `filename=` と `file=` の両方を持っている。

```python
if isinstance(midi_file, (str, os.PathLike)):
    midi_obj.save(filename=os.fspath(midi_file))
else:
    midi_obj.save(file=midi_file)
```

### 引数名は `midi_file` のまま据え置いてほしい

`transpose_file()` に合わせて `dst` に改名したくなるところだが、
**変えないでほしい。** キーワード引数で呼んでいる利用者が壊れる。
要求元は位置引数で呼んでいるので改名されても動くが、
**この要求は「型を広げる」だけの話で、非互換を持ち込む価値は無い。**

`transpose_file()` は `src` / `dst` の対で受け取るので名前が違うのは
自然だと考えている。**揃えてほしいのは名前ではなく、受け付ける型。**

### 型注釈も広げること（実行時だけ通っても困る）

要求元は `mypy` を通している。実装が file-like を受けても
シグネチャが `str | os.PathLike[str]` のままだと、`io.BytesIO` を
渡した時点でエラーになり、**結局こちらで `# type: ignore` を書くことに
なる。** `transpose_file()` と同じく `BinaryIO` を足してほしい。

### 受け入れ条件

- `io.BytesIO()` を渡して `write()` でき、`getvalue()` が
  `mido.MidiFile(file=...)` で読み戻せる（トラック数・`ticks_per_beat`・
  `note_on` / `note_off` の並びが、パスに書いたものと一致する）
- **パスを渡す既存の呼び出しは無変更で動く**（`str` / `pathlib.Path` とも）
- 型注釈が `str | os.PathLike[str] | BinaryIO` になっていて、
  `io.BytesIO` を渡す呼び出しが型チェックを通る
- docstring と `docs/REFERENCE.md` の 7.2 に、パスと file-like の
  どちらも受けることが書いてある

### 併せて（要求ではない）

`Parser.parse()` も `str | os.PathLike[str]` だけを受ける。
**要求元はディスク上のファイルしか解析しないので、こちらは要らない。**
「読み書きの入口を揃える」という観点で気になるなら検討してほしい、
という程度の話で、**この要求書の受け入れ条件には含めない。**

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
| `transpose_file(src, dst, n, clip, drums)` |
| `write(midi_file, note_info, ticks_per_beat, tempo)` |

前回までと違い、**`transpose_file()` と `write()` が加わっている**
（2 通目で入れてもらった API を実際に使い始めたため）。

今回の要求は**型を広げるだけ**なので、何も壊さない。

これまでと同じく、**直したらタグを打ってほしい**（`0.3.0` など）。
要求元は `tag = "0.2.1"` で固定しているので、タグが増えるまで
こちらの挙動は変わらない。

`0.1.0` のときに当たった、**タグを打った直後に `uv` 側でバージョンが
`0.0.4.dev20+g...` として入る**現象（`uv` の git キャッシュに新しいタグの
ref が入らない）は要求元側で対処できるが、`git push --tags` まで
済んでいることは確かめてほしい。
