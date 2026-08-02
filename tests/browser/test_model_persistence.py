"""選んだ機種が画面をまたいで受け継がれることのテスト。

ロールブック作成 ⇔ 機種設定 のどちらで選んでも、もう一方に反映される
（`static/js/model_store.js`）。
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.browser


def test_model_selected_on_main_page_carries_to_config(
    live_server: str, page: Page
) -> None:
    """作成画面で選んだ機種が、機種設定の画面に引き継がれる。"""
    page.goto(f'{live_server}/')
    page.select_option('#model', '20notes')

    page.goto(f'{live_server}/config')

    expect(page.locator('#model-select')).to_have_value('20notes')
    expect(page.locator('#field-model')).to_have_value('20notes')


def test_model_selected_on_config_page_carries_to_main(
    live_server: str, page: Page
) -> None:
    """機種設定で選んだ機種が、作成画面に引き継がれる。"""
    page.goto(f'{live_server}/config')
    page.select_option('#model-select', '20notes')
    expect(page.locator('#field-model')).to_have_value('20notes')

    page.goto(f'{live_server}/')

    expect(page.locator('#model')).to_have_value('20notes')


def test_model_selection_survives_reload(live_server: str, page: Page) -> None:
    """作成画面を開き直しても、選んだ機種のまま。"""
    page.goto(f'{live_server}/')
    page.select_option('#model', '20notes')

    page.reload()

    expect(page.locator('#model')).to_have_value('20notes')


def test_unknown_saved_model_falls_back(live_server: str, page: Page) -> None:
    """覚えている機種が無くなっていたら、先頭の機種に戻る。

    機種設定の画面で削除・改名できるため、起こりうる。
    """
    page.goto(f'{live_server}/')
    page.evaluate('() => localStorage.setItem("storgan.model", "no-such")')

    page.reload()

    expect(page.locator('#model')).to_have_value('34notes')
