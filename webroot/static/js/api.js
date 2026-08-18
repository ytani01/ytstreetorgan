//
// (c) 2026 Yoichi Tanibayashi
// サーバーとの JSON のやり取りと、使い回す小物。
//
// 「JSON を POST して JSON で受け取る」手順と、通信に失敗したときの
// 知らせ方が、履歴と機種設定にそれぞれ写してあったのでここにまとめる。
//
"use strict";

// document.getElementById() の短縮形。history.js / config_editor.js /
// viewer.js に 1 文字違わず散らばっていた。
window.$ = id => document.getElementById(id);

window.StorganApi = (function () {
  function postJSON(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(res => res.json());
  }

  // 通信に失敗したときの知らせ。呼ぶ側で必要な後始末（setBusy を戻す、
  // ダイアログを閉じるなど）があれば、それを済ませてから呼ぶこと。
  function reportError(err) {
    window.StorganAlert.show(`通信エラーが発生しました: ${err}`, "danger");
  }

  return { postJSON: postJSON, reportError: reportError };
})();
