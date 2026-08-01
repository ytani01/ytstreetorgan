//
// (c) 2026 Yoichi Tanibayashi
// Config Editor JavaScript
//

$(document).ready(function () {
  let confData = window.INITIAL_CONF_DATA || [];
  let currentModel = '';

  function showAlert(message, type = 'success') {
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
    const html = `
      <div class="alert alert-${type} alert-dismissible fade show shadow-sm" role="alert">
        <i class="fas ${icon} mr-2"></i>${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    `;
    $('#alert-container').html(html);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function getModelConfig(modelName) {
    return confData.find(d => d.model === modelName) || null;
  }

  function renderModelSelect(selectModel) {
    const $select = $('#model-select');
    $select.empty();
    confData.forEach(d => {
      const selected = d.model === selectModel ? 'selected' : '';
      $select.append(`<option value="${d.model}" ${selected}>${d.model}</option>`);
    });

    const $copySelect = $('#copy-from-model');
    $copySelect.empty();
    confData.forEach(d => {
      $copySelect.append(`<option value="${d.model}">${d.model}</option>`);
    });
  }

  function renderNoteTable(noteNames, noteOffsets) {
    const $tbody = $('#note-table-body');
    $tbody.empty();

    const count = Math.max(noteNames.length, noteOffsets.length);
    for (let i = 0; i < count; i++) {
      const name = noteNames[i] !== undefined ? noteNames[i] : '';
      const offset = noteOffsets[i] !== undefined ? noteOffsets[i] : 0;
      appendNoteRow(i + 1, name, offset);
    }
    updateTrackBadge();
  }

  function appendNoteRow(idx, name = '', offset = 0) {
    const $tbody = $('#note-table-body');
    const rowHtml = `
      <tr class="note-row">
        <td class="align-middle font-weight-bold text-muted track-num">${idx}</td>
        <td>
          <input type="text" class="form-control form-control-sm note-name-input" value="${name}" placeholder="例: C" required>
        </td>
        <td>
          <input type="number" class="form-control form-control-sm note-offset-input" value="${offset}" required>
        </td>
        <td class="text-center align-middle">
          <button type="button" class="btn btn-outline-danger btn-sm btn-delete-row" title="この行を削除">
            <i class="fas fa-times"></i>
          </button>
        </td>
      </tr>
    `;
    $tbody.append(rowHtml);
  }

  function updateTrackNumbers() {
    $('#note-table-body tr.note-row').each(function (index) {
      $(this).find('.track-num').text(index + 1);
    });
    updateTrackBadge();
  }

  function updateTrackBadge() {
    const count = $('#note-table-body tr.note-row').length;
    $('#note-count-badge').text(`${count} トラック`);
  }

  function loadModelIntoForm(modelName) {
    const conf = getModelConfig(modelName);
    if (!conf) return;

    currentModel = modelName;
    $('#field-model').val(conf['model'] || '');
    $('#field-book-height').val(conf['book height'] !== undefined ? conf['book height'] : '');
    $('#field-margin').val(conf['margin'] !== undefined ? conf['margin'] : '');
    $('#field-pitch').val(conf['pitch'] !== undefined ? conf['pitch'] : '');
    $('#field-hole-height').val(conf['hole height'] !== undefined ? conf['hole height'] : '');
    $('#field-1sec').val(conf['1sec'] !== undefined ? conf['1sec'] : '');
    $('#field-base-note').val(conf['base note'] !== undefined ? conf['base note'] : '');
    $('#field-bridge-width').val(conf['bridge width'] !== undefined ? conf['bridge width'] : '');
    $('#field-bridge-threshold').val(conf['bridge threshold'] !== undefined ? conf['bridge threshold'] : '');
    $('#field-memo').val(conf['memo'] || '');

    renderNoteTable(conf['note name'] || [], conf['note offset'] || []);
  }

  function gatherFormData() {
    const noteNames = [];
    const noteOffsets = [];

    $('#note-table-body tr.note-row').each(function () {
      const name = $(this).find('.note-name-input').val().trim();
      const offset = parseInt($(this).find('.note-offset-input').val(), 10) || 0;
      noteNames.push(name);
      noteOffsets.push(offset);
    });

    return {
      'model': $('#field-model').val().trim(),
      'book height': parseFloat($('#field-book-height').val()),
      'margin': parseFloat($('#field-margin').val()),
      'pitch': parseFloat($('#field-pitch').val()),
      'hole height': parseFloat($('#field-hole-height').val()),
      '1sec': parseFloat($('#field-1sec').val()),
      'base note': parseInt($('#field-base-note').val(), 10),
      'bridge width': parseFloat($('#field-bridge-width').val()),
      'bridge threshold': parseFloat($('#field-bridge-threshold').val()),
      'note name': noteNames,
      'note offset': noteOffsets,
      'memo': $('#field-memo').val().trim()
    };
  }

  // --- Event Handlers ---

  $('#model-select').on('change', function () {
    const selected = $(this).val();
    loadModelIntoForm(selected);
  });

  $('#btn-add-note').on('click', function () {
    const nextIdx = $('#note-table-body tr.note-row').length + 1;
    appendNoteRow(nextIdx, '', 0);
    updateTrackBadge();
  });

  $(document).on('click', '.btn-delete-row', function () {
    $(this).closest('tr').remove();
    updateTrackNumbers();
  });

  $('#btn-save-config').on('click', function () {
    const formData = gatherFormData();

    if (!formData.model) {
      showAlert('機種名は必須です。', 'danger');
      return;
    }

    const payload = {
      action: 'save',
      model_name: currentModel,
      config: formData
    };

    $('#btn-save-config').prop('disabled', true).html('<i class="fas fa-spinner fa-spin mr-2"></i>保存中...');

    fetch(`${window.URL_PREFIX}/config/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        $('#btn-save-config').prop('disabled', false).html('<i class="fas fa-save mr-2"></i> 変更を保存');
        if (data.status === 'ok') {
          confData = data.data;
          const updatedModelName = formData.model;
          renderModelSelect(updatedModelName);
          loadModelIntoForm(updatedModelName);
          showAlert(`機種「${updatedModelName}」の設定を正常に保存しました。`, 'success');
        } else {
          showAlert(`保存エラー: ${data.message}`, 'danger');
        }
      })
      .catch(err => {
        $('#btn-save-config').prop('disabled', false).html('<i class="fas fa-save mr-2"></i> 変更を保存');
        showAlert(`通信エラーが発生しました: ${err}`, 'danger');
      });
  });

  $('#btn-add-model').on('click', function () {
    $('#new-model-name').val('');
    $('#addModelModal').modal('show');
  });

  $('#btn-confirm-add-model').on('click', function () {
    const newName = $('#new-model-name').val().trim();
    const copyFrom = $('#copy-from-model').val();

    if (!newName) {
      alert('新規機種名を入力してください。');
      return;
    }

    if (confData.some(d => d.model === newName)) {
      alert(`機種名「${newName}」は既に存在しています。`);
      return;
    }

    const templateConf = getModelConfig(copyFrom);
    if (!templateConf) return;

    const newConf = JSON.parse(JSON.stringify(templateConf));
    newConf.model = newName;

    const payload = {
      action: 'add',
      model_name: newName,
      config: newConf
    };

    fetch(`${window.URL_PREFIX}/config/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        $('#addModelModal').modal('hide');
        if (data.status === 'ok') {
          confData = data.data;
          renderModelSelect(newName);
          loadModelIntoForm(newName);
          showAlert(`新規機種「${newName}」を追加しました。`, 'success');
        } else {
          showAlert(`追加エラー: ${data.message}`, 'danger');
        }
      })
      .catch(err => {
        $('#addModelModal').modal('hide');
        showAlert(`通信エラーが発生しました: ${err}`, 'danger');
      });
  });

  $('#btn-delete-model').on('click', function () {
    if (!currentModel) return;

    if (confData.length <= 1) {
      showAlert('機種が1つしかないため、削除できません。', 'warning');
      return;
    }

    if (!confirm(`本当に機種「${currentModel}」を削除しますか？`)) {
      return;
    }

    const payload = {
      action: 'delete',
      model_name: currentModel
    };

    fetch(`${window.URL_PREFIX}/config/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          confData = data.data;
          const nextModel = confData[0].model;
          renderModelSelect(nextModel);
          loadModelIntoForm(nextModel);
          showAlert(`機種「${currentModel}」を削除しました。`, 'success');
        } else {
          showAlert(`削除エラー: ${data.message}`, 'danger');
        }
      })
      .catch(err => {
        showAlert(`通信エラーが発生しました: ${err}`, 'danger');
      });
  });

  // Initial setup
  if (confData.length > 0) {
    const initialModel = confData[0].model;
    renderModelSelect(initialModel);
    loadModelIntoForm(initialModel);
  }
});
