# TODO-044. `basedpyright` の 11 件を片付ける（本丸は ytmidilib 側）

- [x] `ytmidilib` に型注釈を入れる（**別リポジトリ**。TODO-045 で要求 → `0.1.0`）
- [x] `docs/Developer.md` の「一括で回す」が実際に通るようにする

## 事実

`uv run basedpyright src` が **11 件のエラーを出し、終了コード 1 を
返していた**。`docs/Developer.md`「一括で回す」は `&&` で繋いであるので、
**この手順は以前から通っていなかった**（`pytest` まで到達しない）。
「11 件は許容する」という判断がどこにも記録されないまま残っていた。

## 11 件は全部 1 つの原因だった

`ytmidilib` の `NoteInfo` が無注釈で、`note` / `velocity` / `end_time` が
`Unknown | None` と推論されていた。`py.typed` を置いているのに中身に注釈が
無い、という食い違いがそもそもの原因。

内訳は `transpose.py` 7 件・`rollbook.py` 3 件・`apps.py` 1 件。

## どう片付けたか

案は 3 つ挙げていた。

| 案 | 判定 |
|---|---|
| **`ytmidilib` に型注釈を入れる** | ◎ 採用。原因そのものを断つ |
| こちらに型付きの薄い層を挟む | △ 同じ形の宣言が二重になる |
| 許容すると決めて記録する | △ 逃げ |

`ytmidilib` は利用者自身のリポジトリなので、上流を直すのが素直だった。
TODO-045 の要求書に「#3 型注釈が無い」として出し、`0.1.0` で入った。

**取り込んだ時点で 11 件 → 1 件。** 残った 1 件は
`transpose.py` の `ni.end_time - ni.abs_time`（`end_time` は
`float | None` のまま）で、`ni.length()` を呼ぶ形に直して 0 件になった
（`length()` は `end_time is None` のとき `0.0` を返す）。

## 「3 通りの態度」も揃えた

同じ問題に、場当たりで 3 通りの態度が混ざっていた。

| 場所 | 直す前 | 直したあと |
|---|---|---|
| `HoleInfo.__init__` | `None` を `-1` に読み替え | 不要になったので削除 |
| `merge_overlapping_notes()` | `assert ... is not None` | **残した**（下記） |
| 残り 11 か所 | 素通し | 型が付いたので素通しでよくなった |

`assert` を残したのは、`end_time` の型が `0.1.0` でも `float | None` の
ままだから。「`Parser.parse()` が必ず埋める」は型に出ない事実なので、
`max()` に渡す前に絞り込む必要がある。**態度は assert 1 通りに揃った。**

## 待っている間にやらなかったこと

**`assert` を撒かなかった。** 上流が直ったときに剥がす手間を増やさない
ため。結果、剥がしたのは 2 か所で済んだ（TODO-047）。

## いま

```bash
uv run ruff check src tests && \
uv run mypy src && \
uv run basedpyright src && \
uv run pytest -m ""
```

**通る**（243 passed）。この手順が実際に通ったのは初めて。
