"""履歴の画面のブラウザテスト。

削除は `live_server` の `webroot/` を実際に減らすので、テストの中で
作ったファイルだけを消すこと（`sample_midi` が消えると他が落ちる）。
"""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from .conftest import REPO_ROOT

pytestmark = pytest.mark.browser


def _upload(page: Page, live_server: str, midi: Path) -> None:
    """履歴に 1 件積む。同名を訊かれたら置き換える。"""
    page.goto(f'{live_server}/')
    page.set_input_files('input[name="file1"]', str(midi))

    modal = page.locator('#same-name-modal')
    if modal.is_visible():
        page.click('#btn-same-replace')

    expect(page.locator('#svgbox svg')).to_be_visible()


def test_lists_uploaded_files(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """アップロードしたものが両方の欄に出る。"""
    midi = tmp_path / 'hist-listed.mid'
    midi.write_bytes((REPO_ROOT / 'webroot' / 'midi' / 'holy.mid').read_bytes())
    _upload(page, live_server, midi)

    page.goto(f'{live_server}/history')

    expect(page.locator('#midi-table tr[data-name="hist-listed.mid"]')
           ).to_have_count(1)
    expect(page.locator('#svg-table tr[data-name="hist-listed.mid.svg"]')
           ).to_have_count(1)


def test_show_stored_svg_keeps_all_values(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """「表示」でも諸元が全部出る（生成したときと同じ）。

    寸法と穴の数は図から読み、図から求まらない音符の数と `mm_per_sec` は
    `<svg>` に埋めた属性から読む。
    """
    midi = tmp_path / 'hist-show.mid'
    midi.write_bytes((REPO_ROOT / 'webroot' / 'midi' / 'holy.mid').read_bytes())
    _upload(page, live_server, midi)
    generated = page.locator('.viewer-foot').inner_text()

    page.goto(f'{live_server}/history')
    page.click('#svg-table tr[data-name="hist-show.mid.svg"] [data-show]')

    expect(page.locator('#svgbox svg')).to_be_visible()
    expect(page.locator('.result-head')).to_contain_text('履歴から表示')

    foot = page.locator('.viewer-foot')
    assert '---' not in foot.inner_text()
    assert foot.inner_text() == generated
    # 演奏時間も出る（mm_per_sec が読めるため）
    expect(page.locator('#dur-t')).not_to_have_text('---')
    expect(page.locator('#pos-t')).not_to_have_text('---')


def test_regenerate_from_stored_midi(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """「再生成」なら諸元が全部出る。"""
    midi = tmp_path / 'hist-regen.mid'
    midi.write_bytes((REPO_ROOT / 'webroot' / 'midi' / 'holy.mid').read_bytes())
    _upload(page, live_server, midi)

    page.goto(f'{live_server}/history')
    page.click('#midi-table tr[data-name="hist-regen.mid"] [data-regen]')

    expect(page.locator('#svgbox svg')).to_be_visible()
    expect(page.locator('.result-head')).to_contain_text('生成しました')
    assert '---' not in page.locator('.viewer-foot').inner_text()


def test_delete_one_file(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """個別削除。確認してから消え、一覧から居なくなる。"""
    midi = tmp_path / 'hist-delete.mid'
    midi.write_bytes((REPO_ROOT / 'webroot' / 'midi' / 'holy.mid').read_bytes())
    _upload(page, live_server, midi)

    page.goto(f'{live_server}/history')
    row = page.locator('#svg-table tr[data-name="hist-delete.mid.svg"]')
    expect(row).to_have_count(1)

    page.once('dialog', lambda d: d.accept())
    row.locator('[data-del]').click()

    expect(page.locator('#alert-container')).to_contain_text('削除しました')
    expect(page.locator('#svg-table tr[data-name="hist-delete.mid.svg"]')
           ).to_have_count(0)
    # MIDI のほうは残る
    expect(page.locator('#midi-table tr[data-name="hist-delete.mid"]')
           ).to_have_count(1)


def test_delete_cancelled_keeps_the_file(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """確認でキャンセルしたら、何も送らず消さない。"""
    midi = tmp_path / 'hist-keep.mid'
    midi.write_bytes((REPO_ROOT / 'webroot' / 'midi' / 'holy.mid').read_bytes())
    _upload(page, live_server, midi)

    page.goto(f'{live_server}/history')

    sent: list[str] = []
    page.on('request', lambda r: (
        sent.append(r.url) if r.method == 'POST' else None
    ))

    page.once('dialog', lambda d: d.dismiss())
    page.locator('#midi-table tr[data-name="hist-keep.mid"] [data-del]').click()

    page.wait_for_timeout(500)
    assert not sent, f'キャンセルしたのに送っている: {sent}'
    expect(page.locator('#midi-table tr[data-name="hist-keep.mid"]')
           ).to_have_count(1)
