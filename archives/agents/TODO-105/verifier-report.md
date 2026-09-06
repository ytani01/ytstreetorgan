# TODO-105 確認報告

## 1. グローバルフックの動作確認

`~/.claude/hooks/todo-count.sh` を手で実行した結果：

```json
{
  "systemMessage": "TODOに残っているのは、1 件"
}
```

**確認内容**：
- 新しいフックは `## TODO-` で始まる h2 見出しを数える（`/^## TODO-[0-9]/`）
- 旧フックは `### ` という h3 見出しを数えていた（`/^### /`）
- 現在の `TODO.md` には `## TODO-088.` が 1 つあり、`## 完了済み` より前にあるため、新フックが正しく 1 件と数える
- 旧フックは h2 見出しが無いため 0 件と数えていた（確認: `git show HEAD:.claude/settings.json` で `/^### /` を確認）

**結果**: ✓ 合っている

## 2. CLAUDE.md の 35～64 行目の実物確認

### コマンド例の実行結果

```bash
$ token-usage.py TODO-088
TODO-088 の範囲
  始点 2026-09-05 20:04:34  a12b017 docs(todo): TODO 運用をグローバルの更新に合わせる件を TODO-088 として立てる
  終点 2026-09-05 20:07:43  (まだ完了していない: 現在時刻まで)

担当             output  cache_creation    (cache_read)   msgs          $
main              7,372          11,966       1,468,230     15       $1.0
verifier          2,056          34,511         246,347      9       $0.1
...
（参考: cache_read 1,714,577、メッセージ 24 件）
```

```bash
$ token-usage.py TODO-088 --since '2026-09-05 20:00:00'
（正常に実行され、指定時刻以降のデータを集計）
```

```bash
$ token-usage.py --list
TODO       始点                 終点
TODO-088   2026-09-05 20:04:34  (未完了)
TODO-087   2026-08-14 02:27:49  2026-08-14 02:34:12
...
```

### パスと条件の確認

- ✓ `~/bin/token-usage.py` が存在し、`~/dot.files/token-usage.py` へのシンボリックリンク
- ✓ `~/dot.files/token-usage.py` に `PRICING` が定義されている（81 行目）
- ✓ `~/.claude/projects/-home-ytani-work-ytstreetorgan/` が実在し、正しく割り出される
- ✓ TODO-087 以前は `この範囲の transcript がありません。` となる（exit code 1）
- ✓ 出力の最後の行が `（参考: cache_read …）` で合致

**結果**: ✓ 合っている

## 3. .claude/settings.json 削除後の参照確認

リポジトリ内を grep した結果：

```
TODO.md:- [ ] 2. `.claude/settings.json` の SessionStart フックを削除する  （タスク本体）
TODO.md:  プロジェクトで走るのに、`.claude/settings.json` にも同じものがある  （背景説明）
archives/todo/TODO-008.md  （アーカイブの歴史記録）
archives/todo/TODO-057.md  （アーカイブの歴史記録）
archives/todo/TODO-082.md  （アーカイブの歴史記録）
```

**結果**: ✓ リポジトリ内に実装的な参照なし。アーカイブの歴史記録のみ（削除して困るものなし）

## 4. TODO.md の骨格がグローバルと合致

グローバルの形（`~/.claude/CLAUDE.md` 「TODO.md でのタスク管理」）：
- h1: `# TODO`
- 冒頭: `**残っている項目: TODO-NNN。** これまでに NNN 件を決着させた。`
- 進行中の項目: `## TODO-NNN. ...`
- 決着済み: `## 完了済み`

このリポジトリの現在の形：
```markdown
# TODO

**残っている項目: TODO-088。** これまでに 87 件を決着させた。
...

## TODO-088. TODO 運用をグローバルの更新に合わせる
...

## 完了済み
...
```

**結果**: ✓ 合っている

## 5. 決着件数の一貫性

- `TODO.md` 冒頭の表記: `これまでに 87 件を決着させた`
- `archives/todo/` のファイル数: 87 件
- `TODO.md` の「完了済み」目次のリンク数: 87 件

**結果**: ✓ すべて一致している

## まとめ

- ✓ フックが正しく 1 件と数える（旧フックの h3 問題を解決）
- ✓ `CLAUDE.md` に書いた 3 つのコマンド例が実物と合致
- ✓ パス割り出し、`PRICING` 存在、TODO-087 以前の出力確認、出力末尾の文言すべて正確
- ✓ `.claude/settings.json` 削除後に困る参照がない
- ✓ `TODO.md` の骨格がグローバルの形と完全に合致
- ✓ 決着件数 87 が全検証対象で一貫している

**指示通り直っており、書いたとおりに動く。**
