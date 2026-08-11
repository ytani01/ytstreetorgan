# TODO-061. 定型検証サブエージェント委任ドキュメントの作成

作成: 2026-08-09
決着: 2026-08-09

## きっかけ

[multi_agent_token_savings.md](file:///home/ytani/work/ytstreetorgan/docs/multi_agent_token_savings.md) にて提案したマルチエージェント構成のうち、「定型検証のサブエージェント委任」について、具体的なサブエージェントの分類や仕様、導入方針を深掘り検討する必要があったため。

## やったこと

1. これまでの全 60 件の TODO アーカイブおよびプロジェクト構成 (`pyproject.toml`) を調査し、頻出する定型検証作業（ユニットテスト、Linter/Formatter、型チェック、ブラウザ E2E テスト、Git/TODO運用チェック、ドキュメント・表記規約監査）を整理した。
2. 4 種類の定型検証サブエージェント (`ci-runner`, `browser-test-runner`, `repo-status-checker`, `doc-style-auditor`) を定義した。
3. 各サブエージェントの推奨モデル (`flash_lite`), 役割, プロンプト例, 委任の判断基準（直接実行 vs 委任のトレーディングオフ）を明記したドキュメント [routine_verification_subagents.md](file:///home/ytani/work/ytstreetorgan/docs/routine_verification_subagents.md) を作成した。

## テスト

- [routine_verification_subagents.md](file:///home/ytani/work/ytstreetorgan/docs/routine_verification_subagents.md) のマークダウンフォーマット、リンク整合性、指示内容の妥当性を確認。
