# TODO-062. 定型検証サブエージェントドキュメントに Gemini・Claude のモデル名および Effort 設定を追記する（対応しない）

作成: 2026-08-09
決着: 2026-08-12

## きっかけ

TODO-061 で作った [routine_verification_subagents.md](file:///home/ytani/work/ytstreetorgan/docs/routine_verification_subagents.md) には、
サブエージェントの推奨モデルが `flash_lite` のように書いてあるだけで、
Gemini・Claude の実際のモデル名や Effort の設定が書かれていなかった。
そこを埋めるつもりで立てた項目。

## やらないと決めた理由

**ドキュメント自体を使わなくなったため。** 追記する先が使われないので、
書き足しても読まれない。

なお、元のタイトルは「Gemini/Claude」だったが、ファイル名にスラッシュを
入れられないので中黒にしてある（TODO-060 のアーカイブが
`archives/todo/TODO-060. ドキュメント docs/` というディレクトリに
なってしまったのと同じ罠）。

## テスト

無し（コードもドキュメントも変更していない）。
