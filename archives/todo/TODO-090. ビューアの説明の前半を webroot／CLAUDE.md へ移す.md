# TODO-090. ビューアの説明の前半を `webroot/CLAUDE.md` へ移す

- [x] `CLAUDE.md` 264〜281 行を `webroot/CLAUDE.md` へ移す
- [x] 移した先の節の並びと見出しを、`webroot/CLAUDE.md` の他の節に揃える
- [x] ルートの `CLAUDE.md` に残る後半が、単独で読めるか確かめる

モデル / effort: Sonnet 5 / low

## きっかけ

`/doctor`（Claude Code の健康診断）で見つかった。診断そのものは
おおむね健全で、直す価値があったのはこの 1 件だけ。

ルートの `CLAUDE.md` は 23,146 文字あり、**すべてのセッションで
読み込まれる**。「ロールブックのビューア」の節のうち前半は、
transform で拡縮しない理由・panzoom を使わない理由・初期表示の位置・
拡縮の位置合わせという、**ブラウザ側だけの話**で、`webroot/` を
触らないときには要らなかった。

`CLAUDE.md` には既に「フロントエンド / 確認の出し方」という節があり、
`webroot/CLAUDE.md` へ委ねる形になっている。同じやり方に揃えた。

## 決めたこと

- **後半（`window.BOOK_DATA` の受け渡し以降）は移さない。**
  ブックの諸元の受け渡し、`RollBook.svg()` が埋める属性、
  `Handler1._book_of()` と `storage.book_from_svg()` の 2 か所を
  直すこと、穴の数え方 — ここは Python 側も絡むので、`src/` を
  触るときに読めないと困る
- 両方の節に相互の参照を 1 行ずつ置いた。ルート側は
  「作りは `webroot/CLAUDE.md` にある」、`webroot/` 側は
  「諸元を組み立てているのは Python 側で、ルートの `CLAUDE.md` にある」
- `webroot/CLAUDE.md` の冒頭が「ロールブックのビューアの作りは
  ルートの `CLAUDE.md` にある」と書いていたので、そこも直した
- 置き場所は「ロールブックの見え方（画面だけ）」の直前。
  ロールブックの表示まわりが隣り合う
- **`DOCTOR.md`（診断の全文）は追跡しない。** `/doctor` を回すたびに
  上書きされる作業メモなので、`.gitignore` に足した

## やったこと

- `CLAUDE.md` の「ロールブックのビューア」前半（18 行）を
  `webroot/CLAUDE.md` の新しい節「ロールブックのビューア」へ移した
- ルート側に残した後半の書き出しを、箇条書きから地の文に直した
  （並んでいた 2 項目が無くなったため）
- `webroot/CLAUDE.md` の冒頭の案内を直した
- `.gitignore` に `DOCTOR.md` を足した

`CLAUDE.md` は 23,146 → 21,898 文字（-1,248 文字。約 310 トークン）。
`webroot/CLAUDE.md` は 11,589 → 13,246 文字。

## テスト

文書だけの変更だが、決まりどおり通した。

```
uv run pytest -q            # 303 passed, 49 deselected
uv run ruff check src tests # All checks passed!
uv run mypy src             # Success: no issues found in 19 source files
```
