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
    # （ロゴなどの装飾 SVG と区別するため、置き場を明示して選ぶ）
    expect(page.locator('#svgbox svg')).to_be_visible()

    # ダウンロードリンクが元のファイル名 + .svg を指している
    link = page.locator(f'a[href*="/download/{sample_midi.name}.svg"]')
    expect(link).to_have_count(1)

    # リンク先が実際に SVG を返す
    href = link.get_attribute('href')
    assert href is not None
    res = page.request.get(urljoin(page.url, href))
    assert res.ok
    assert res.text().startswith('<svg')


def test_viewer_starts_at_the_beginning_of_the_song(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """初期表示は右端。

    viewBox が負で、曲の先頭が x=0 側 = ブックの右端にあるため。
    """
    page.goto(f'{live_server}/')
    page.set_input_files('input[name="file1"]', str(sample_midi))

    expect(page.locator('#svgbox svg')).to_be_visible()

    # 既定は「高さ合わせ」なので横にはみ出しており、その右端にいる
    page.wait_for_function(
        '() => { const b = document.getElementById("svgbox");'
        ' return b.scrollWidth > b.clientWidth'
        ' && b.scrollLeft >= b.scrollWidth - b.clientWidth - 2; }'
    )


def test_viewer_zoom_controls(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """倍率のボタンが SVG の描画サイズを変える。"""
    page.goto(f'{live_server}/')
    page.set_input_files('input[name="file1"]', str(sample_midi))

    expect(page.locator('#svgbox svg')).to_be_visible()

    # 原寸 = 100%。そこから縮小すると 1/1.4 倍
    page.click('#fit-actual')
    expect(page.locator('#zoomval')).to_have_text('100%')
    page.click('#zoom-out')
    expect(page.locator('#zoomval')).to_have_text('71%')

    # 「全体」は横スクロールが消えるところまで縮む
    page.click('#fit-all')
    page.wait_for_function(
        '() => { const b = document.getElementById("svgbox");'
        ' return b.scrollWidth <= b.clientWidth + 2; }'
    )


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
