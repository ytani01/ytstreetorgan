//
// (c) 2026 Yoichi Tanibayashi
// ロールブックのビューア（生成結果の画面）
//
"use strict";

/* ---- ロールブックのビューア --------------------------------------------
   [!! 重要 !!] transform で拡縮しない。SVG の描画サイズそのものを変える。
   こうするとブラウザ標準のスクロールがそのまま効き、スクロールバーが
   全体の中の現在位置を示してくれる。SVG が width="…mm" で出力されている
   ので、倍率 1.0 がそのまま原寸（96dpi 換算）になる。
   汎用の panzoom ライブラリは transform ベースで、縦横比 33:1 の
   ロールブックではスクロールバーが消えて現在位置を見失うので使わない。 */
(function () {
  const box = document.getElementById("svgbox");
  const book = window.BOOK_DATA;
  if (!box || !book || !book.width || !book.height) {
    return;  // ファイル選択の画面、または寸法が取れなかったとき
  }

  const svgEl = box.querySelector("svg");
  if (!svgEl) {
    return;
  }
  // CSS で大きさを決めるので、属性の width/height は邪魔になる
  svgEl.removeAttribute("width");
  svgEl.removeAttribute("height");

  // 分からない値の出し方。サーバー（storage.UNKNOWN）から来る
  const UNKNOWN = window.UNKNOWN || "---";

  const PX_PER_MM = 96 / 25.4;
  const Z_MIN = 0.02;
  const Z_MAX = 10.0;

  const $ = id => document.getElementById(id);
  const zoomEl = $("zoom");
  const zoomVal = $("zoomval");
  const posMM = $("pos-mm");
  const posT = $("pos-t");
  const minimap = $("minimap");
  const mmwin = $("mmwin");

  let z = 0.2;

  box.style.setProperty("--book-h", book.height + "mm");

  // 倍率の刻みは対数。2% と 1000% を線形に並べると低倍率側が潰れる
  const toSlider = v => Math.round(
    100 * (Math.log(v) - Math.log(Z_MIN)) / (Math.log(Z_MAX) - Math.log(Z_MIN))
  );
  const fromSlider = s => Math.exp(
    Math.log(Z_MIN) + (s / 100) * (Math.log(Z_MAX) - Math.log(Z_MIN))
  );

  function fmtTime(sec) {
    const s = Math.max(0, Math.floor(sec));
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  }

  function update() {
    // ビューアの中央が、ブックの右端（＝曲の先頭）から何 mm の位置か。
    // padding の分は rect から求める（root の font-size で変わるため）。
    const boxRect = box.getBoundingClientRect();
    const svgRect = svgEl.getBoundingClientRect();
    const fromRightPx = svgRect.right - (boxRect.left + boxRect.width / 2);
    const mm = Math.min(
      book.width, Math.max(0, fromRightPx / (PX_PER_MM * z))
    );

    posMM.textContent = mm.toFixed(0);
    // 履歴から保存済みの SVG を出したときは mm_per_sec が分からない。
    // 秒に直せないので位置だけ出す。
    posT.textContent = book.mm_per_sec > 0
      ? fmtTime(mm / book.mm_per_sec) : UNKNOWN;

    const scrollW = Math.max(1, box.scrollWidth);
    mmwin.style.left = (box.scrollLeft / scrollW * 100) + "%";
    mmwin.style.width = (Math.min(1, box.clientWidth / scrollW) * 100) + "%";
  }

  /* 拡縮しても、基準の点（既定は表示の中央、ホイールならポインタの位置）が
     画面の同じところに残るようにする。

     [!! 重要 !!] scrollWidth に対する比で覚えてはいけない。padding は
     拡縮しないので比が倍率に対して一定にならず、はみ出していないときは
     scrollWidth が clientWidth で頭打ちになって中央へ飛ぶ。
     ブック上の位置（SVG の端から何 mm か）で覚えれば倍率と無関係に決まる。 */
  function setZoom(next, anchorX) {
    const prev = z;

    const boxRect = box.getBoundingClientRect();
    const ax = (anchorX === undefined)
      ? boxRect.left + boxRect.width / 2 : anchorX;
    const ay = boxRect.top + boxRect.height / 2;
    // 基準の点は、ブックの右端（曲の先頭）から何 mm・上端から何 mm か
    const before = svgEl.getBoundingClientRect();
    const mmX = (before.right - ax) / (PX_PER_MM * prev);
    const mmY = (ay - before.top) / (PX_PER_MM * prev);

    z = Math.min(Z_MAX, Math.max(Z_MIN, next));

    box.style.setProperty("--z", z);
    zoomEl.value = String(toSlider(z));
    zoomVal.textContent = Math.round(z * 100) + "%";

    if (prev !== z) {
      // 描画サイズが変わったあとでないと、実測しても古い値が返る
      requestAnimationFrame(() => {
        const r = svgEl.getBoundingClientRect();
        // スクロールを増やすと中身は左（上）へ動く。ずれた分だけ足す
        box.scrollLeft += (r.right - mmX * PX_PER_MM * z) - ax;
        box.scrollTop += (r.top + mmY * PX_PER_MM * z) - ay;
        update();
      });
    }
    update();
  }

  // padding は root の font-size に連動して変わるので実測する。
  // 余分に引いているのは box-shadow の分（切ると 1px 分スクロールが出る）。
  function innerSize() {
    const cs = getComputedStyle(box);
    return {
      w: box.clientWidth
        - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) - 8,
      h: box.clientHeight
        - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - 8,
    };
  }

  /* 既定はこちら。ブックの高さを画面に合わせ、あとは横スクロールで送る。
     縦横比が 33:1 なので「全体」を既定にすると細すぎて何も読めない。 */
  function fitHeight() {
    setZoom(innerSize().h / (book.height * PX_PER_MM));
    requestAnimationFrame(toStart);
  }
  function fitAll() {
    setZoom(innerSize().w / (book.width * PX_PER_MM));
    requestAnimationFrame(toStart);
  }
  /* 曲の先頭は右端（SVG の x=0 側）。だから初期表示は右端に寄せる。 */
  function toStart() {
    box.scrollLeft = box.scrollWidth;
    update();
  }

  zoomEl.addEventListener("input", () => setZoom(fromSlider(Number(zoomEl.value))));
  $("zoom-in").addEventListener("click", () => setZoom(z * 1.4));
  $("zoom-out").addEventListener("click", () => setZoom(z / 1.4));
  $("fit-height").addEventListener("click", fitHeight);
  $("fit-all").addEventListener("click", fitAll);
  $("fit-actual").addEventListener("click", () => setZoom(1));
  $("to-start").addEventListener("click", toStart);
  box.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);

  /* ---- 帯（ミニマップ）: クリックでその位置へ、ドラッグで送る ----
     枠（#mmwin = いま見えている範囲）を掴んだときだけ相対移動にする。
     掴んだ場所がずれずに付いてくるので、少しだけ動かしたいときに扱いやすい。
     枠の外を押したときは、これまで通りその位置へ飛ばしてから追従する。 */

  // 掴んだ点と表示範囲の左端との距離（box のスクロール座標）。
  // ドラッグ中は scrollWidth が変わらないので、押した時点で決めてよい。
  let mmGrab = null;

  function mmScrollTo(clientX) {
    const r = minimap.getBoundingClientRect();
    const ratio = (clientX - r.left) / Math.max(1, r.width);
    box.scrollLeft = ratio * box.scrollWidth - mmGrab;
    update();
  }

  minimap.addEventListener("pointerdown", e => {
    if (e.button !== 0) {
      return;
    }
    const r = minimap.getBoundingClientRect();
    const ratio = (e.clientX - r.left) / Math.max(1, r.width);

    if (e.target === mmwin) {
      mmGrab = ratio * box.scrollWidth - box.scrollLeft;
    } else {
      mmGrab = box.clientWidth / 2;  // 押した点が中央に来るように飛ぶ
      mmScrollTo(e.clientX);
    }

    minimap.classList.add("is-grabbing");
    minimap.setPointerCapture(e.pointerId);
    e.preventDefault();  // 帯の上での選択やスクロールの開始を止める
  });

  minimap.addEventListener("pointermove", e => {
    if (mmGrab === null) {
      return;
    }
    mmScrollTo(e.clientX);
  });

  for (const ev of ["pointerup", "pointercancel"]) {
    minimap.addEventListener(ev, () => {
      mmGrab = null;
      minimap.classList.remove("is-grabbing");
    });
  }

  /* Ctrl / ⌘ + ホイールで拡縮。素のホイールはスクロールのまま残す。 */
  box.addEventListener("wheel", e => {
    if (!e.ctrlKey && !e.metaKey) {
      return;
    }
    e.preventDefault();
    // ポインタの下にある位置を動かさない
    setZoom(z * (e.deltaY < 0 ? 1.12 : 1 / 1.12), e.clientX);
  }, { passive: false });

  /* ドラッグでのパン。長い紙を手で送る感覚に合わせる。 */
  let drag = null;
  box.addEventListener("pointerdown", e => {
    if (e.button !== 0) {
      return;
    }
    drag = { x: e.clientX, y: e.clientY, sl: box.scrollLeft, st: box.scrollTop };
    box.classList.add("is-grabbing");
    box.setPointerCapture(e.pointerId);
  });
  box.addEventListener("pointermove", e => {
    if (!drag) {
      return;
    }
    box.scrollLeft = drag.sl - (e.clientX - drag.x);
    box.scrollTop = drag.st - (e.clientY - drag.y);
  });
  for (const ev of ["pointerup", "pointercancel"]) {
    box.addEventListener(ev, () => {
      drag = null;
      box.classList.remove("is-grabbing");
    });
  }

  const durT = $("dur-t");
  if (durT) {
    durT.textContent = book.mm_per_sec > 0
      ? fmtTime(book.width / book.mm_per_sec) : UNKNOWN;
  }

  fitHeight();
})();
