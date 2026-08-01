"""メイン画面（MIDI アップロード → SVG プレビュー）のブラウザテスト。"""
from pathlib import Path
from urllib.parse import urljoin

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.browser


def test_upload_midi_renders_svg_preview(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """MIDI を選ぶとフォームが自動送信され、SVG とダウンロードリンクが出る。"""
    page.goto(f'{live_server}/')

    expect(page.locator('text=Please select a MIDI file')).to_be_visible()

    # ファイル選択で onchange -> form.submit() が走る
    page.set_input_files('input[name="file1"]', str(sample_midi))

    # 生成された SVG がページに埋め込まれる
    expect(page.locator('svg')).to_be_visible()

    # ダウンロードリンクが元のファイル名 + .svg を指している
    link = page.locator(f'a[href*="/download/{sample_midi.name}.svg"]')
    expect(link).to_have_count(1)

    # リンク先が実際に SVG を返す
    href = link.get_attribute('href')
    assert href is not None
    res = page.request.get(urljoin(page.url, href))
    assert res.ok
    assert res.text().startswith('<svg')


def test_static_assets_load(live_server: str, page: Page) -> None:
    """CSS/JS が 404 しない。

    storgan.html は URL prefix を直書きしていて、実際の prefix
    (/storgan2) と食い違ったまま 404 していたことがある。
    """
    failed: list[str] = []
    page.on('response', lambda r: (
        failed.append(f'{r.status} {r.url}') if r.status >= 400 else None
    ))

    page.goto(f'{live_server}/')
    page.wait_for_load_state('networkidle')

    assert not failed, f'読み込みに失敗したリソース: {failed}'
