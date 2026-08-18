# TODO-096. 持ち帰り系のヘッダ組み立てが 3 か所に写してある

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

`download.py` の `Download` / `DownloadTransposedMidi` /
`DownloadTransposedMidiZip` が、`Content-Type` → `Content-Disposition`
（`storage.content_disposition()` を通す）→ `write()` → `finish()` を
同じ順で並べていた。「名前をそのまま入れると、日本語のファイル名で
500 になる」というコメントまで 3 回写してあった。

あわせて `Download.get()` が 4096 バイトずつ読んでいた。`self.write()` は
呼ぶたびに応答へ積むだけで `finish()` まで送り出さないので、分けて読んでも
同じ量がメモリに載る。**分けている意味が無かった。**

## やったこと

- `StorganBaseHandler.finish_download(data, content_type, download_name)`
  を足し、3 つのハンドラを寄せた
- `Download.get()` のループを `path_name.read_bytes()` にした
- `download.py` から `content_disposition` の import が不要になった

**`AuditionMidi` は寄せていない。** `Content-Disposition` を付けないのが
TODO-063 で決めた仕様（試聴用で、持ち帰らせない）。`finish_download()` の
docstring にその旨を書いてある。

## サブエージェント

`core`（opus / high）が実装した。分担の全体は TODO-099 に書いてある。

## テスト

`uv run pytest -q`（303 件）、`uv run pytest -m browser -q`（49 件）、
`uv run ruff check src tests`、`uv run mypy src` がすべて通った。

`Content-Disposition` の中身は `tests/test_history.py` の `TestDownload`
が既に見ている（日本語の名前、空白入りの名前の引用符）ので、テストは
足していない。
