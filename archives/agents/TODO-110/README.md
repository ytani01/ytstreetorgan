# TODO-110 の分担

`docs/User.md` と `docs/images/*.png` を今の画面に追従させる項目。

| 担当 | 定義 | 受け持ち | 報告 |
|---|---|---|---|
| web | `.claude/agents/web.md`（Sonnet 5 / effort medium） | `make_shots.py` でのスクリーンショット撮り直し、新旧の比較、`docs/User.md` 3 章の追従 | [web-report.md](web-report.md) |
| verifier | `~/.claude/agents/verifier.md`（Haiku 4.5） | 撮った画像とテンプレートの突き合わせ、戻した 4 枚の再確認、`User.md` の記述と実画面の一致、pytest / ruff / mypy | [verifier-report.md](verifier-report.md) |

## この分担にした理由

- 文書と画像だけの項目だが、`docs/images/make_shots.py` を走らせるという
  「書いたとおりに試せるもの」があるので、確認を別の担当に分けた（TODO-017）。
  main が確認してよい例外（確かめる中身が書式だけ）にはあたらない
- 画面そのものは変えないので、レビューの担当は入れていない
- web は画面側を受け持つ既存の定義でそのまま足りたため、モデルは上書きしなかった
- verifier には「実装担当の自己申告を鵜呑みにせず、画像を実際に開いて確かめる」
  ことと、「修正はせず報告だけ」を依頼文に明記した

## 結果

verifier が、web の「画面の表現に揃えた」という申告と実物の食い違い
（「候補の一覧」→「移調の候補の一覧」）を拾った。main が判断し、
重複する箇条書きごと外した。詳細は
[`archives/todo/TODO-110. 利用者向けの文書が、アップロード画面の変更に追従していない.md`](../../todo/TODO-110.%20利用者向けの文書が、アップロード画面の変更に追従していない.md)。
