# TODO-080. `docs/routine_verification_subagents.md` を削除する

作成: 2026-08-12
決着: 2026-08-12

## きっかけ

TODO-061 で作った文書だが、中身が Gemini 前提のままで、現在の運用と食い違っていた。

- モデル名が `flash_lite` / `pro`、呼び出しが `invoke_subagent` / `define_subagent`
- 永続化先を `.agents/agents/<name>/AGENTS.md` としているが、実際は
  `.claude/agents/*.md` に置き、済んだら `archives/agents/TODO-NNN/` へ移す
- 「全 60 件の TODO」（いまは 78 件）、使っていない `ruff format --check`
- アーカイブへのリンクが 3 件切れている（TODO-066 のファイル名修正に追従していない）

追記する話だった TODO-062 は、既に（対応しない）で決着している。

## やったこと

1. `git rm docs/routine_verification_subagents.md`
2. `archives/todo/TODO-061` と `TODO-062` に「この文書は TODO-080 で削除した」と一行添えた。
   辿れるようにするためで、**archives のリンク切れ自体は書き換えていない**
   （当時の記録なので）

`docs/multi_agent_token_savings.md` からの参照は無かった（`grep` で確認）。

## テスト

無し（文書の削除だけで、コードは変更していない）。
