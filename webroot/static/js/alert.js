//
// (c) 2026 Yoichi Tanibayashi
// 画面上部の知らせ（成功 / 失敗 / 注意）
//
// 履歴と機種設定で同じものを出す。かつては両方に 1 文字違わない
// showAlert() が置いてあった。
//
"use strict";

window.StorganAlert = (function () {
  const CLASS = {
    success: "alert--ok",
    danger: "alert--error",
    warning: "alert--warn",
  };

  /**
   * 知らせを 1 件出す（前のものは消える）。
   *
   * @param {string} message 出す文章
   * @param {string} [type] "success" | "danger" | "warning"
   * @param {string} [boxId] 置き場の id。既定は "alert-container"
   */
  function show(message, type = "success", boxId = "alert-container") {
    const box = document.getElementById(boxId);
    if (!box) {
      return;
    }

    const div = document.createElement("div");
    div.className = `alert ${CLASS[type] || CLASS.warning}`;
    // 成功は読み上げを割り込ませない。失敗と注意は割り込ませる
    div.setAttribute("role", type === "success" ? "status" : "alert");
    div.textContent = message;

    box.replaceChildren(div);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return { show: show };
})();
