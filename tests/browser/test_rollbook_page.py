"""メイン画面（MIDI アップロード → SVG プレビュー）のブラウザテスト。"""
import re
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


def test_upload_non_midi_shows_a_message(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """MIDI でないファイルを送ると、理由を出してファイル選択の画面に戻る。

    捕まえないと tornado 既定の 500 ページに置き換わり、画面ごと失われる
    （実際そうなっていた）。
    """
    bad = tmp_path / 'not-a-song.mid'
    bad.write_bytes(b'this is not a MIDI file')

    page.goto(f'{live_server}/')

    with page.expect_response(lambda r: r.request.method == 'POST') as info:
        page.set_input_files('input[name="file1"]', str(bad))

    assert info.value.status == 200

    status = page.locator('#drop-status')
    expect(status).to_contain_text('not-a-song.mid を読み込めませんでした')
    expect(status).to_have_class(re.compile(r'drop__status--error'))

    # ロールブックは出ない。選び直せるようフォームは残っている
    expect(page.locator('#svgbox')).to_have_count(0)
    expect(page.locator('input[name="file1"]')).to_be_attached()


def test_broken_upload_is_not_kept(
    live_server: str, page: Page, tmp_path: Path, sample_midi: Path
) -> None:
    """読み込めなかったファイルは残さない。

    残すと、次に同じ名前で正しいファイルを送っても
    ``Handler1.post()`` の ``exists()`` に弾かれ、壊れたほうが使われる。
    """
    same_name = tmp_path / 'retry.mid'

    page.goto(f'{live_server}/')
    same_name.write_bytes(b'broken')
    with page.expect_response(lambda r: r.request.method == 'POST'):
        page.set_input_files('input[name="file1"]', str(same_name))
    expect(page.locator('#drop-status')).to_contain_text('読み込めませんでした')

    # 同じ名前で、今度は中身の正しい MIDI を送る
    same_name.write_bytes(sample_midi.read_bytes())
    page.set_input_files('input[name="file1"]', str(same_name))

    expect(page.locator('#svgbox svg')).to_be_visible()
    expect(page.locator('a[href*="/download/retry.mid.svg"]')).to_have_count(1)


def test_upload_over_size_limit_is_stopped_before_sending(
    small_limit_server: str, page: Page, sample_midi: Path
) -> None:
    """上限を超えるファイルは、送る前に止めて理由を出す。

    送ってしまうと tornado が本文を読まずに接続を切るので、ブラウザには
    真っ白なページが残る（実際そうなっていた）。
    """
    assert sample_midi.stat().st_size > 4096

    page.goto(f'{small_limit_server}/')
    # size_limit がそのまま画面の案内になっている
    expect(page.locator('.drop__sub')).to_contain_text('4.0 KB まで')

    sent: list[str] = []
    page.on('request', lambda r: (
        sent.append(r.url) if r.method == 'POST' else None
    ))

    page.set_input_files('input[name="file1"]', str(sample_midi))

    status = page.locator('#drop-status')
    expect(status).to_contain_text('大きすぎます')
    expect(status).to_contain_text('4.0 KB')
    expect(status).to_have_class(re.compile(r'drop__status--error'))

    assert not sent, f'上限超えなのに送っている: {sent}'
    expect(page.locator('#svgbox')).to_have_count(0)
