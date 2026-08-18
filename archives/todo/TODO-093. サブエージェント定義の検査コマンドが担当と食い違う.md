# TODO-093. サブエージェント定義の検査コマンドが担当と食い違う

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

TODO-091 で `CLAUDE.md` に「テストを回す担当は最後の 1 体にする」と書いた
のに、`.claude/agents/core.md` は `core` 自身に `uv run pytest -q` を
通せと言っていた。`core` と `web`（もしくは `tests`）を並列で動かすと、
`tests/webapp_base.py` が `webroot/templates` と `webroot/static` を
複製するため、`core` の `pytest` が他の担当の書きかけを拾って落ちる
ことがある。

`web.md` の `uv run ruff check src tests` も食い違っていた。`web` が
触れるのは `webroot/templates/` と `webroot/static/` だけで、ruff は
テンプレートも JS も CSS も見ない。自分の仕事に対しては空振りで、
他の担当の書きかけを拾って違反が出ても `web` は `src/` も `tests/` も
触れないので直しようがない。

## やったこと

- `core.md`: `pytest` の実行を外した。**テストを回すのは `tests` 担当に
  任せる**（`CLAUDE.md` の決めごとのとおり）。`ruff` は `core` が書く
  `src/` だけに絞った（`ruff check src tests` → `ruff check src`）。
  `tests` への追従が要るときは報告する旨を明記した
- `web.md`: `uv run ruff check src tests` の行を削除した。触れない範囲の
  検査を指示していたのが原因なので、報告に切り替えるのではなく
  そもそも回さないようにした

`CLAUDE.md` 側の記述（テストを回す担当は最後の 1 体、という決めごと）は
変えていない。今回の食い違いは agent 定義側が古いままだったことが原因。

## テスト

`.claude/agents/*.md` は文書なので、`pytest` / `ruff` / `mypy` の対象外。
差分を読み直し、`core` が `pytest` を回す記述が無いこと、`web` が `src`/
`tests` を検査する記述が無いことを確認した。
