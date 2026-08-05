# TODO-049. 「高さ合わせ」「全体」で見ている位置を保つ

## きっかけ

ビューアで「高さ合わせ」を押すと、曲の先頭（右端）へ飛んでいた。
長い曲の途中を見ているときに、倍率だけ直したいのに位置を見失う。

## 直したこと

`webroot/static/js/viewer.js`

- `fitHeight()` / `fitAll()` から `requestAnimationFrame(toStart)` を削除。
  倍率を変えるだけにして、位置は `setZoom()` の保持（TODO-037）に任せる
- 初期表示は右端のまま。末尾の `fitHeight()` の直後に
  `requestAnimationFrame(toStart)` を置いた。`setZoom()` も rAF で
  位置を戻すので、あとから登録したこちらが後に走る

これで拡縮系の操作（+ / − / スライダー / 原寸 / ホイール / 高さ合わせ /
全体）がすべて位置を保つようになり、揃った。

## テスト

`tests/browser/test_rollbook_page.py::test_fit_height_keeps_position`

拡大して途中へスクロールしてから「高さ合わせ」を押し、`#pos-mm` が
変わらないことを見る。**先に `zoom-in` しておくのが要点**で、
既に高さ合わせの倍率だと `setZoom()` の `prev !== z` が偽になり、
何も起きないまま通ってしまう。

「全体」は横にはみ出さなくなる＝必ずブックの中央が映るので、
位置の保持を確かめる意味が無い。テストしていない。

初期表示が右端であることは
`test_viewer_starts_at_the_beginning_of_the_song` が元から見ている。
