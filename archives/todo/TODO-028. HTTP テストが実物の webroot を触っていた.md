# TODO-028. HTTP テストが実物の webroot を触っていた

旧番号: **R**（コミットメッセージはこの記号で書いてある）

`tests/test_webapp_async.py` が `webroot=Path('./webroot')` と実物を渡していて、
アップロードのテストが `webroot/midi/dummy.mid` と
`webroot/svg/dummy.mid.svg` を**実際に書いていた**。`tearDown` で消しては
いたが、途中で落ちると消し残る。一覧を読むテストは、そこに置いてある
実ファイルの影響も受けていた。

K で足した `tests/test_history.py` は一時ディレクトリに複製する形にして
いたので、**同じ目的のテストが 2 通りのやり方で書かれていた**。

`tests/webapp_base.py` に `WebAppTestCase` を切り出した。

**ただし `test_webapp_async.py` には実際には手が入っておらず、この説明は
正しくなかった。** 積み残しは W-1-27 で片付けた（`687e0ab`）。

- `webroot` をテストごとに一時ディレクトリへ複製し、後片付けは
  `addCleanup` に任せる（`tearDown` は不要になった）
- 置き場に何か置きたいときは `setup_files()` を上書きする
  （履歴のテストが MIDI と古い形の SVG を置いている）
- `PORT` と `SERVER_KWARGS`（`debug` / `size_limit`）は subclass が決める

**わざと落としても実物が汚れないことを確認した**（アップロード直後に
例外を投げるテストを一時的に作り、`webroot/` に何も残らないことを見た）。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
