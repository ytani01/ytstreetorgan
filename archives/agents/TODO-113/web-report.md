# TODO-113 確認担当（web）報告

前回の測り直し・撮り直し（利用者の指摘で目標を約27px に下げ、`.appbar` に
`padding-block: 0;` を追加した後の状態）。**前回の測定結果・スクリーンショットは破棄し、
この内容で置き換える。**

## 確認方法

playwright（Chromium, headless）でサーバー（`uv run ytstreetorgan webapp -p 10081`）に
アクセスし、`header.appbar` の `getBoundingClientRect().height` を実測。
幅 1280px（通常）と 480px（狭い画面）、明暗テーマ、3 画面（`/` `/history` `/config`）
の組み合わせで測定した。

## 測った高さ

3 画面とも同じ `base.html` のヘッダーを使っているため、高さは画面によらず同一。

| 幅 | 変更前 | 変更後 |
|---|---|---|
| 1280px | 79.39px | **36.19px** |
| 480px（nav 折り返し） | 151.38px | 92.5px |

**狙いの「約27〜29px」には僅かに届いていないが、目標に近い値まで詰まった。**
`padding-block: 0` が効いて `header.appbar` 自身の padding は 0 になった
（確認済み: computed style で `padding: 0px`）。残る 36px は、内側の
`.appbar nav a` の高さ（font-size .84rem × line-height 1.5 ≒ 25.2px ＋
上下 padding 各 3px で計 31.2px）が、ブランド部分（27.6px）より高いため、
これが flex 行の高さを決めていることによる。27〜29px まで詰めるには、
nav リンクの `line-height` を明示的に縮めるなど追加の調整が要ると考えられる
（コードは直していない。報告のみ）。

## 見た目の確認

- **ロゴ（24×16、viewBox は 0 0 30 20 のまま）**: 4倍拡大のスクリーンショットで
  確認したが、輪郭・穴の矩形とも潰れて見えない。判読に問題なし
  （`TODO-113-logo-zoom.png`）
- **ブランド名（.92rem）・バージョン（.68rem）**: 通常表示・4倍拡大のいずれでも
  読みにくさは無い
- 1280px 幅・明暗テーマとも、ロゴ・ブランド名・バージョン・nav の見切れや
  重なりは無い。nav のホバー／`aria-current="page"` の帯も窮屈さは無い
- 480px 幅では、ブランド名が折り返して縦 3 行、nav も折り返して縦積みになり
  高さが 92.5px まで増える。変更前（151.38px）より縮んでおり、崩れは無い
- **`main` 上端の余白**: `main` 自体の `padding-top` は元々 0px で、実際の
  余白は `.wrap` の `padding: 1.15rem 1rem 1.5rem`（今回変更していない）に
  よるもの。`header` 下端から見出し（`h1`）まで約23px あり、詰まりすぎては
  いない
- 明暗テーマの切り替えでの見た目の破綻は無し

## pytest / ruff / mypy

- `uv run pytest -q` → 303 passed, 49 deselected
- `uv run ruff check src tests` → All checks passed!
- `uv run mypy src` → Success: no issues found in 18 source files

いずれも問題なし（CSS / テンプレートのみの変更のため予想どおり）。

## 比較画像

`~/tmp/playwright-mcp/TODO-113-header-before-after.png` — `git stash` で
変更前に戻してアップロード画面のヘッダー部分だけを撮り、`git stash pop` で
戻して同じ場所を撮って上下に並べたもの。`git stash` の前後で作業ツリーが
元どおりであること（`TODO.md` / `webroot/static/css/my.css` /
`webroot/templates/base.html` の変更が残っていること）は `git status` /
`git diff --stat` で確認済み。

## スクリーンショット

`~/tmp/playwright-mcp/` に保存（前回分は削除して撮り直し）。

- `TODO-113-header-upload-light.png` / `-dark.png` / `-light-narrow.png` / `-dark-narrow.png`
- `TODO-113-header-history-*.png`（同上4種）
- `TODO-113-header-config-*.png`（同上4種）
- `TODO-113-logo-zoom.png`（ロゴ拡大確認用）
- `TODO-113-main-top.png`（main 上端の余白確認用）
- `TODO-113-header-before-after.png`（変更前後の比較）

## 作業用ファイルについて

`check_header.py` はリポジトリのトップには置いておらず、常に
セッションのスクラッチパッド（`/tmp/claude-.../scratchpad/`）に作成した。
そちらはこのセッション終了で消える一時領域のため、リポジトリ側の
後始末は不要（該当ファイルはリポジトリ内に存在しない）。

## 残る懸念

- **狙いの高さ（約27〜29px）には届いていない（実測36.19px）。** 原因は
  nav リンクの line-height。詰め切るなら nav a に line-height を明示する
  追加修正が要ると考えられる（実装は別途判断）
- 480px 幅での折り返し（高さ92.5px）は今回の変更前から同じ傾向の挙動
  （変更前 151px → 変更後 92.5px、絶対値としてはまだ大きい）。
  「ヘッダーが厚い」の対象に狭い画面幅を含めるかどうかは要判断
