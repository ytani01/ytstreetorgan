# TODO-100. 「土台」「持ち帰り」を分かりやすい語に直す

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

「土台」（基底クラスを指す比喩）と「持ち帰り」（ダウンロードを指す
比喩）が `CLAUDE.md` やコード・テストのコメントに散っていて、
一般的でない言い回しになっていた。具体的なクラス名・普通の語に
直すことにした。

## やったこと

- 「土台」→「基底クラス」または `StorganBaseHandler`（文脈で使い分け）。
  `tests/browser/conftest.py:1` はクラスではないので「ブラウザテスト用の
  fixture」にした
- 「持ち帰り」「持ち帰る」などの活用形を含めて「ダウンロード」に書き直した。
  `CLAUDE.md` / `webroot/CLAUDE.md` / `base_handler.py` / `handler1.py` /
  `history.py` / `config_handler.py` / `download.py` / `transpose.py` /
  `audition.py` / `webapp.py` と、対応するテストが対象
- `storgan.html:281` の `title` を
  「移調した MIDI をダウンロード（ロールブックではありません）」にした
- `CLAUDE.md` の「画面に出す用語」の表に「ダウンロード」の行を足した
- `archives/todo/TODO-095` / `TODO-099` の該当箇所も直した。`TODO-096` は
  見出し・ファイル名（`git mv`）・`TODO.md` の目次リンクを揃えた

範囲外にしたもの: 上記以外の `archives/`（`TODO-014` / `TODO-042` /
`TODO-050` / `TODO-063` / `TODO-068` / `TODO-072` / `TODO-075` など）と、
`TODO.md` の `TODO-050` / `TODO-075` の目次行。アーカイブの決着当時の
ファイル名をそのまま出しているため、書き換えない。

## テスト

`uv run pytest -q`（303 件）、`uv run pytest -m browser -q`（49 件）、
`uv run ruff check src tests`、`uv run mypy src` がすべて通った。
