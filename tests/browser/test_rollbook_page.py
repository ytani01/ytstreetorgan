"""メイン画面（MIDI アップロード → SVG プレビュー）のブラウザテスト。"""
import re
from pathlib import Path
from urllib.parse import urljoin

import pytest
from playwright.sync_api import Page, expect

from .conftest import REPO_ROOT, upload_midi

pytestmark = pytest.mark.browser


def test_upload_midi_renders_svg_preview(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """MIDI を選ぶとフォームが自動送信され、SVG とダウンロードリンクが出る。"""
    page.goto(f'{live_server}/')
    expect(page.locator('text=MIDI ファイルを選んでください')).to_be_visible()

    # ファイル選択で onchange -> form.submit() が走る
    upload_midi(page, live_server, sample_midi)

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
    upload_midi(page, live_server, sample_midi)

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
    upload_midi(page, live_server, sample_midi)

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


def scroll_left(page: Page) -> float:
    """ビューアの横スクロール位置。"""
    return page.evaluate('() => document.getElementById("svgbox").scrollLeft')


def open_viewer(page: Page, live_server: str, midi: Path) -> None:
    """SVG を出して、帯が使える状態にする。"""
    upload_midi(page, live_server, midi)
    expect(page.locator('#svgbox svg')).to_be_visible()

    # 既定の「高さ合わせ」では横にはみ出しているので、帯に動く余地がある
    page.wait_for_function(
        '() => { const b = document.getElementById("svgbox");'
        ' return b.scrollWidth > b.clientWidth * 2; }'
    )


def test_minimap_click_jumps_and_drag_follows(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """帯は押した位置へ飛び、押したまま動かすと付いてくる。"""
    open_viewer(page, live_server, sample_midi)

    bar = page.locator('#minimap').bounding_box()
    assert bar is not None
    y = bar['y'] + bar['height'] / 2

    # 枠の外を押す → その位置へ飛ぶ
    page.mouse.move(bar['x'] + bar['width'] * 0.2, y)
    page.mouse.down()
    left = scroll_left(page)

    # 押したまま右へ → 追従する（離すまで動く）
    page.mouse.move(bar['x'] + bar['width'] * 0.6, y)
    middle = scroll_left(page)
    assert middle > left

    page.mouse.move(bar['x'] + bar['width'] * 0.9, y)
    right = scroll_left(page)
    assert right > middle

    # 離したあとは追従しない
    page.mouse.up()
    page.mouse.move(bar['x'] + bar['width'] * 0.1, y)
    assert scroll_left(page) == right


def test_minimap_window_drag_is_relative(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """枠を掴んだときは飛ばさず、掴んだ場所を保ったまま動かす。"""
    open_viewer(page, live_server, sample_midi)

    bar = page.locator('#minimap').bounding_box()
    assert bar is not None
    y = bar['y'] + bar['height'] / 2

    # まん中あたりへ移しておく（枠が端に貼り付いていると相対移動が見えない）
    page.mouse.click(bar['x'] + bar['width'] / 2, y)
    before = scroll_left(page)

    win = page.locator('#mmwin').bounding_box()
    assert win is not None

    # 枠を掴んだだけでは動かない
    page.mouse.move(win['x'] + win['width'] / 2, y)
    page.mouse.down()
    assert scroll_left(page) == before

    # 動かした分だけ進む（帯の幅に対する割合 = 全長に対する割合）。
    # 離す前に見ること。離してからだと、飛ばすだけの実装でも同じ位置になる
    delta = bar['width'] * 0.1
    page.mouse.move(win['x'] + win['width'] / 2 + delta, y)

    total = page.evaluate('() => document.getElementById("svgbox").scrollWidth')
    assert scroll_left(page) == pytest.approx(
        before + total * 0.1, abs=total * 0.01
    )
    page.mouse.up()


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

    upload_midi(page, small_limit_server, sample_midi, wait_result=False)

    status = page.locator('#drop-status')
    expect(status).to_contain_text('大きすぎます')
    expect(status).to_contain_text('4.0 KB')
    expect(status).to_have_class(re.compile(r'drop__status--error'))

    assert not sent, f'上限超えなのに送っている: {sent}'
    expect(page.locator('#svgbox')).to_have_count(0)


def _book_size(page: Page) -> str:
    """ビューアのフッターから、ブックの諸元を読む。"""
    return page.locator('.viewer-foot').inner_text()


def test_same_name_replaces_after_confirming(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """同じ名前で上げ直したら、置き換えると答えれば新しい中身になる。

    かつては送られてきた中身を捨てて古いほうを解析していたので、
    **成功したように見えて前回の結果が返っていた**。
    """
    short = REPO_ROOT / 'webroot' / 'midi' / 'holy.mid'
    long = REPO_ROOT / 'webroot' / 'midi' / 'd-kaeru.mid'
    same = tmp_path / 'replace-me.mid'

    page.goto(f'{live_server}/')
    same.write_bytes(short.read_bytes())
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#svgbox svg')).to_be_visible()
    before = _book_size(page)

    # 同じ名前・違う中身。訊かれたら「置き換える」
    page.goto(f'{live_server}/')
    same.write_bytes(long.read_bytes())
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#same-name-modal')).to_be_visible()
    page.click('#btn-same-replace')
    expect(page.locator('#svgbox svg')).to_be_visible()

    assert _book_size(page) != before, '古いほうの結果が返っている'


def test_same_name_cancelled_sends_nothing(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """置き換えないと答えたら、送らずにその場で止まる。"""
    midi = REPO_ROOT / 'webroot' / 'midi' / 'holy.mid'
    same = tmp_path / 'keep-me.mid'
    same.write_bytes(midi.read_bytes())

    page.goto(f'{live_server}/')
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#svgbox svg')).to_be_visible()

    page.goto(f'{live_server}/')
    sent: list[str] = []
    page.on('request', lambda r: (
        sent.append(r.url) if r.method == 'POST' else None
    ))
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#same-name-modal')).to_be_visible()
    page.click('#btn-same-cancel')

    expect(page.locator('#same-name-modal')).to_be_hidden()
    expect(page.locator('#drop-status')).to_contain_text('そのままにしました')
    # ファイル選択の画面のまま。送ってもいない
    expect(page.locator('input[name="file1"]')).to_be_attached()
    page.wait_for_timeout(500)
    assert not sent, f'取りやめたのに送っている: {sent}'


def test_same_name_reuse_shows_the_previous_file(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """「前回のファイルで変換」なら、置き換えずに前回のファイルから作る。

    どちらのボタンでも変換はする。違うのは使うファイルだけ。
    """
    first = REPO_ROOT / 'webroot' / 'midi' / 'holy.mid'
    second = REPO_ROOT / 'webroot' / 'midi' / 'd-kaeru.mid'
    same = tmp_path / 'reuse-me.mid'

    page.goto(f'{live_server}/')
    same.write_bytes(first.read_bytes())
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#svgbox svg')).to_be_visible()
    before = _book_size(page)

    # 同じ名前で中身は別物。「前回のファイルで変換」を選ぶ
    page.goto(f'{live_server}/')
    same.write_bytes(second.read_bytes())
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#same-name-modal')).to_be_visible()
    page.click('#btn-same-reuse')

    expect(page.locator('#svgbox svg')).to_be_visible()
    assert _book_size(page) == before, '今回選んだほうで作られている'
    # 何が起きたのか画面に出る
    # どのファイルから作ったのか名前も出る
    expect(page.locator('.result-head')).to_contain_text(
        '前回アップロードした reuse-me.mid から作りました'
    )

    # サーバー側のファイルも置き換わっていない
    page.goto(f'{live_server}/')
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#same-name-modal')).to_be_visible()
    page.click('#btn-same-reuse')
    expect(page.locator('#svgbox svg')).to_be_visible()
    assert _book_size(page) == before


def test_same_name_dialog_closed_by_esc_is_a_cancel(
    live_server: str, page: Page, tmp_path: Path
) -> None:
    """ESC で閉じた場合も、キャンセルと同じ（送らない）。"""
    midi = REPO_ROOT / 'webroot' / 'midi' / 'holy.mid'
    same = tmp_path / 'esc-me.mid'
    same.write_bytes(midi.read_bytes())

    page.goto(f'{live_server}/')
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#svgbox svg')).to_be_visible()

    page.goto(f'{live_server}/')
    sent: list[str] = []
    page.on('request', lambda r: (
        sent.append(r.url) if r.method == 'POST' else None
    ))
    page.set_input_files('input[name="file1"]', str(same))
    expect(page.locator('#same-name-modal')).to_be_visible()
    page.keyboard.press('Escape')

    expect(page.locator('#same-name-modal')).to_be_hidden()
    expect(page.locator('#drop-status')).to_contain_text('そのままにしました')
    page.wait_for_timeout(500)
    assert not sent, f'ESC で閉じたのに送っている: {sent}'
