//
// (c) 2026 Yoichi Tanibayashi
// ファイル選択の画面（アップロードと機種セレクタ）
//
// ロールブックのビューアは viewer.js。同じ画面で動くが、扱うものが
// まったく別（こちらは <form>、あちらは表示中の SVG）なので分けてある。
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
      // どちらを選んでも変換はする。違うのは「どちらのファイルを使うか」
      modalMsg.textContent =
        `${file.name} は既にアップロードされています。`
        + 'どちらのファイルで変換しますか？';
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

/* ---- 移調の候補（TODO-039）--------------------------------------------- */
// 生成結果の画面にだけ出る表。押した行の移調量で作り直す。
// 履歴からの再生成と同じ経路（stored_midi）に乗せてある。
(function () {
  const form = document.getElementById("transpose-form");
  const value = document.getElementById("transpose-value");
  if (!form || !value) {
    return;  // ファイル選択の画面と、履歴から出したときは表が無い
  }

  document.addEventListener("click", e => {
    const btn = e.target.closest("[data-transpose]");
    if (!btn) {
      return;
    }
    value.value = btn.dataset.transpose;
    form.submit();
  });
})();
