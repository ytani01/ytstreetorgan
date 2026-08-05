# TODO-040. `play` で stdout を差し替えるのをやめる

TODO-039 で `play` の出力を整理したとき、再生中に音符 1 つずつ出る行を
DEBUG に回すため、`Player.play()` の間だけ `sys.stdout` を差し替える
`_StdoutToDebug` を入れていた。**取りやめた。**

## なぜやめたか

あの行を出しているのは `ytmidilib`（**別リポジトリのパッケージ**）の
`print()`。こちらの都合で横取りするのは筋が悪い。

- 向こうの出力の**形が変われば黙って壊れる**。こちらのテストでは気づけない
- `play()` の中の `print()` を全部まとめて奪うので、**本当に見せたいものが
  出たときも消える**
- 黙らせたいなら `ytmidilib` 側で直すのが筋

`play` の出力に音符の行（146 行）が戻るが、それは元からの挙動。

## 入れたもの

`apps.py` から `_StdoutToDebug` と `contextlib.redirect_stdout` を削除し、
`contextlib` / `io` の import も外した。`player.play()` はそのまま呼ぶ。

`_StdoutToDebug` を当てにしていたテストの主張を直した
（`test_play_does_not_print_each_note` →
`test_play_does_not_list_parsed_notes`）。**再生中の行は対象外**だと
テストの docstring にも書いてある。

TODO-039 の記録からもこの仕組みの記述を消した（残すと誤解を招く）。

## 残したもの（TODO-039 のまま。stdout の差し替えとは無関係）

- どう移調したかを INFO で 1 行出す（`transpose_summary()`）
- 候補の表は `parse` と `rollbook` だけに出す
- **解析した**音符の一覧を `play` では `logger.debug()` にする。
  これはこちらのコードで、元から `-d` のときしか出ていなかった

## 確かめたこと

- `play -m '20notes a' -t auto` で INFO の 1 行が出て、再生中の行が
  元どおり 146 行出る
- `uv run pytest -q`（197 件）/ `ruff` / `mypy` とも通る

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
