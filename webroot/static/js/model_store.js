//
// (c) 2026 Yoichi Tanibayashi
// 選択中の機種を画面間で受け継ぐ（ロールブック作成 ⇔ 機種設定）。
//
// サーバーには持たせない。「今どの機種を触っているか」は端末ごとの状態で
// しかなく、設定ファイルに書き戻すものでもないため localStorage で足りる。
//
"use strict";

window.ModelStore = (function () {
  const KEY = "storgan.model";

  function load() {
    try {
      return window.localStorage.getItem(KEY) || "";
    } catch (e) {
      return "";  // localStorage が使えない設定でも動くこと
    }
  }

  function save(name) {
    try {
      window.localStorage.setItem(KEY, name);
    } catch (e) {
      // 受け継げなくなるだけなので、黙って諦める
    }
  }

  /* 覚えている機種を返す。ただし機種設定側で削除・改名されていることが
     あるので、今ある機種に無ければ fallback にする。 */
  function pick(names, fallback) {
    const saved = load();
    return names.indexOf(saved) >= 0 ? saved : fallback;
  }

  return { load: load, save: save, pick: pick };
})();
