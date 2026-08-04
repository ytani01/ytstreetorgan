//
// (c) 2026 Yoichi Tanibayashi
// メイン画面（ファイル選択 / ロールブックのビューア）
//
"use strict";

/* ---- アップロード ------------------------------------------------------ */
// 機種セレクタとは別に持つ。機種が 1 つも無いとセレクタは描画されないが、
// ファイル選択はできてしまうため。
(function () {
  const input = document.getElementById("file1");
  if (!input) {
    return;  // 生成結果の画面にはフォームが無い
  }

  const status = document.getElementById("drop-status");
  const overwrite = document.getElementById("overwrite");
  const reuse = document.getElementById("reuse");
  const modal = document.getElementById("same-name-modal");
  const modalMsg = document.getElementById("same-name-msg");
  const limit = window.SIZE_LIMIT || 0;
  const uploaded = window.UPLOADED_NAMES || [];

  function setStatus(text, isError) {
    if (!status) {
      return;
    }
    status.textContent = text;
    status.classList.toggle("drop__status--error", Boolean(isError));
  }

  /* 選び直せるように戻す。同じファイルをもう一度選んでも change が出る */
  function reset() {
    input.value = "";
  }

  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) {
      return;
    }

    // 上限を超えたら送らない。送ると tornado が本文を読まずに接続を切るので、
    // ブラウザには真っ白なページが残り、理由が何も伝わらない。
    if (limit && file.size > limit) {
      setStatus(
        `${file.name} は大きすぎます（上限 ${window.SIZE_LIMIT_TEXT}）。`, true
      );
      reset();
      return;
    }

    // 同じ名前が既にあるなら訊く。黙って上書きすると、直したつもりの
    // ファイルなのか前のままなのかが画面から分からない。
    // 送るかどうかはダイアログのボタンが決める（下の close ハンドラ）。
    if (uploaded.includes(file.name)) {
      modalMsg.textContent =
        `${file.name} は既にアップロードされています。どうしますか？`;
      modal.showModal();
      return;
    }

    input.form.submit();
  });

  /* ---- 同名だったときの 3 択 ---- */

  // ESC や ✕ で閉じた場合も「キャンセル」と同じ扱いにしたいので、
  // 選ばれたものを覚えてから閉じ、close イベント 1 か所で処理する。
  let choice = "";

  function closeWith(next) {
    choice = next;
    modal.close();
  }

  modal.addEventListener("close", () => {
    const chosen = choice;
    choice = "";

    if (chosen === "replace") {
      overwrite.value = "1";
    } else if (chosen === "reuse") {
      reuse.value = "1";
    } else {
      setStatus("そのままにしました。", false);
      reset();
      return;
    }
    input.form.submit();
  });

  document.getElementById("btn-same-replace")
    .addEventListener("click", () => closeWith("replace"));
  document.getElementById("btn-same-reuse")
    .addEventListener("click", () => closeWith("reuse"));
  for (const id of ["btn-same-cancel", "btn-same-close"]) {
    document.getElementById(id)
      .addEventListener("click", () => closeWith(""));
  }
})();

(function () {
  const select = document.getElementById("model");
  const specs = document.getElementById("specs");
  if (!select || !specs) {
    return;  // 生成結果の画面には機種セレクタが無い
  }

  const models = window.MODELS_DATA || [];

  function num(v, digits) {
    return typeof v === "number" ? v.toFixed(digits) : "—";
  }

  // 選んだ機種の寸法を先に見せる。生成してから気づくのを避けるため
  function updateSpecs(name) {
    const m = models.find(d => d.model === name);
    if (!m) {
      specs.replaceChildren();
      return;
    }
    const items = [
      ["ブック高さ", num(m["book_height"], 1), " mm"],
      ["トラック数", (m["notes"] || []).length, ""],
      ["ピッチ", num(m["pitch"], 1), " mm"],
      ["送り速度", num(m["mm_per_sec"], 0), " mm/秒"],
      ["基準の音", m["base_note"], ""],
    ];
    specs.replaceChildren(...items.map(([label, value, unit]) => {
      const div = document.createElement("div");
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.append(String(value));
      if (unit) {
        const small = document.createElement("small");
        small.textContent = unit;
        dd.append(small);
      }
      div.append(dt, dd);
      return div;
    }));
  }

  // 前の画面で選んだ機種を引き継ぐ（無ければサーバーが出した既定のまま）
  const names = Array.from(select.options).map(o => o.value);
  select.value = window.ModelStore.pick(names, select.value);

  select.addEventListener("change", () => {
    window.ModelStore.save(select.value);
    updateSpecs(select.value);
  });
  updateSpecs(select.value);
})();

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

  // 分からない値の出し方。テンプレート側の表記と合わせること
  const UNKNOWN = "---";

  const PX_PER_MM = 96 / 25.4;
  const Z_MIN = 0.02;
  const Z_MAX = 5.0;

  const $ = id => document.getElementById(id);
  const zoomEl = $("zoom");
  const zoomVal = $("zoomval");
  const posMM = $("pos-mm");
  const posT = $("pos-t");
  const minimap = $("minimap");
  const mmwin = $("mmwin");

  let z = 0.2;

  box.style.setProperty("--book-h", book.height + "mm");

  // 倍率の刻みは対数。2% と 500% を線形に並べると低倍率側が潰れる
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

  function setZoom(next, anchorRatio) {
    const prev = z;
    z = Math.min(Z_MAX, Math.max(Z_MIN, next));

    const ratio = (anchorRatio === undefined)
      ? (box.scrollLeft + box.clientWidth / 2) / Math.max(1, box.scrollWidth)
      : anchorRatio;

    box.style.setProperty("--z", z);
    zoomEl.value = String(toSlider(z));
    zoomVal.textContent = Math.round(z * 100) + "%";

    if (prev !== z) {
      // 描画サイズが変わったあとでないと scrollWidth が古い
      requestAnimationFrame(() => {
        box.scrollLeft = ratio * box.scrollWidth - box.clientWidth / 2;
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

  minimap.addEventListener("click", e => {
    const r = minimap.getBoundingClientRect();
    box.scrollLeft =
      (e.clientX - r.left) / r.width * box.scrollWidth - box.clientWidth / 2;
    update();
  });

  /* Ctrl / ⌘ + ホイールで拡縮。素のホイールはスクロールのまま残す。 */
  box.addEventListener("wheel", e => {
    if (!e.ctrlKey && !e.metaKey) {
      return;
    }
    e.preventDefault();
    const r = box.getBoundingClientRect();
    const anchor =
      (box.scrollLeft + (e.clientX - r.left)) / Math.max(1, box.scrollWidth);
    setZoom(z * (e.deltaY < 0 ? 1.12 : 1 / 1.12), anchor);
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
