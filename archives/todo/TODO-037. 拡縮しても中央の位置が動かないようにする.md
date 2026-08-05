# TODO-037. 拡縮しても中央の位置が動かないようにする

`setZoom()` の位置合わせを、`scrollWidth` に対する比から
「基準の点がブックの端から何 mm か」に変えた。

拡大すると、画面の中央に出ていた位置（`#pos-mm` の値）がずれていた。
長いブックの一か所を拡大して見たいときに、見ていた場所を見失う。

原因は位置の覚え方。`(scrollLeft + clientWidth / 2) / scrollWidth` の比で
覚えて、拡縮後に同じ比へ戻していた。これは 2 つの理由でずれる。

- `scrollWidth` には `padding`（1rem × 2）が入っていて、**そこは拡縮しない**。
  だから比は倍率に対して一定にならない
- はみ出していないときの `scrollWidth` は `clientWidth` で頭打ちになる。
  低倍率から拡大すると、比が 0.5 に潰れていて中央へ飛ぶ

## 入れたもの

`webroot/static/js/viewer.js` の `setZoom()`。倍率を変える前に基準の点の
位置を mm で実測し、変えたあとの `requestAnimationFrame` で引き戻す。

```js
const before = svgEl.getBoundingClientRect();
const mmX = (before.right - ax) / (PX_PER_MM * prev);
const mmY = (ay - before.top) / (PX_PER_MM * prev);
// …倍率を変える…
requestAnimationFrame(() => {
  const r = svgEl.getBoundingClientRect();
  box.scrollLeft += (r.right - mmX * PX_PER_MM * z) - ax;
  box.scrollTop += (r.top + mmY * PX_PER_MM * z) - ay;
});
```

- 実測（`getBoundingClientRect()`）にしたので、`padding` が
  root の `font-size` で変わっても、`box-shadow` の分があっても合う
- 縦も同じように保つ。高さ合わせから拡大すると縦にもはみ出すため
- ホイール拡縮は、比ではなく**ポインタの画面上の x 座標**を渡すようにした
  （`setZoom(z * 1.12, e.clientX)`）。基準の点の決め方が 1 本になった
- 「高さ合わせ」「全体」は、これまで通り拡縮のあと右端へ寄せる
  （`fitHeight()` が後から `requestAnimationFrame(toStart)` を積むので、
  こちらが勝つ）

## 確かめたこと

- 高さ合わせのまま曲の先頭側（`scrollWidth * 0.85`）へ寄せ、`＋` を 3 回
  押しても `#pos-mm` が動かない（誤差 1mm。表示が整数 mm なのでこれが下限）。
  `−` で戻したときも同じ
  （`tests/browser/test_rollbook_page.py::test_viewer_zoom_keeps_center`）
- 古い実装に戻すと 5mm ずれて落ちる（実際に戻して確認）
- **ブックのちょうど中央では、古い実装でも誤差が打ち消し合う。**
  テストが端寄りで測っているのはこのため
- `uv run pytest -q` / `uv run pytest -m browser -q` とも通る

---

**これは記録で、現行仕様ではない**（仕様は `CLAUDE.md` と `docs/`）。
一覧は [TODO.md](../../TODO.md) にある。
