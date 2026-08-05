# TODO-043. 移調まわりを整理する

TODO-038〜041 を続けて足したぶん、`rollbook.py` が 999 行まで膨らみ、
同じ手順が 2 か所に写された状態になっていた。TODO-042 で `handler1.py` に
新しいハンドラを足す前に片付けた。**振る舞いは変えていない。**

## 1. 移調の手順が 2 か所に写されていた（いちばん危なかった）

`RollBook.parse()` と `MidiApp._convert_for_model()` が、同じ 5 手順を
それぞれ持っていた（候補を作る → `'auto'` なら 1 位を採る → 表に出す行に
絞る → 実際にずらす）。

**片方だけ直すと静かに食い違う。** 実際に揃っていなかった:
`MidiApp` は `transpose_score()` で「いま選んでいる行」を `self._chosen`
に持っていた（INFO の要約に使う）が、`RollBook` は持っていなかった。

`transpose.py` の `plan_transpose()` にまとめた。返すのは
`TransposePlan`（`transpose` / `candidates` / `chosen` / `notes`）で、
両方がこれを呼ぶ。`RollBook` も `chosen` を得られるようになった。

**`merge_overlapping_notes()` は手順に含めない。** 呼ぶ側で済ませて渡す。
あれは「実機は 1 音に 1 パイプ」という別の話（TODO-038）で、含めると
`transpose.py` → `rollbook.py` の import が要って循環する。

## 2. `RollBook._check_transpose()` を `apps.py` が外から呼んでいた

```python
# apps.py（直す前）
self._transpose_req = RollBook._check_transpose(transpose)
```

`MidiApp` は `RollBook` を作らないのに、引数の検証だけ借りていた。
module 関数 `parse_transpose_arg()` として公開し、両方がそれを呼ぶ形にした。

## 3. `rollbook.py` が 999 行 → 596 行

移調まわりを **`transpose.py`（498 行）** へ分けた。移したのは
`key_label` / `TransposeCandidate` / `_NoteTally` / `transpose_score` /
`transpose_candidates` / `add_transpose_rows` / `transpose_has_improvement` /
`select_transpose_rows` / `transpose_notices` / `transpose_notes` /
`playable_notes` / `model_note_range`。

`playable_notes()` と `model_note_range()` は**移調の候補を作るためだけ**に
あり、他から呼ばれていないことを確かめてから移した。

**`note2scale()` と `merge_overlapping_notes()` は残した。** 前者は
`HoleInfo` が穴の位置を決めるのに使い、後者は TODO-038 の話。どちらも
移調の都合ではない。

依存が一方向に揃った:

```
conf.py → transpose.py → rollbook.py → apps.py / handler1.py
```

**`transpose.py` は `.conf` しか import しない**（`rollbook.py` を
import すると循環する）。

## 4. `handler1.py` で候補と注記を組で渡していた

```python
candidates=rollbook.candidates,
notices=transpose_notices(rollbook.candidates),   # これが 2 か所に
```

`_render()` は既に `candidates` から `show_transpose_table` を作っていたので、
**注記も `_render()` の中で作る**ようにした。呼ぶ側は候補だけ渡せばよく、
片方で注記を渡し忘れる余地も消えた。

## やらなかったこと

- **`RollBook` / `HoleInfo` の分割**。430 行あるが、ブックの組み立てという
  1 つの話でまとまっている
- **SVG まわりの分離**。110 行で、色の定義は `storage.py` が読み直す約束
  （`HOLE_COLOR` / `META_PREFIX`）と結びついている。動かすと
  「描くほうが持ち主」という関係が薄れる

## `_transpose_req` には型注釈を付けること

`parse_transpose_arg()` は `int | Literal['auto']` を返すが、
**インスタンス属性へ代入するときに pyright が `Literal['auto']` を
`str` へ広げる**（literal widening）。注釈を省くと属性の型が
`int | str` になり、`plan_transpose(requested: int | Literal['auto'])`
に渡せなくなる。

```python
self._transpose_req: int | Literal['auto'] = parse_transpose_arg(transpose)
```

`RollBook.__init__` と `MidiApp.__init__` の両方で明示している。
**`mypy` はこれを見逃す。`basedpyright` だけが拾った。**

## 確かめたこと

- **テストの中身を 1 つも書き換えずに全部通る**（`test_rollbook.py` の
  import 元を `ytstreetorgan.transpose` に振り分けただけ）。
  振る舞いを変えていない印にした
- `uv run pytest -q`（204 件）/ `-m browser`（39 件）/ `ruff` / `mypy` とも通る
- `basedpyright src` の指摘が、整理の前後で**種類も件数も同じ**
  （11 件。`ytmidilib` が型情報を持たないことによるもので、
  `rollbook.py` にあった指摘が `transpose.py` へ移っただけ）。
  **一度これを回し忘れて、上の literal widening を見落としかけた**
  （`ruff` と `mypy` は通っていた）。`docs/Developer.md` の
  「一括で回す」に `basedpyright` も入っている。省かないこと
- `parse -m '20notes a' -t auto` の出力（候補の表・注記・INFO の要約）が
  整理前と同一であることを目で確認

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
