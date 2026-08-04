"""設定エディタ (config_editor.js) のブラウザテスト。

サーバー側の HTTP テストでは通らない、ブラウザ上のロジックを対象にする。

設定を書き換えるテストは ``restore_conf`` を付けること。``live_server`` は
セッション全体で 1 個なので、書き換えたままにすると後続に影響する。
"""
import json

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.browser


def test_selecting_model_populates_form(live_server: str, page: Page) -> None:
    """機種を選ぶと、その設定値が各入力欄に反映される。"""
    page.goto(f'{live_server}/config')

    # 初期表示は先頭の機種
    expect(page.locator('#field-model')).to_have_value('34notes')

    page.select_option('#model-select', '20notes')

    expect(page.locator('#field-model')).to_have_value('20notes')
    # 別機種に切り替わったので、寸法も 20notes のものになっている
    book_height = page.input_value('#field-book-height')
    assert float(book_height) > 0

    # 音階数もその機種のものに差し替わる
    rows = page.locator('#note-table-body tr.note-row')
    expect(rows).to_have_count(20)
    expect(page.locator('#note-count-badge')).to_have_text('20 トラック')


def test_add_and_delete_note_row_renumbers(live_server: str, page: Page) -> None:
    """ノート行を追加・削除すると、行番号とバッジが振り直される。"""
    page.goto(f'{live_server}/config')

    rows = page.locator('#note-table-body tr.note-row')
    expect(rows).to_have_count(34)

    page.click('#btn-add-note')
    expect(rows).to_have_count(35)
    expect(page.locator('#note-count-badge')).to_have_text('35 トラック')
    # 追加された行の番号は末尾の連番
    expect(rows.last.locator('.track-num')).to_have_text('35')

    # 先頭行を消すと、以降の番号が繰り上がる
    rows.first.locator('.btn-delete-row').click()
    expect(rows).to_have_count(34)
    expect(page.locator('#note-count-badge')).to_have_text('34 トラック')
    expect(rows.first.locator('.track-num')).to_have_text('1')
    expect(rows.last.locator('.track-num')).to_have_text('34')


def test_add_model_dialog_inherits_current_model(
    live_server: str, page: Page
) -> None:
    """追加ダイアログは、今編集している機種を引き継ぐ。"""
    page.goto(f'{live_server}/config')
    page.select_option('#model-select', '20notes')
    expect(page.locator('#field-model')).to_have_value('20notes')

    page.click('#btn-add-model')

    # コピー元は編集中の機種。名前もそれを元にした（重複しない）候補
    expect(page.locator('#copy-from-model')).to_have_value('20notes')
    expect(page.locator('#new-model-name')).to_have_value('20notes 2')


def test_save_persists_edited_value(
    live_server: str, page: Page, restore_conf: None
) -> None:
    """フォームの編集内容が保存され、サーバー側の値が変わる。"""
    page.goto(f'{live_server}/config')

    page.fill('#field-margin', '7.5')

    # トラックの音名・オフセットも、表から拾って保存されること
    rows = page.locator('#note-table-body tr.note-row')
    rows.first.locator('.note-name-input').fill('C#')
    rows.first.locator('.note-offset-input').fill('3')

    page.click('#btn-save-config')

    expect(page.locator('#alert-container')).to_contain_text('正常に保存しました')

    # サーバーから読み直しても反映されている
    body = page.request.get(f'{live_server}/config/api/data').body()
    data = json.loads(body)
    saved = next(d for d in data['data'] if d['model'] == '34notes')
    assert saved['margin'] == 7.5
    # 編集した先頭トラックだけが変わり、残りは並び順ごと保たれている
    assert len(saved['notes']) == 34
    assert saved['notes'][0] == {'name': 'C#', 'offset': 3}
    assert saved['notes'][1] == {'name': 'G', 'offset': 2}


def _conf_data(page: Page, live_server: str) -> list[dict]:
    """サーバーが持っている設定を読み直す。"""
    body = page.request.get(f'{live_server}/config/api/data').body()
    return json.loads(body)['data']


# ---------------------------------------------------------------------
# 機種の追加 / 削除
# ---------------------------------------------------------------------

def test_add_model_copies_the_template(
    live_server: str, page: Page, restore_conf: None
) -> None:
    """追加を確定すると、コピー元の中身を引き継いだ機種ができる。"""
    page.goto(f'{live_server}/config')
    page.select_option('#model-select', '20notes')
    expect(page.locator('#field-model')).to_have_value('20notes')

    page.click('#btn-add-model')
    page.fill('#new-model-name', '26notes test')
    page.click('#btn-confirm-add-model')

    expect(page.locator('#alert-container')).to_contain_text('追加しました')
    # ダイアログは閉じ、追加した機種がそのまま編集対象になる
    expect(page.locator('#addModelModal')).to_be_hidden()
    expect(page.locator('#model-select')).to_have_value('26notes test')
    expect(page.locator('#field-model')).to_have_value('26notes test')
    expect(page.locator('#note-table-body tr.note-row')).to_have_count(20)

    data = _conf_data(page, live_server)
    added = next(d for d in data if d['model'] == '26notes test')
    src = next(d for d in data if d['model'] == '20notes')
    # 名前以外はコピー元と同じ。トラックは並び順ごと
    assert added['notes'] == src['notes']
    assert added['base_note'] == src['base_note']
    assert added['book_height'] == src['book_height']


