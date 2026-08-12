# TODO-078. `HoleInfo` が設定項目を `.get(key, 0.0)` で読んでいる

## きっかけ

`HoleInfo.__init__` は `mm_per_sec` / `pitch` / `margin` / `hole_height` を
`.get(..., 0.0)` で読み、コメントで「単体で使われたときの保険」と断って
いた。だが 0 が入ると**黙って高さ 0 の図が出る**。TODO-031 の W-1-2 で
潰したのと同じ種類の事故で、あのときは `RollBook.__init__` に
`validate_config()` を入れて塞いだ。`HoleInfo` を直に作る経路には、その
関門が無かった。`ModelConf` が `total=False` なので型でも守られていない。

## 決めごと

**必須項目だけの `TypedDict`（`total=True`）に分ける。**
`HoleInfo` はそちらを受け取り、`conf['pitch']` の形で読む。
既定値 0 は使わない。

## やったこと

- `conf.py` に `ValidModelConf`（`total=True`）を足した。項目は
  `ModelConf` と同じで、必須かどうかだけが違う（`'memo'` だけ
  `NotRequired`。動作に影響しないため）
- `load_model_conf()` の戻り値をこの型にした。`validate_config()` を
  通した直後なので `cast()` してよい
- 図を描く側（`HoleInfo` / `RollBook._conf` / `transpose.py` の各関数 /
  `MidiApp._model_conf`）を `ValidModelConf` に載せ替え、`.get(..., 0.0)`
  を `conf['...']` に変えた
- **`ModelConf` は残す。** 設定を読み書きする側（`Conf.data` と設定
  エディタ）は検証前の値も持つので、生の JSON の形のままでよい

型の使い分けは `CLAUDE.md`「設定ファイル」に書いた。

**`conf.py` の `for field, cast in ...` を `convert` に改名した。**
`typing.cast` を import したことで名前が衝突した（ruff の F402）。

## 実行時はどうなるか

項目が欠けたまま `HoleInfo` を直に作ると **`KeyError`** になる。
既定値 0 で進んで高さ 0 の図を出すよりよい。`RollBook` を通る経路は
`load_model_conf()` が先に弾くので、ここまで来ない。

## テスト

`tests/test_rollbook.py`:

- `MINIMAL_CONF`（必須項目を全部持った設定）を足し、`test_rollbook_parse`
  と `test_holeinfo_str` がこれを使うようにした。どちらも
  `bridge_width` / `bridge_threshold` を欠いていて、いまは `KeyError` になる
- `test_holeinfo_needs_every_field` を新設。7 項目を 1 つずつ抜いて、
  それぞれ `KeyError` になることを見る

結果: `pytest -m ""` 346 passed、`ruff check src tests` / `mypy src` /
`basedpyright src` は問題なし。
