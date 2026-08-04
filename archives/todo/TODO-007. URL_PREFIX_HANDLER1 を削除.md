# TODO-007. URL_PREFIX_HANDLER1 を削除

`/{prefix}/handler1.*` のルートは、テンプレートからも JS からも参照されない
死んだ経路だった。冗長だった `url_prefix_handler1` 設定も外し、`handler1.py` の
`_url_path` は `_urlprefix` から組み立てるようにした。
末尾スラッシュなしのリダイレクト（`/px` → 301 → `/px/`）は従来どおり。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
