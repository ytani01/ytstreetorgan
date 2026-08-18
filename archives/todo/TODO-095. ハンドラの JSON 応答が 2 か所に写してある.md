# TODO-095. ハンドラの JSON 応答が 2 か所に写してある

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

ソースコード全体を見直したときに見つかった写しの 1 つ。

`history.py` と `config_handler.py` が、次の 3 つをそれぞれ持っていた。

1. **JSON を返す** — `set_header('Content-Type', 'application/json')` ＋
   `write(json.dumps(..., ensure_ascii=False))` が、両方合わせて 6 か所
2. **エラーを返す** — `{'status': 'error', 'message': msg}` ＋
   `set_status(code)`。`history.py` は `_error()` にまとめてあったが、
   `config_handler.py` は POST の中に 2 か所直書きしてあった
3. **リクエストの本文を JSON として読む** — 2 か所

そのうち `config_handler.py` の 400 を返す 1 か所だけ `ensure_ascii=False`
が付いていなかった。JSON としては正しく、画面でも `json.loads()` を通る
ので不具合ではないが、**同じ文面が経路によって違う形で返る**のは、
ここが写しである証拠だった。

## やったこと

`StorganBaseHandler`（`base_handler.py`）に寄せた。

- `request_json()` — 本文を JSON として読む。読めなければ `ValueError`。
  **本文が空かどうかの判定は呼ぶ側に残した**ので、`config_handler.py` の
  「本文が空ならフォームの引数から組み立てる」分岐はそのまま
- `write_json(data)` — `Content-Type` ＋ `json.dumps(..., ensure_ascii=False)`
- `write_json_error(code, msg)` — ログ ＋ `set_status()` ＋ `write_json()`。
  **エラー専用に分けてある**（ステータスと `{'status': 'error', ...}` の形が
  必ず対になるように。1 つにまとめると呼ぶ側が形を組み立て直すことになる）
- `BAD_JSON_MSG` — 2 か所で同じだった文面を定数に

`HistoryHandler._error()` は削除して `StorganBaseHandler` へ寄せ、`config_handler.py` の
直書き 2 か所も置き換えた。結果、付け忘れていた 1 か所も
`ensure_ascii=False` に揃った。**画面に出る文面は変えていない。**

TODO-072（`stored_file()` / `transpose_arg()`）が受け取るほうの集約で、
これは返すほうにあたる。

## サブエージェント

`core`（opus / high）が実装した。分担の全体は TODO-099 に書いてある。

## テスト

`uv run pytest -q`（303 件）、`uv run pytest -m browser -q`（49 件）、
`uv run ruff check src tests`、`uv run mypy src` がすべて通った。
テストの追従は不要だった（外から見た振る舞いを変えていないため）。

`ensure_ascii=False` に揃ったことを確かめるため、既存の「不正な JSON」の
テスト 2 つに、`status` が `'error'` であることと、`message` に `'JSON'`
が含まれることの確認を足した（`tests/test_history.py` /
`tests/test_config_handler.py`）。**両方が同じ `BAD_JSON_MSG` を返す**ことを、
この 2 か所で突き合わせられる。
