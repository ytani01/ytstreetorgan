//
// (c) 2026 Yoichi Tanibayashi
// 移調の候補を試聴する（TODO-063）
//
// 表の行の「試聴」を押すと、その行の音を <midi-player> に読み込む。
// **鳴る音を決めるのはサーバー側**（/audition/midi/…）。ここでは音階の
// 判定を一切しない（note2scale() を JS に複製すると、同じ手順を 2 か所に
// 持つことになる）。
//
// **URL は組み立てない。** テンプレートが data-audition に丸ごと書いて
// いるので、それを src へ写すだけ。
//
"use strict";

(function () {
  const player = document.getElementById("audition-player");
  const table = document.getElementById("transpose-table");
  if (!player || !table) {
    return;  // ファイル選択の画面と、履歴から出したときは表が無い
  }

  document.addEventListener("click", e => {
    // data-transpose ではなく data-audition。前者は storgan.js が拾って
    // ロールブックの作り直しに行ってしまう
    const btn = e.target.closest("[data-audition]");
    if (!btn) {
      return;
    }

    // 前の候補が鳴っている途中で差し替えると、鳴らしたまま音が変わる。
    // 聴き比べるものなので、いったん止めて頭から出せるようにする
    player.stop();
    player.src = btn.dataset.audition;

    // どの行を読み込んだのかを残す。表の行はどれも似た数字が並ぶので、
    // 印が無いと今どれを聴いているのか分からなくなる
    for (const tr of table.querySelectorAll("tr.is-audition")) {
      tr.classList.remove("is-audition");
    }
    const row = btn.closest("tr");
    if (row) {
      row.classList.add("is-audition");
    }
  });
})();
