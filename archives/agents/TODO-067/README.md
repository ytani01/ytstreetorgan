# TODO-067 で使ったサブエージェントの定義

TODO-067（設定項目 `base_note` を廃止する）を役割分担して進めたときの、
Claude Code のサブエージェントの定義。

**現行の設定ではない。** 定義として効くのは `.claude/agents/*.md` に
置いてあるときだけで、ここにあるものは「このとき何をどう分担したか」の
記録。使い回すなら `.claude/agents/` へ複製する（**Claude Code は
起動時にしか読まないので、置いたら一度再起動が要る**）。

## 分担

| 名前 | モデル / effort | 担当 |
|---|---|---|
| `core` | Opus / high | `conf.py`・`rollbook.py`・`transpose.py`・`apps.py`。`note_offsets()` の廃止と打ち消し合いの解消 |
| `web` | Sonnet / medium | `config_editor.html`+`.js` の「基準の音」欄削除、`storgan.js` の諸元一覧 |
| `tests` | Sonnet / medium | テスト 5 ファイルの追従（`base_note` が 32 か所）、`pytest` / `ruff` / `mypy` の実行 |
| `docs` | Sonnet / low | 設定 JSON 2 つと `CLAUDE.md` の追従 |

**Opus は `core` にだけ充てた。** 打ち消し合いを解消するとき、
`model_note_range()` が `notes` の空のときに何を返すか（旧 `(base_note,
base_note)`）を決める必要があり、そこだけ判断が要ったため。残る 3 つは
「消して追従する」だけで判断の余地が小さいので Sonnet にしてある
（トークンを減らすため）。

## 進め方

`core` → （`web` と `docs` を並列）→ `tests` の順に動かした。

- `web` / `docs` は `core` が関数の形を変えたあとでないと追従できない
- `tests` を最後の 1 体にしたのは、他の担当が並行して直している最中に
  テストを回すと、結果が誰の未追従によるものか分からなくなるため

触ってよいファイルを担当ごとに区切った（`core` は `src/` だけ、`web` は
`webroot/` だけ、というように）ので、並列でも衝突しなかった。

決着の内容は
[TODO-067](../../todo/TODO-067.%20設定項目%20base_note%20を廃止する.md)。
