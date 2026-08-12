# TODO-075. `handler1.py` が 5 ハンドラ 718 行で、土台クラスも中にある

## きっかけ

`history.py` と `config_handler.py` が、**「ロールブックを作る画面」の
モジュールから基底クラスを import していた**。役割から見て逆で、
`handler1.py` を触るときに他の画面まで巻き込む形になっていた。

## サブエージェントは編成しなかった

「規模が大きいので編成を検討する」と立てた項目だが、**編成せずに進めた**。
実体は「クラスをファイル間で移して import を張り替える」で、判断が要るのは
分割線の引き方だけ。移動そのものは連続した 1 まとまりなので、分担すると
各メンバーが `handler1.py` 718 行を読み直すぶんのほうが高くつく。
着手前に利用者へこの判断を示して、了解を得た。

## やったこと

3 つに分けた。依存は一方向（TODO-043 と同じ考え方）。

    base_handler.py → handler1.py / download.py / history.py /
                      config_handler.py

| モジュール | 中身 | 行数 |
|---|---|---|
| `base_handler.py` | `StorganBaseHandler` | 149 |
| `download.py` | `Download` / `DownloadTransposedMidi` / `DownloadTransposedMidiZip` / `AuditionMidi` | 227 |
| `handler1.py` | `Handler1` | 約 380 |

- import を張り替えた先: `webapp.py`（ルート定義）、`history.py`、
  `config_handler.py`、`tests/test_handler1.py`
- `CLAUDE.md` の「Web 層」に、どのモジュールに何があるかの表を足した

**クラスの中身は 1 行も変えていない**（移しただけ）。TODO-072 で
`StorganBaseHandler` に足した `stored_file()` / `transpose_arg()` は、
そのまま `base_handler.py` へ移った。

## テスト

`tests/test_handler1.py` の import を `Download` だけ `download` から
取るように直した。ほかのテストは無変更で通る。

結果: `pytest -q` 292 passed、`pytest -m browser -q` 49 passed、
`ruff check src tests` と `mypy src` は問題なし。
