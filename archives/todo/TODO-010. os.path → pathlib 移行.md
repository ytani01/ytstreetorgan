# TODO-010. os.path → pathlib 移行

旧番号: **B**（コミットメッセージはこの記号で書いてある）

26 件すべて解消。`per-file-ignores` の移行チェックリストは空になった。

B-1（`webroot` / `workdir` の `str` 配線）も同時に解消。`WebServer` が
`Path` に正規化し、`app.settings` にも `Path` のまま渡すようにしたので、
各ハンドラは `self._webroot / 'svg' / fname` と書ける。

`Conf.SEARCH_PATH` の `Path('.')` だけは `PTH201` を除外して残した
（探索対象がカレントであることを明示するほうが読みやすいため）。

検証: SVG 出力が HEAD とバイト一致（195,330 bytes）。CLI・Web とも通しで動作確認。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
