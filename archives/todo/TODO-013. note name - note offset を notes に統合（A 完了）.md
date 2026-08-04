# TODO-013. note name - note offset を notes に統合（A 完了）

旧番号: **A-2**（コミットメッセージはこの記号で書いてある）

2 本の並行配列（`'note name'` と `'note offset'`）を、
`'notes': [{"name": ..., "offset": ...}, ...]` の 1 本にした。
**長さがずれ得る形をやめたので、`validate_config()` の長さ一致チェックが
そもそも不要になった**（代わりに要素ごとに index 付きで検証する）。
`note2scale()` も `NoteConf` のリストを受け取る。

`'name'` の位置づけ（当初の A-2 の宿題）は、統合そのもので解決した。
オフセットと同じ要素の中にあるので「どのトラックの音名か」が構造から自明で、
CLAUDE.md には**表示専用**（SVG 生成は `'offset'` しか見ない）と明記した。

**旧形式はもう読めない**（手動移行）。`~/etc/storgan-conf.json` の 4 機種は
変換済みで、旧ファイルは `storgan-conf.json.old-format-20260804-043049` に退避。
移行の検証として、変更前のコードを worktree に展開し
4 機種 × 5 曲 = 20 通りの SVG を比較 — 全てバイト単位で一致した。

併せて、基準ノート番号（`base note`）を設定エディタの「基本寸法」から
「音階マッピング」へ移した。各トラックの `offset` はこの番号からの半音数なので、
mm の寸法と並べるより表の真上にある方が読める。

なお、直前のコミットの `storgan.conf-dist` → `conf/storgan-conf.json` リネームで
`tests/conftest.py` の参照先が失われ、テストが全 81 件エラーになっていた。
`Conf.CONF_FNAME` を使うようにして解消（`tests/browser/conftest.py` も同様）。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
