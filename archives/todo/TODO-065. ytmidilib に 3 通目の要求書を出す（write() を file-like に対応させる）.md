# TODO-065. `ytmidilib` に 3 通目の要求書を出す（`write()` を file-like に対応させる）

要求書（[`20260812a-ytmidilib-requests-3.md`](../20260812a-ytmidilib-requests-3.md)）を
出し、回答（[`20260812b-ytmidilib-responses-3.md`](../20260812b-ytmidilib-responses-3.md)）で
要求どおり対応された。**この項目は要求書までで、0.3.0 の取り込みは TODO-083。**

## きっかけ

`ytmidilib.write()` が `str | os.PathLike` しか受けず、file-like を受けない。
そのため TODO-063 の試聴（`audition.playable_midi_bytes()`）が、バイト列が
欲しいだけなのに一時ディレクトリを作って書いて読み戻して消していた。
**試聴の MIDI は保存しない**という決めごとに、小さな穴が開いている。

同じパッケージの `transpose_file()` は 2 通目（TODO-048）で file-like を
受けるようになっていて、**その理由は `write()` にもそのまま当てはまる**。
書き出す 2 つの関数で受け付ける型が食い違っている状態だった。

## やったこと

要求は 1 件だけ。

- `write()` の第 1 引数に `BinaryIO` を足す（`str | os.PathLike[str] | BinaryIO`）
- **引数名 `midi_file` は据え置き。** `transpose_file()` の `dst` に揃えたく
  なるが、キーワード引数で呼ぶ利用者が壊れる。今回は型を広げるだけの話で、
  非互換を持ち込む価値が無い。**揃えてほしいのは名前ではなく受け付ける型**
- **型注釈も広げる**こと。実装だけ通ってもこちらで `# type: ignore` を
  書くことになる

`Parser.parse()` の file-like 対応は「併せて」として挙げたが、
**受け入れ条件には含めなかった**（こちらはディスク上のファイルしか
解析しない）。

## 回答（2026-08-12）

**要求どおり。要求書と違う判断をした点は無い。** 引数名の据え置き、型注釈、
docstring と `docs/REFERENCE.md` 7.2 への追記まで含めて対応され、
受け入れ条件 4 つとも根拠のテスト名（`test_write_bytesio` /
`test_write_str_path`）付きで満たしている。出力バイト列は `0.2.1` から
変わらず、非互換は無い。

`Parser.parse()` は**入れていない**。理由は「要求元に用途が無い」ことと、
`parse()` はファイル名をログとエラーメッセージに出すので、file-like を
渡されたときに何を名乗るかを決める必要があり、同じ分岐を足すだけでは
済まないこと。**やらないと決めたわけではない**ので、用途ができたら
知らせる。

## テスト

**こちら側のコードは変えていない**（要求書と回答書という文書だけ）。
`ytmidilib` 側は `pytest` 110 passed、`ruff` / `mypy` / `basedpyright`
とも 0 件と回答書にある。

## タグ

`0.3.0` が push 済みなのを確認した（2026-08-12、`git ls-remote --tags`）。
取り込みは TODO-083。
