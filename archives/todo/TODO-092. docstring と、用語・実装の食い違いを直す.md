# TODO-092. docstring と、用語・実装の食い違いを直す

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5 / effort medium | verifier |
| 実施 | Opus 5 / effort high | verifier |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 5,026 | 10,807 | 82% |
| verifier | Haiku 4.5 | 記載なし | 5,563 | 31,557 | 18% |
| 合計 |  |  | 10,589 | 42,364 | 概算 $0.7 |

- verifier は定義のモデル（`haiku`）のまま。docstring と実装を突き合わせる
  だけで、判断が要らない
- 定義に `effort` の行は無い（Haiku は effort 非対応）
- main は見込みの Sonnet 5 ではなく Opus 5 で動いた（利用者の設定）
- 対象箇所の下調べは TODO-091 の待ち時間に済ませたので、そのぶんは
  TODO-091 側の数字に入っている

分担の理由と報告は `archives/agents/TODO-092/` にある。

## きっかけ

TODO-089 で `docs/User.md` を書いたときに見つけた 2 件。どちらも
docstring だけの話で、挙動には関係しない。

## やったこと

**挙動は変えていない。** docstring を 2 か所直しただけ。

- **`apps.py` の `MidiApp.__init__`。** `sec_min` / `sec_max` の説明を
  「音の長さの下限・上限 [秒]」から
  **「1 音を鳴らす時間の下限・上限 [秒]」**に変えた。
  `CLAUDE.md`「画面に出す用語」の「音の長さ」は**移調の候補で使う割合**を
  指す語なので、1 音あたりの再生時間に同じ語を使うとかぶる。
  `docs/User.md` の `--min` / `--max` の説明と同じ言い方に揃えた
- **`handler1.py` の `_show_stored_svg()`。** 「穴の数と `mm_per_sec` は
  SVG に無いので None」という説明が古かった。TODO-026 で図から求まらない
  値を `<svg>` の属性に埋めるようにしてから、`storage.book_from_svg()` が
  それを読んでいる。**「寸法と穴の数は図そのものから、`mm_per_sec` の
  ように図に現れない値は `<svg>` の属性から読む。属性が無い古い SVG では
  None のままで、画面に `---` と出る」**に直した

`transpose.py` の「音の長さ」は移調の候補の割合を指していて正しい用法
なので、触っていない。

## テスト

- `uv run pytest -q` — 303 passed, 49 deselected
- `uv run ruff check src tests` — All checks passed
- `uv run mypy src` — Success: no issues found in 18 source files

verifier に、書いた説明が実装と合っているかも確かめさせた。

- `sec_min` / `sec_max` が `Player.play()` に渡り、1 音を鳴らす時間を
  決めていること。`docs/User.md` 326 行の説明と一致していること
- `book_from_svg()` が、寸法を `<svg>` の `width` / `height` から、
  穴の数を描かれている穴と破線から数え、`mm_per_sec` を属性
  （`mm-per-sec`）から読んでいること
- 属性が無いと None になり、`viewer.js` の `UNKNOWN`（`---`）で表示される
  こと

指摘は 1 件。最初の書き方「`width` / `height` と穴の数は図から数え」だと、
**寸法まで「数える」ことになって不正確**（寸法は属性から読むだけ）。
「寸法と穴の数は図そのものから」に直した。

## 分担の振り返り

- **verifier が見つけたのは 1 件**（「数える」が寸法にもかかっていた）。
  実装との食い違いは無かった。書いた本人には、自分の文が両方に
  かかって読めることが見えにくい
- **見込みとの食い違いは main のモデルだけ**（Sonnet 5 の見込みが
  Opus 5 になった）。担当は見込みどおり verifier 1 人
- **次に同じ規模の項目をやるなら、同じ組み方でよい。** docstring だけの
  項目でも、書いた説明が実装と合っているかを突き合わせる相手が要る。
  モデルは Haiku で足りた。verifier の指摘を受けた直しは表現の言い換え
  だけだったので、2 回目の verifier は立てず main が `pytest` /
  `ruff` / `mypy` を回して済ませた
