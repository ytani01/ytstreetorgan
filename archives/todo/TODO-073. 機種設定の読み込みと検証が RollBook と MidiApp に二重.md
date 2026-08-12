# TODO-073. 機種設定の読み込みと検証が `RollBook` と `MidiApp` に二重

## きっかけ

`rollbook.py` と `apps.py` が、`Conf(...).get(model)` → 空なら `ValueError`
→ `validate_config()` → 駄目なら `ValueError` を、**同じ日本語のメッセージ
まで含めて**それぞれ持っていた。片方だけ直すと文面が食い違う。

移調量の正規化（`parse_transpose_arg()` ＋「`'auto'` なら 0 として
持っておく」）も同じ 2 行が両方にあった。`parse_transpose_arg()` は
TODO-043 で module 関数にしたが、その先までは共通化していなかった。

## やったこと

- `conf.load_model_conf(model_name, conf_file)` — 機種名から検証済みの
  設定を返す。無い / 不正なら `ValueError`（メッセージはそのまま画面に
  出るので日本語のまま移した）
- `transpose.initial_transpose(transpose)` — 要求のままの値と、始めに
  使う半音数（`'auto'` なら 0）の 2 つを返す
- `RollBook.__init__` と `MidiApp.__init__` を両方に載せ替えた。
  使わなくなった import（`Conf` / `validate_config` /
  `parse_transpose_arg`）も削除

**`self._transpose_req` の型注釈は残すこと。** タプルで受け取るときは
`self._transpose_req: int | Literal['auto']` を先に宣言しておく。省くと
`Literal['auto']` が `str` へ広げられ、`plan_transpose()` に渡せなくなる
（`mypy` は通るが `basedpyright` が拾う。実際に拾われた）。

## テスト

新しいテストは足していない。**既存のテストが両方の経路を通る**
（`tests/test_rollbook.py` の機種名の誤り、`tests/test_main.py` の
`play -m`）。文面を 1 か所にしたので、片方だけ変わることはもう無い。

結果: `pytest -m ""` 346 passed、`ruff check src tests` / `mypy src` /
`basedpyright src` は問題なし。
