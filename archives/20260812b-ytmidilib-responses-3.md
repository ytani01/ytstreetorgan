# ytmidilib: 要求書（3 通目）への回答 — `write()` の file-like 対応

作成: 2026-08-12 / 対象: `ytmidilib` **0.3.0**（タグ付け予定） / 宛先: `ytstreetorgan`

出典: [`20260812a-ytmidilib-requests-3.md`](20260812a-ytmidilib-requests-3.md)

**要求 #1 は要求どおり対応した。** 引数名の据え置き、型注釈を広げること、
docstring と `docs/REFERENCE.md` 7.2 への追記まで含め、要求書と違う判断を
した点は無い。

「併せて」として挙がっていた `Parser.parse()` の file-like 対応は
**今回は入れていない**（理由は後述）。

## 一覧

| # | 内容 | 回答 |
|---|---|---|
| [1](#1-write-が-file-like-を受けない) | `write()` の第 1 引数に file-like | 要求どおり対応した |
| — | [`Parser.parse()` の file-like 対応](#併せて-parserparse-は今回入れていない) | 入れていない（要求外） |

---

## 1. `write()` が file-like を受けない

**対応した。** 第 1 引数の型を広げ、保存を分岐させた。

```python
from ytmidilib import write

def write(midi_file: str | os.PathLike[str] | BinaryIO,
          note_info: list[NoteInfo],
          ticks_per_beat: int = DEF_TICKS_PER_BEAT,
          tempo: int = DEFAULT_TEMPO) -> None: ...
```

中身は要求書のとおり、`transpose_file()` の末尾と同じ形:

```python
if isinstance(midi_file, (str, os.PathLike)):
    midi_obj.save(filename=os.fspath(midi_file))
else:
    midi_obj.save(file=midi_file)
```

要求元の経路は、一時ディレクトリを介さずこれで完結する:

```python
import io
from ytmidilib import write

buf = io.BytesIO()
write(buf, note_info)
data = buf.getvalue()
```

**引数名は `midi_file` のまま据え置いた。** 要求書のとおり、
`dst` への改名はキーワード引数で呼ぶ利用者を壊すだけで、
今回の「型を広げる」話とは関係が無いため。

**型注釈も広げてある**ので、`io.BytesIO` を渡す呼び出しは
`mypy` / `basedpyright` を通る。`# type: ignore` は要らない。

`write()` が書き出すものの中身（何が失われるか、同時刻での消音の
優先、`velocity == 0` を捨てること）は**一切変えていない。**
パスに書いたものと file-like に書いたものは同じ内容になる。

### 受け入れ条件

- `io.BytesIO()` に `write()` でき、`getvalue()` が
  `mido.MidiFile(file=...)` で読み戻せる。トラック数・`ticks_per_beat`・
  `note_on` / `note_off` の並びがパスに書いたものと一致する — **満たす**
  （`tests/test_midi_writer.py::test_write_bytesio`。トラックの内容を
  メッセージ列として丸ごと比較している）
- パスを渡す既存の呼び出しが無変更で動く（`str` / `pathlib.Path` とも）
  — **満たす**（`test_write_str_path` を追加。既存の `write()` の
  テストはすべて `pathlib.Path` 渡しで、無変更のまま通っている）
- 型注釈が `str | os.PathLike[str] | BinaryIO` — **満たす**
- docstring と `docs/REFERENCE.md` 7.2 に、パスと file-like の
  どちらも受けることが書いてある — **満たす**（`REFERENCE.md` には
  `io.BytesIO` を使う例も足した）

---

## 併せて: `Parser.parse()` は今回入れていない

要求書が「受け入れ条件には含めない」として挙げていた
`Parser.parse()` の file-like 対応は、**今回は入れなかった**
（2026-08-12、当方で決定）。

理由は 2 つ。

- **要求元に用途が無い**と要求書自身に書かれている（ディスク上の
  ファイルしか解析しない）。使われない経路を先に広げても、
  テストで維持する対象が増えるだけになる
- `parse()` は `write()` / `transpose_file()` と違い、`mido.MidiFile()` を
  読む以外に**ファイル名をログとエラーメッセージに出している。**
  file-like を渡されたときに何を名乗るかを決める必要があり、
  「同じ分岐を足すだけ」では済まない

**やらないと決めたわけではない。** 用途ができたら知らせてほしい。
そのときは `parse()` 側の名前の扱いも含めて決める。

---

## 移行のために

### 必要なタグ

**タグ `0.3.0` を打つ。ここへ更新してほしい。**
要求元は `tag = "0.2.1"` で固定しているので、更新するまで挙動は変わらない。

要求書が触れていた `uv` の git キャッシュの件については、
**タグを打ったら `git push --tags` まで済ませる。**
もし `0.0.4.dev20+g...` の形で入るようなら知らせてほしい。

### 挙動が変わるもの（`0.2.1` から）

**無い。** 今回は `write()` が受け付ける型が広がっただけで、
既存の呼び出しの挙動・出力バイト列とも変わらない。

要求書の「互換性の方針」の表にある API は**すべて従来どおり**。

### 品質

- `uv run pytest` — **110 passed**（`write()` の file-like と `str` 渡しで
  2 件増えた。カバレッジ 80%）
- `ruff check src/ tests/` / `mypy src/ tests/` / `basedpyright` の 3 つとも
  **エラー 0・警告 0**
