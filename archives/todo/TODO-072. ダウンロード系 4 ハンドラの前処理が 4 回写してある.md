# TODO-072. ダウンロード系 4 ハンドラの前処理が 4 回写してある

## きっかけ

`Download` / `DownloadTransposedMidi` / `DownloadTransposedMidiZip` /
`AuditionMidi` が、次の 3 つを各々持っていた。

- `resolve_in()` → `ValueError` を捕まえて 400（`bad file name`）
- `int(self.get_argument('t'))` → `ValueError` を捕まえて 400（`bad transpose`）
- `is_file()` でなければ 404

## やったこと

`StorganBaseHandler` に 2 つ足して、4 ハンドラを載せ替えた。

- `stored_file(subdir, name)` — `resolve_in()` ＋ 実在の確認。
  置き場の外なら 400、無ければ 404
- `transpose_arg()` — クエリの `t` を整数で読む。読めなければ 400

**`Handler1._stored_path()` とは別にした**（TODO-072 の決めごと）。
あちらは画面に理由を出して `None` を返す版で、持ち帰りの経路で HTML を
返しても読まれない。名前も分けてある。

**404 と 400 の出る順序が変わった。** 前は「名前 → 移調量 → 実在」で、
いまは `stored_file()` が名前と実在をまとめて見るので「名前 → 実在 →
移調量」になる。**存在しないファイルに壊れた `t` を付けた**ときだけ、
`400 bad transpose` ではなく 404 が返る。`Download` は元からこの順で、
4 つで揃った形になる。

## テスト

`pytest -q` 292 passed（既存のテストはどれも実在するファイルで移調量の
誤りを試しているので、順序が変わっても結果は同じ）。
`ruff check src tests` と `mypy src` は問題なし。
