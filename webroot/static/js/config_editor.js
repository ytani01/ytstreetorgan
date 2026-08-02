//
// (c) 2026 Yoichi Tanibayashi
// 機種設定エディタ
//
// jQuery / Bootstrap には依存しない（CDN を読まずに動くこと）。
// モーダルは Pico がそのまま面倒を見てくれる <dialog> を使う。
//
"use strict";

document.addEventListener("DOMContentLoaded", function () {
  let confData = window.INITIAL_CONF_DATA || [];
  let currentModel = "";

  const $ = id => document.getElementById(id);

  const alertBox = $("alert-container");
  const modelSelect = $("model-select");
  const copySelect = $("copy-from-model");
  const noteBody = $("note-table-body");
  const noteBadge = $("note-count-badge");
  const saveBtn = $("btn-save-config");
  const dialog = $("addModelModal");
  const newNameInput = $("new-model-name");
  const addError = $("add-model-error");

  // 入力欄の id と、設定ファイル上のキーの対応。
  // キーは生の JSON フィールド名（空白や数字始まりを含む）。
  const FIELDS = {
    "field-model": "model",
    "field-book-height": "book height",
    "field-margin": "margin",
    "field-pitch": "pitch",
    "field-hole-height": "hole height",
    "field-1sec": "1sec",
    "field-base-note": "base note",
    "field-bridge-width": "bridge width",
    "field-bridge-threshold": "bridge threshold",
    "field-memo": "memo",
  };

  const NUMERIC = {
    "book height": parseFloat,
    "margin": parseFloat,
    "pitch": parseFloat,
    "hole height": parseFloat,
    "1sec": parseFloat,
    "base note": v => parseInt(v, 10),
    "bridge width": parseFloat,
    "bridge threshold": parseFloat,
  };

  /* ---- 通知 ------------------------------------------------------------ */

  function showAlert(message, type = "success") {
    const cls = {
      success: "alert--ok",
      danger: "alert--error",
      warning: "alert--warn",
    }[type] || "alert--warn";

    const div = document.createElement("div");
    div.className = `alert ${cls}`;
    div.setAttribute("role", type === "success" ? "status" : "alert");
    div.textContent = message;
    alertBox.replaceChildren(div);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* ---- 描画 ------------------------------------------------------------ */

  function getModelConfig(modelName) {
    return confData.find(d => d.model === modelName) || null;
  }

  function fillSelect(select, selected) {
    select.replaceChildren(...confData.map(d => {
      const opt = document.createElement("option");
      opt.value = d.model;
      opt.textContent = d.model;
      opt.selected = d.model === selected;
      return opt;
    }));
  }

  function renderModelSelect(selectModel) {
    fillSelect(modelSelect, selectModel);
    fillSelect(copySelect, selectModel);
  }

  function makeInput(cls, type, value, label) {
    const input = document.createElement("input");
    input.type = type;
    input.className = cls;
    input.value = value;
    input.required = true;
    input.setAttribute("aria-label", label);
    return input;
  }

  function appendNoteRow(idx, name = "", offset = 0) {
    const tr = document.createElement("tr");
    tr.className = "note-row";

    const tdNum = document.createElement("td");
    tdNum.className = "track-num";
    tdNum.textContent = String(idx);

    const tdName = document.createElement("td");
    tdName.append(
      makeInput("note-name-input", "text", name, `トラック ${idx} の音名`)
    );

    const tdOffset = document.createElement("td");
    tdOffset.append(
      makeInput(
        "note-offset-input", "number", offset, `トラック ${idx} のオフセット`
      )
    );

    const tdDel = document.createElement("td");
    tdDel.style.textAlign = "center";
    const del = document.createElement("button");
    del.type = "button";
    del.className = "btn-row btn-delete-row";
    del.textContent = "✕";
    del.title = "この行を削除";
    del.setAttribute("aria-label", `トラック ${idx} を削除`);
    tdDel.append(del);

    tr.append(tdNum, tdName, tdOffset, tdDel);
    noteBody.append(tr);
  }

  function noteRows() {
    return noteBody.querySelectorAll("tr.note-row");
  }

  function renderNoteTable(noteNames, noteOffsets) {
    noteBody.replaceChildren();

    const count = Math.max(noteNames.length, noteOffsets.length);
    for (let i = 0; i < count; i++) {
      const name = noteNames[i] !== undefined ? noteNames[i] : "";
      const offset = noteOffsets[i] !== undefined ? noteOffsets[i] : 0;
      appendNoteRow(i + 1, name, offset);
    }
    updateTrackBadge();
  }

  function updateTrackNumbers() {
    noteRows().forEach((tr, index) => {
      tr.querySelector(".track-num").textContent = String(index + 1);
    });
    updateTrackBadge();
  }

  function updateTrackBadge() {
    noteBadge.textContent = `${noteRows().length} トラック`;
  }

  function loadModelIntoForm(modelName) {
    const conf = getModelConfig(modelName);
    if (!conf) {
      return;
    }

    currentModel = modelName;
    // 機種の切り替えは必ずここを通る（追加・削除・改名の後も）。
    // 覚えておいて、他の画面へ移ってもこの機種のままにする。
    window.ModelStore.save(modelName);

    for (const [id, key] of Object.entries(FIELDS)) {
      const val = conf[key];
      $(id).value = val !== undefined && val !== null ? val : "";
    }

    renderNoteTable(conf["note name"] || [], conf["note offset"] || []);
  }

  function gatherFormData() {
    const noteNames = [];
    const noteOffsets = [];

    noteRows().forEach(tr => {
      noteNames.push(tr.querySelector(".note-name-input").value.trim());
      noteOffsets.push(
        parseInt(tr.querySelector(".note-offset-input").value, 10) || 0
      );
    });

    const data = {};
    for (const [id, key] of Object.entries(FIELDS)) {
      const raw = $(id).value;
      data[key] = NUMERIC[key] ? NUMERIC[key](raw) : raw.trim();
    }
    data["note name"] = noteNames;
    data["note offset"] = noteOffsets;
    return data;
  }

  /* ---- サーバーとのやり取り -------------------------------------------- */

  function postConfig(payload) {
    return fetch(`${window.URL_PREFIX}/config/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(res => res.json());
  }

  function setBusy(btn, busy, label) {
    if (busy) {
      btn.setAttribute("aria-busy", "true");
    } else {
      btn.removeAttribute("aria-busy");
    }
    btn.disabled = busy;
    btn.textContent = label;
  }

  /* ---- イベント -------------------------------------------------------- */

  modelSelect.addEventListener("change", () => {
    loadModelIntoForm(modelSelect.value);
  });

  $("btn-add-note").addEventListener("click", () => {
    appendNoteRow(noteRows().length + 1, "", 0);
    updateTrackBadge();
  });

  noteBody.addEventListener("click", e => {
    const btn = e.target.closest(".btn-delete-row");
    if (!btn) {
      return;
    }
    btn.closest("tr").remove();
    updateTrackNumbers();
  });

  saveBtn.addEventListener("click", () => {
    const formData = gatherFormData();

    if (!formData.model) {
      showAlert("機種名は必須です。", "danger");
      return;
    }

    setBusy(saveBtn, true, "保存中...");

    postConfig({
      action: "save",
      model_name: currentModel,
      config: formData,
    }).then(data => {
      setBusy(saveBtn, false, "変更を保存");
      if (data.status === "ok") {
        confData = data.data;
        const updatedModelName = formData.model;
        renderModelSelect(updatedModelName);
        loadModelIntoForm(updatedModelName);
        showAlert(
          `機種「${updatedModelName}」の設定を正常に保存しました。`, "success"
        );
      } else {
        showAlert(`保存エラー: ${data.message}`, "danger");
      }
    }).catch(err => {
      setBusy(saveBtn, false, "変更を保存");
      showAlert(`通信エラーが発生しました: ${err}`, "danger");
    });
  });

  /* ---- 機種の追加 / 削除 ------------------------------------------------ */

  function showDialogError(message) {
    addError.textContent = message;
    addError.hidden = false;
  }

  function closeDialog() {
    dialog.close();
  }

  /* 既存機種と重複しない名前を作る。「34notes」→「34notes 2」 */
  function suggestModelName(base) {
    let name = base;
    for (let i = 2; confData.some(d => d.model === name); i++) {
      name = `${base} ${i}`;
    }
    return name;
  }

  $("btn-add-model").addEventListener("click", () => {
    /* 今編集している機種を引き継ぐ。新機種はたいていその派生なので、
       コピー元をそれにし、名前もそれを元にした候補を入れておく。
       コピー元の選択肢はここで作り直す（機種を切り替えたあとでも
       ダイアログが古い機種を指したままにならないように）。 */
    fillSelect(copySelect, currentModel);
    newNameInput.value = currentModel ? suggestModelName(currentModel) : "";
    addError.hidden = true;
    dialog.showModal();
    newNameInput.focus();
    newNameInput.select();  // そのまま打ち直せるように全選択しておく
  });

  for (const id of ["btn-cancel-add-model", "btn-close-add-model"]) {
    $(id).addEventListener("click", closeDialog);
  }

  $("btn-confirm-add-model").addEventListener("click", () => {
    const newName = newNameInput.value.trim();
    const copyFrom = copySelect.value;

    if (!newName) {
      showDialogError("機種名を入力してください。");
      return;
    }
    if (confData.some(d => d.model === newName)) {
      showDialogError(`機種名「${newName}」は既に存在しています。`);
      return;
    }

    const templateConf = getModelConfig(copyFrom);
    if (!templateConf) {
      showDialogError("コピー元の機種が見つかりません。");
      return;
    }

    const newConf = structuredClone(templateConf);
    newConf.model = newName;

    postConfig({
      action: "add",
      model_name: newName,
      config: newConf,
    }).then(data => {
      closeDialog();
      if (data.status === "ok") {
        confData = data.data;
        renderModelSelect(newName);
        loadModelIntoForm(newName);
        showAlert(`新規機種「${newName}」を追加しました。`, "success");
      } else {
        showAlert(`追加エラー: ${data.message}`, "danger");
      }
    }).catch(err => {
      closeDialog();
      showAlert(`通信エラーが発生しました: ${err}`, "danger");
    });
  });

  $("btn-delete-model").addEventListener("click", () => {
    if (!currentModel) {
      return;
    }
    if (confData.length <= 1) {
      showAlert("機種が1つしかないため、削除できません。", "warning");
      return;
    }
    if (!confirm(`本当に機種「${currentModel}」を削除しますか？`)) {
      return;
    }

    const deleted = currentModel;

    postConfig({
      action: "delete",
      model_name: currentModel,
    }).then(data => {
      if (data.status === "ok") {
        confData = data.data;
        const nextModel = confData[0].model;
        renderModelSelect(nextModel);
        loadModelIntoForm(nextModel);
        showAlert(`機種「${deleted}」を削除しました。`, "success");
      } else {
        showAlert(`削除エラー: ${data.message}`, "danger");
      }
    }).catch(err => {
      showAlert(`通信エラーが発生しました: ${err}`, "danger");
    });
  });

  /* ---- 初期表示 -------------------------------------------------------- */

  if (confData.length > 0) {
    // 前の画面で選んだ機種を引き継ぐ。無ければ先頭の機種
    const initialModel = window.ModelStore.pick(
      confData.map(d => d.model), confData[0].model
    );
    renderModelSelect(initialModel);
    loadModelIntoForm(initialModel);
  }
});
