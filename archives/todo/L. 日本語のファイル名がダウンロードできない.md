# L. 日本語のファイル名がダウンロードできない

`Download.get()` が `'attachment; filename=' + name` と組み立てていたため、
**非 ASCII の名前だと 500 になっていた**（HTTP ヘッダは latin-1 しか通らず、
tornado が弾く）。空白入りは 200 で返るが引用符が無く、ブラウザが名前を
途中で切りうる状態だった。

K で履歴に全ファイルのダウンロードリンクが並び、日本語名の MIDI を
上げていると押すたびに 500 になるので、先に直した。

`storage.content_disposition()` に切り出し、RFC 6266 の形にした。

    attachment; filename="download.mid"; filename*=UTF-8''%E3%83%86%E3%82%B9%E3%83%88%E6%9B%B2.mid

- UTF-8 のままの名前は `filename*` に percent-encode して入れる
  （今のブラウザはこちらを優先する）
- 読まないもの向けに ASCII へ落とした `filename` を引用符付きで併記する。
  NFKD で分解してから ASCII に落とすので `naïve` → `naive`。
  日本語のように全部消える場合は `download` + 拡張子にする
- 引用符・バックスラッシュ・制御文字は `_` にする（quoted-string が壊れるため）

テスト 8 本追加（168 → 178）。組み立てそのものと、実際に 200 で落とせて
中身が一致すること。**直す前のコードに戻すと落ちることを確認済み。**

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
