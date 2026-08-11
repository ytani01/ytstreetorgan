"""移調の候補を、ブラウザ上で試聴する機能のテスト（TODO-063）。"""
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from .conftest import upload_midi

pytestmark = pytest.mark.browser


def test_audition_button_swaps_player_src_without_rerendering(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """試聴ボタンは `<midi-player>` の src を差し替えるだけで、

    ロールブックの作り直し（POST）には行かない。「MIDI」列のリンクも
    従来どおり `/download/midi-transpose/` のままで、試聴と持ち帰りが
    混ざっていないことを確かめる。
    """
    upload_midi(page, live_server, sample_midi)

    posts: list[str] = []
    page.on('request', lambda r: (
        posts.append(r.url) if r.method == 'POST' else None
    ))
    failed: list[str] = []
    page.on('response', lambda r: (
        failed.append(f'{r.status} {r.url}') if r.status >= 400 else None
    ))

    row = page.locator('#transpose-table tbody tr').first
    audition_btn = row.locator('button[data-audition]')
    audition_src = audition_btn.get_attribute('data-audition')
    assert audition_src is not None
    assert '/audition/' in audition_src

    midi_link = row.locator('a[href*="/download/midi-transpose/"]')
    midi_href_before = midi_link.get_attribute('href')
    assert midi_href_before is not None
    assert '/download/midi-transpose/' in midi_href_before

    audition_btn.click()

    # <midi-player> の src がその行の試聴 URL に差し替わる
    player = page.locator('#audition-player')
    expect(player).to_have_attribute('src', audition_src)

    # 押した行に印が付く
    expect(row).to_have_class(re.compile(r'is-audition'))

    # MIDI 列は変わらない（試聴と持ち帰りが混ざっていない）
    assert midi_link.get_attribute('href') == midi_href_before

    # ロールブックの作り直し（POST）には行っていない
    assert not posts, f'試聴ボタンで送信している: {posts}'

    # 400 以上のレスポンスが無い（試聴の読み込みも含めて）
    page.wait_for_timeout(500)
    assert not failed, f'400 以上のレスポンスがあった: {failed}'


def test_audition_player_enables_play_button_after_loading(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """試聴の対象を読み込んだあと、プレーヤーの再生ボタンが押せるようになる。"""
    upload_midi(page, live_server, sample_midi)

    row = page.locator('#transpose-table tbody tr').first
    row.locator('button[data-audition]').click()

    player = page.locator('#audition-player')
    # <midi-player> はカスタム要素で、再生ボタンは shadow DOM の中にある
    # （Playwright のロケーターはシャドウ DOM を貫通する）
    play_button = player.locator('button.play')
    expect(play_button).to_be_enabled(timeout=15000)
