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

  /* 機種セレクタに「前の画面の選択を引き継ぐ」を配線する。初期値を
     pick() で決め、change のたびに save() する。それ以上の処理
     （表示の更新など）は onChange に渡す。

     config_editor.js は change のたびに保存する場所が違う
     （loadModelIntoForm() の中）ので、これは使わない。 */
  function wire(select, onChange) {
    const names = Array.from(select.options).map(o => o.value);
    select.value = pick(names, select.value);
    select.addEventListener("change", () => {
      save(select.value);
      if (onChange) {
        onChange(select.value);
      }
    });
  }

  return { load: load, save: save, pick: pick, wire: wire };
})();
