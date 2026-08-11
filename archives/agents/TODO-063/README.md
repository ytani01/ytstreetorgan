# TODO-063 で使ったサブエージェントの定義

TODO-063（ブラウザ上で、実機で鳴る音だけを試聴できるようにする）を
役割分担して進めたときの、Claude Code のサブエージェントの定義。

**現行の設定ではない。** 定義として効くのは `.claude/agents/*.md` に
置いてあるときだけで、ここにあるものは「このとき何をどう分担したか」の
記録。使い回すなら `.claude/agents/` へ複製する（**Claude Code は
起動時にしか読まないので、置いたら一度再起動が要る**）。

## 分担

| 名前 | モデル / effort | 担当した区切り |
|---|---|---|
| `core-dev` | Opus / high | A。`rollbook.py` の継ぎ目、`audition.py`、`AuditionMidi`、テスト |
| `vendor-fetch` | Sonnet / low | B の頭。同梱 3 本の取得とサイズ照合、`LICENSES.md` |
| `ui-dev` | Opus / medium | B。試聴列、`<midi-player>`、`midi_audition.js`、`my.css` |
| `qa-browser` | Sonnet / high | C。`tests/browser/` の追加と、静的検査を通すこと |
| `docs-scribe` | Sonnet / low | C。`docs/tech-stack.md`、`webroot/CLAUDE.md`、ルートの `CLAUDE.md` |

**Opus は設計の判断が要る A と B にだけ充てた。** 取得・テストの実行・
文書は、やることが決まっていて判断の余地が小さいので Sonnet にしてある
（トークンを減らすため）。

決着の内容は
[TODO-063](../../todo/TODO-063.%20ブラウザ上で、実機で鳴る音だけを試聴できるようにする.md)。
