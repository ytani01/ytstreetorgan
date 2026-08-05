//
// (c) 2026 Yoichi Tanibayashi
// 履歴（アップロード済み MIDI / 生成済み SVG）の一覧
//
"use strict";

document.addEventListener("DOMContentLoaded", function () {
  const $ = id => document.getElementById(id);

  const modelSelect = $("model-select");
  const form = $("act-form");

  const LABEL = { midi: "MIDI", svg: "SVG" };

  // 知らせの出し方は alert.js（履歴と機種設定で共通）
  const showAlert = window.StorganAlert.show;

  /* ---- 機種の選択を画面間で引き継ぐ（storgan.js / config_editor.js と同じ） */

  if (modelSelect) {
    const names = Array.from(modelSelect.options).map(o => o.value);
    modelSelect.value = window.ModelStore.pick(names, modelSelect.value);

    modelSelect.addEventListener("change", () => {
      window.ModelStore.save(modelSelect.value);
    });
  }

  /* ---- 再生成 / 表示 ---------------------------------------------------- */

  // どちらも生成結果の画面を出すので、隠しフォームを submit して遷移する。
  // 使わないほうは空にしておくこと（サーバーは値のあるほうを見る）。
  function submitAct(field, name) {
    $("act-model").value = modelSelect ? modelSelect.value : "";
    $("act-midi").value = field === "midi" ? name : "";
    $("act-svg").value = field === "svg" ? name : "";
    if (modelSelect) {
      window.ModelStore.save(modelSelect.value);
    }
    form.submit();
  }

  /* ---- 削除 -------------------------------------------------------------- */

  function postDelete(payload) {
    return fetch(`${window.URL_PREFIX}/history`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(res => res.json());
  }

  function afterDelete(data, message) {
    if (data.status === "ok") {
      // 一覧はサーバーが数え直したものを使いたいので、素直に読み直す
      sessionStorage.setItem("storgan.history.msg", message);
      location.reload();
    } else {
      showAlert(`削除エラー: ${data.message}`, "danger");
    }
  }

  document.addEventListener("click", e => {
    const regen = e.target.closest("[data-regen]");
    if (regen) {
      submitAct("midi", regen.dataset.regen);
      return;
    }

    const show = e.target.closest("[data-show]");
    if (show) {
      submitAct("svg", show.dataset.show);
      return;
    }

    const del = e.target.closest("[data-del]");
    if (del) {
      const kind = del.dataset.del;
      const name = del.dataset.name;
      if (!confirm(`${name} を削除しますか？`)) {
        return;
      }
      postDelete({ kind: kind, name: name })
        .then(data => afterDelete(data, `${name} を削除しました。`))
        .catch(err => showAlert(`通信エラーが発生しました: ${err}`, "danger"));
      return;
    }

    const delAll = e.target.closest("[data-del-all]");
    if (delAll) {
      const kind = delAll.dataset.delAll;
      if (!confirm(`${LABEL[kind]} をすべて削除しますか？`)) {
        return;
      }
      postDelete({ kind: kind, all: true })
        .then(data => afterDelete(
          data, `${LABEL[kind]} を ${data.removed} 件削除しました。`
        ))
        .catch(err => showAlert(`通信エラーが発生しました: ${err}`, "danger"));
    }
  });

  /* ---- 読み直したあとの知らせ ------------------------------------------ */

  const msg = sessionStorage.getItem("storgan.history.msg");
  if (msg) {
    sessionStorage.removeItem("storgan.history.msg");
    showAlert(msg, "success");
  }
});
