# TODO-094. `src/ytstreetorgan/mylog-new.py` が残っている

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

TODO-086 の作業で残った `mylog.py` の古い複製（未追跡）。`mylog.py` との
差は `TYPE_CHECKING` の囲みと 2 つの型注釈が無いことだけで、どこからも
参照されていない。名前にハイフンが入っているので import もできない。
それでも `src/` の中にあるため `uv run mypy src` が型検査の対象に数え、
wheel を作れば同梱される。

## やったこと

利用者に確認したところ、下書きとして残す理由が無いとのことだったので、
`src/ytstreetorgan/mylog-new.py` を削除した。

## テスト

`uv run mypy src` と `uv run pytest -q` を実行し、削除前後で結果が
変わらないことを確認した（もともと import されていないため影響なし）。
