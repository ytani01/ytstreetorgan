"""設定エディタ (config_editor.js) のブラウザテスト。

サーバー側の HTTP テストでは通らない jQuery のロジックを対象にする。
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


def test_save_persists_edited_value(live_server: str, page: Page) -> None:
    """フォームの編集内容が保存され、サーバー側の値が変わる。"""
    page.goto(f'{live_server}/config')

    page.fill('#field-margin', '7.5')
    page.click('#btn-save-config')

    expect(page.locator('#alert-container')).to_contain_text('正常に保存しました')

    # サーバーから読み直しても反映されている
    body = page.request.get(f'{live_server}/config/api/data').body()
    data = json.loads(body)
    saved = next(d for d in data['data'] if d['model'] == '34notes')
    assert saved['margin'] == 7.5
