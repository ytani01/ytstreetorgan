# TODO-008. Claude Code のプラグインをこのプロジェクトで無効化

`github` / `frontend-design` は 60 起動で 0 回だった。他プロジェクトでは使うため、
ユーザースコープ（`~/.claude/settings.json`）は有効のまま、このプロジェクトの
`.claude/settings.local.json` で `false` にした（設定の優先順位は
ユーザー < プロジェクト < ローカル）。`pyright-lsp` は Python なので有効のまま。
※ `settings.local.json` は gitignore されているため、リポジトリには残らない。

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