@pytest.mark.parametrize('name, expected', [
    ('', '機種名を入力してください'),
    ('20notes', '既に存在'),
])
def test_add_model_rejects_bad_name(
    live_server: str, page: Page, name: str, expected: str
) -> None:
    """名前が空 / 重複なら、サーバーに送らずダイアログ内で断る。"""
    page.goto(f'{live_server}/config')

    sent: list[str] = []
    page.on('request', lambda r: (
        sent.append(r.url) if '/config/save' in r.url else None
    ))

    page.click('#btn-add-model')
    page.fill('#new-model-name', name)
    page.click('#btn-confirm-add-model')

    error = page.locator('#add-model-error')
    expect(error).to_be_visible()
    expect(error).to_contain_text(expected)
    # 打ち直せるようにダイアログは開いたまま
    expect(page.locator('#addModelModal')).to_be_visible()
    assert not sent, f'サーバーに送ってしまっている: {sent}'


def test_delete_model_removes_it(
    live_server: str, page: Page, restore_conf: None
) -> None:
    """確認ダイアログで OK すると、機種が消えて先頭の機種に移る。"""
    page.goto(f'{live_server}/config')
    page.select_option('#model-select', '20notes a')
    expect(page.locator('#field-model')).to_have_value('20notes a')

    page.once('dialog', lambda d: d.accept())
    page.click('#btn-delete-model')

    expect(page.locator('#alert-container')).to_contain_text('削除しました')
    expect(page.locator('#model-select option')).to_have_count(3)
    expect(page.locator('#field-model')).to_have_value('34notes')

    models = [d['model'] for d in _conf_data(page, live_server)]
    assert '20notes a' not in models


def test_delete_model_cancelled_keeps_it(live_server: str, page: Page) -> None:
    """確認ダイアログでキャンセルすると、何も起きない。"""
    page.goto(f'{live_server}/config')
    page.select_option('#model-select', '20notes a')
    expect(page.locator('#field-model')).to_have_value('20notes a')

    sent: list[str] = []
    page.on('request', lambda r: (
        sent.append(r.url) if '/config/save' in r.url else None
    ))

    page.once('dialog', lambda d: d.dismiss())
    page.click('#btn-delete-model')

    # 「何も起きない」ことの確認なので、送っていれば届くだけ待ってから見る
    page.wait_for_timeout(500)
    assert not sent, f'キャンセルしたのに送っている: {sent}'
    expect(page.locator('#alert-container')).to_be_empty()
    expect(page.locator('#field-model')).to_have_value('20notes a')

    models = [d['model'] for d in _conf_data(page, live_server)]
    assert '20notes a' in models


# ---------------------------------------------------------------------
# 入力値の検証とエラー表示
# ---------------------------------------------------------------------

def test_save_rejects_empty_model_name(live_server: str, page: Page) -> None:
    """機種名が空なら、サーバーに送る前に断る。"""
    page.goto(f'{live_server}/config')

    sent: list[str] = []
    page.on('request', lambda r: (
        sent.append(r.url) if '/config/save' in r.url else None
    ))

    page.fill('#field-model', '')
    page.click('#btn-save-config')

    expect(page.locator('#alert-container .alert--error')).to_contain_text(
        '機種名は必須です'
    )
    assert not sent, f'サーバーに送ってしまっている: {sent}'


def test_save_shows_server_side_error(live_server: str, page: Page) -> None:
    """必須の数値欄が空だと、サーバーの 400 がそのまま画面に出る。

    空欄は ``parseFloat('')`` → NaN → JSON では null になり、
    サーバーの ``validate_config()`` が「項目が無い」として弾く。
    """
    page.goto(f'{live_server}/config')

    page.fill('#field-book-height', '')
    page.click('#btn-save-config')

    alert = page.locator('#alert-container .alert--error')
    expect(alert).to_be_visible()
    expect(alert).to_contain_text("必須項目 'book_height' がありません")

    # 「保存中...」のまま固まらず、押せる状態に戻る
    save = page.locator('#btn-save-config')
    expect(save).to_be_enabled()
    expect(save).to_have_text('変更を保存')

    # 失敗したので、サーバー側の値は変わっていない
    saved = next(
        d for d in _conf_data(page, live_server) if d['model'] == '34notes'
    )
    assert saved['book_height'] == 126.0


def test_blank_offset_is_saved_as_zero(
    live_server: str, page: Page, restore_conf: None
) -> None:
    """オフセットを空にすると 0 として保存される。

    ``gatherFormData()`` が ``parseInt(...) || 0`` で拾うため。
    つまりサーバー側の「offset が整数でない」検証は UI からは到達しない
    （到達しうる経路は API を直接叩く場合だけ）。
    """
    page.goto(f'{live_server}/config')

    rows = page.locator('#note-table-body tr.note-row')
    rows.nth(1).locator('.note-offset-input').fill('')
    page.click('#btn-save-config')

    expect(page.locator('#alert-container')).to_contain_text('正常に保存しました')

    saved = next(
        d for d in _conf_data(page, live_server) if d['model'] == '34notes'
    )
    assert saved['notes'][1] == {'name': 'G', 'offset': 0}
