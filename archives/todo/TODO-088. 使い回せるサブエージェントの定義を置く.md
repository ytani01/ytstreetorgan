# TODO-088. 使い回せるサブエージェントの定義を `.claude/agents/` に置く

作成: 2026-08-19
決着: 2026-08-19

## きっかけ

サブエージェントを使ったのは TODO-063 と TODO-067 の 2 回で、どちらも
その項目のためだけに定義を書き、済んだら `archives/agents/TODO-NNN/` へ
移していた。`.claude/agents/` は空のままで、次の項目でまた書き起こす形に
なっていた。

## やったこと

`archives/todo/` の TODO-001〜087 と、`archives/agents/` の 2 組を読み、
繰り返し出てくる役割を 5 つに分けて `.claude/agents/` に置いた。

| 名前 | モデル / effort | 触ってよいもの | ツール上限 |
|---|---|---|---|
| `core` | Opus / high | `src/ytstreetorgan/*.py`、`pyproject.toml` | 60 |
| `web` | Sonnet / medium | `webroot/templates/`、`webroot/static/` | 50 |
| `tests` | Sonnet / medium | `tests/` | 50 |
| `docs` | Sonnet / low | `CLAUDE.md`、`docs/`、`README.md`、`conf/*.json` | 30 |
| `survey` | Sonnet / medium | （読むだけ。変更しない） | 40 |

役割の切り分けは、過去の項目の内訳から決めた。Python の書き換え
（TODO-043 / 070 / 072〜078 ほか）、画面（TODO-011 / 012 / 029 / 033〜037 /
049〜056 / 064 / 068 / 069 / 084 ほか）、テスト（TODO-014 / 028 / 081）、
文書と設定 JSON（TODO-004 / 057 / 066 / 079 / 080 / 087）が繰り返し出てくる。
5 つ目の `survey` は、TODO-079 / 087 のような「文書と実装の食い違いを
洗い出す」作業が調査だけで完結するため、読み取り専用の担当として分けた。

各定義に次の 5 つを書いた。

1. `model:` と `effort:`
2. 触ってよいファイルと、触ってはいけないもの（`TODO.md` と `archives/`、
   git のコミットは全員が触らない）
3. ツール呼び出しの上限回数と、使い切ったときの振る舞い
   （そこで作業をやめ、残りを報告する）
4. 進め方（このリポジトリの決めごとのうち、その役割が破りやすいもの）
5. **報告を書く直前に、決めごとのファイルを読み直すこと**

5 の読み直し先は役割ごとに変えた。`core` は `CLAUDE.md` と
`tests/CLAUDE.md`、`web` は `CLAUDE.md` と `webroot/CLAUDE.md`、
`tests` は `tests/CLAUDE.md` と `docs/Developer.md`、`docs` と `survey` は
`CLAUDE.md`。読み直しのぶんの呼び出し回数を上限から残すよう書いてある。

### 決めたこと

- **`web` だけ `tools:` を書いていない。** ブラウザで開いて確かめるのに
  `mcp__claude-in-chrome__*` が要るため。残る 4 つは絞ってある
  （`survey` は `Bash, Read, Glob, Grep` で、`Bash` も読み取りだけと明記）
- **`web` の既定は Sonnet。** 設計の判断が要る画面のときは、呼び出し側で
  モデルを Opus に差し替える（TODO-063 の `ui-dev` は Opus だった）。
  その旨を定義の中に書いてある
- **これらは `.claude/agents/` に残す。** `archives/agents/` へは移さない。
  現行の設定であり、使い回すために作ったものなので
- **一覧の文書は作らなかった。** TODO-061 で作った
  `docs/routine_verification_subagents.md` が実態と食い違って TODO-080 で
  削除になっており、同じことになるため。どういう役割があるかは各定義の
  `description:` に書いてある

## テスト

無し（エージェントの定義ファイルだけで、コードは変更していない）。
frontmatter が読めること（`name` / `model` / `effort` / `tools`）と、
定義が参照する `CLAUDE.md` / `webroot/CLAUDE.md` / `tests/CLAUDE.md` /
`docs/Developer.md` が実在することは確かめた。

**Claude Code は起動時にしか `.claude/agents/` を読まない。** 使うには
一度再起動が要る。
