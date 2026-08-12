# TODO-070. `Conf.load()` が壊れた設定を半端に読み込んだ状態にする

## きっかけ

`load()` は `self.data = json.loads(...)` のあとで
`self.models = self._model_names()` を呼んでいた。JSON としては読めるが
要素に `'model'` が無い設定を読ませると、**`data` は壊れた中身のまま・
`models` は空**で残る。`_model_names()` の docstring は「壊れた設定を
半端に読み込んだ状態にしない」と書いているのに、実際にはそうなっていなかった。

`ConfigHandler` は `conf.data` をそのまま画面と JSON API に返すので、
この状態の設定が編集画面に出る。

## やったこと

`src/ytstreetorgan/conf.py` だけで済んだ。

- `load()` は一時変数（`data` / `models`）に読み、**両方が揃ってから**
  `self.data` / `self.models` へ差し替える。途中で例外になったときは
  どちらも触らないので、**前に読めていた設定がそのまま残る**
- `_model_names()` を `staticmethod` にし、数える対象を引数で受け取る形に
  した。`self.data` を見ていると「差し替える前の値を数える」が書けない。
  `save()` からの呼び出しは `self._model_names(self.data)` になる

## テスト

`tests/test_conf.py` の `TestLoad` を直した。

- `test_load_missing_model_key_raises_keyerror_internally` を
  `..._keeps_data_empty` に改名し、`conf.data` も空のままであることを見る
  （元は壊れた中身が入るのを「そういうもの」として書いてあった）
- `test_load_missing_model_key_keeps_previous_data` を足した。**一度読めた
  設定があるときに壊れた設定を読ませても、前の中身と機種名が残る**
- `test_load_non_dict_items_raises_generic_exception` と
  `test_load_json_object_instead_of_list` も、`conf.data` が空のままに変えた

結果: `pytest -q` 292 passed、`ruff check src tests` と `mypy src` は
問題なし。画面には出ないので、ブラウザでの確認はしていない。
