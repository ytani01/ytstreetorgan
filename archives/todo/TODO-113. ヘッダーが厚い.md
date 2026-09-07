# TODO-113. ヘッダーが厚い

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | main + web |
| 実施 | Opus 5 / effort high | main + web |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 11,023 | 22,055 | 51% |
| web | Sonnet 5 | medium | 5,167 | 99,708 | 49% |
| 合計 |  |  | 16,190 | 121,763 | 概算 $2.6 |

- web は定義（`.claude/agents/web.md`）のまま。CSS の値を詰めるだけで設計の
  判断は要らないので、opus への差し替えはしていない

## きっかけ

ヘッダーが厚く、画面の上を余分に使っていた。

## やったこと

`webroot/static/css/my.css` と `webroot/templates/base.html` を変えた。

- `.appbar` に `padding-block: 0` を足した
- `.appbar__inner` の padding を `.2rem 1rem` → `.1rem 1rem`
- `.appbar nav a` の padding を `.35rem .8rem` → `.15rem .7rem`、
  font-size を `.88rem` → `.84rem`
- `.brand__name` の font-size を `1rem` → `.92rem`
- ロゴ SVG の width/height を `30x20` → `24x16`（viewBox は `0 0 30 20` のまま）

**高さの大半は Pico.css の `header,body>main{padding-block:var(--pico-block-spacing-vertical)}`
だった。** 着手時は `.appbar__inner` と nav リンクの padding が効いていると
見込んで、その 2 つだけを詰めた。だが web の実測では 79.39px → 71.39px にしか
ならず、原因が Pico 側にあることが分かった。`.appbar` で打ち消したうえで、
ロゴと文字の大きさも下げた。

**途中で目標を変えている。** 最初は「印象を変えずに数 px 詰める」つもりで
padding だけを詰めたが、利用者が比較して「違いがあまり分からない」と言ったので、
ロゴと文字の大きさも下げる案に切り替えた。もっとも、そのとき見えていた差が
小さかったのは、上の見込み違いで実際にはほとんど詰まっていなかったため。

## 確かめたこと

web が playwright（Chromium, headless）で実測した。報告は
[`archives/agents/TODO-113/web-report.md`](../agents/TODO-113/web-report.md)。

- ヘッダーの高さ: 79.39px → **36.19px**（幅 1280px）。
  幅 480px（nav が折り返す）でも 151.38px → 92.5px
- 3 画面（アップロード / 履歴 / 機種設定）× 明暗テーマ × 幅 1280/480px で
  見切れ・重なり・崩れなし
- ロゴを 4 倍に拡大しても輪郭と穴の矩形は潰れていない。ブランド名（.92rem）と
  バージョン（.68rem）も読める
- `main` 上端の余白は変わっていない（`body>main` 側の padding-block は
  残してある。実際の余白は `.wrap` が作っている）
- `uv run pytest -q` → 303 passed, 49 deselected /
  `uv run ruff check src tests` → 通過 / `uv run mypy src` → 通過

## 分担の振り返り

- **web が見つけたのは、高さの大半が Pico.css の `padding-block` だという
  こと。** これが無ければ、8px しか詰まっていないものを「約 31px になった」と
  報告して終わっていた。実際、main はスクリーンショットを見て「約 32px」と
  読み違えており、目で見るだけでは捕まえられなかった
- **見込みと食い違ったのは、main が CSS を読んだだけで実測しなかったため。**
  自前の CSS（`my.css`）しか見ておらず、Pico の既定と重なることを勘定に
  入れていなかった。「どの宣言が効いているか」は読むだけでは決まらない
- **次に寸法を詰める項目をやるなら、項目を立てる前に現状の実測を頼む。**
  今回は「37px を 31px に」という数字を根拠なく書いた項目を立ててしまい、
  立て直し（目標の変更と原因の追記）が 2 回発生した。measure 用の 1 往復を
  先に入れるほうが、やり直しより安い。編成そのもの（main + web）は
  変えなくてよい

## 残ること

狙いの 27〜29px には届いていない。残る高さは nav リンクの line-height
（`.84rem × 1.5 ≒ 25.2px`）が決めており、詰めるなら `line-height` を
明示することになる。36px で十分として、ここで止めた
（これ以上詰めるとリンクの当たり判定が小さくなる）。
