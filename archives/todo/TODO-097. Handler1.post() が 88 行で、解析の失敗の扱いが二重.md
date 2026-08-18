# TODO-097. `Handler1.post()` が 88 行で、解析の失敗の扱いが二重

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

`handler1.py` の `post()` に、履歴からの分岐・同名だったときの判定
（overwrite / reuse）・ファイルの保存・解析・描画がまとまって入っていた
（88 行、34 文）。`stored_svg` / `stored_midi` は既に別のメソッドへ
出してあったので、**アップロードから作るぶんだけが本文に残っていた**
形になっていた。

`parse_to_file()` を `try` で囲んで `UNREADABLE_MSG` を出すところが、
`post()` と `_generate_from_stored()` に 1 つずつあった。

`post()` は `async` だったが、`await` するものが 1 つも無かった。

## やったこと

- `post()` は「どこから来たかの見分け」だけ（22 行）にした
- `_generate_from_upload()` — アップロードから作るぶん。
  `_show_stored_svg()` / `_generate_from_stored()` と同じ高さに揃えた
- `_reuse_stored(fname, path)` — 同名だったときの overwrite / reuse の
  判定。断ったら `None`（描画済み）を返す。`_rollbook_of()` /
  `_stored_path()` と同じ約束
- `_parse_to_svg(rollbook, midi_path, svg_path, unlink_on_error=False)` —
  解析の失敗の扱いを 1 か所に
- `async` を外した（tornado は同期の `post()` もそのまま受ける）

**2 つの `try` は同じに見えて同じではなかった。** アップロードのぶんは
読めなかった MIDI を消す（残すと、次に同じ名前で正しいファイルを送る
たびに「既にあります」と言われることになる）。履歴からの再生成では
消さない（元からある、他のものの元でもあるファイルなので）。
この違いは `unlink_on_error` として残し、理由を docstring に書いた。

失敗したときの文言は `UNREADABLE_MSG.format(midi_path.name)` に統一した。
アップロード側は元は `file1_fname` だったが、`file1_path` は
`webroot/midi/` にその名前で作るパスなので、通常は同じ文字列になる。

## サブエージェント

`core`（opus / high）が実装した。分担の全体は TODO-099 に書いてある。

## テスト

`uv run pytest -q`（303 件）、`uv run pytest -m browser -q`（49 件）、
`uv run ruff check src tests`、`uv run mypy src` がすべて通った。

`post()` が同期になった影響を `tests/test_rollbook_page_http.py` で
確かめた（HTTP 経由なので影響なし）。`tests/test_handler1.py` が内部の
メソッドを直接呼んでいないことも確認した。
