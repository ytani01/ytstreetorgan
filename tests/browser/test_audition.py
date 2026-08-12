"""移調の候補を、ブラウザ上で試聴する機能のテスト（TODO-063、TODO-068）。

試聴は行ごとのボタンではなく、**いま表示しているロールブックの移調量**を
プレーヤーが読み込む形（TODO-068）。移調を選ぶとページごと作り直されるので、
そのたびに試聴の対象も切り替わる。
"""
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from .conftest import upload_midi

pytestmark = pytest.mark.browser


def test_player_loads_the_current_transpose(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """プレーヤーには、いま出しているブックの移調量の音が入っている。

    「MIDI」列のリンクは従来どおり `/download/midi-transpose/` のままで、
    試聴と持ち帰りが混ざっていないことも確かめる。
    """
    failed: list[str] = []
    page.on('response', lambda r: (
        failed.append(f'{r.status} {r.url}') if r.status >= 400 else None
    ))

    upload_midi(page, live_server, sample_midi)

    src = page.locator('#audition-player').get_attribute('src')
    assert src is not None
    assert '/audition/midi/' in src

    # いま出しているブックの行（.is-current）の移調量と一致する
    current = page.locator('#transpose-table tbody tr.is-current')
    transpose = current.locator(
        'button[data-transpose]'
    ).get_attribute('data-transpose')
    assert transpose is not None
    assert f'?t={transpose}&' in src

    # 持ち帰る MIDI は別の経路のまま
    midi_link = current.locator('a[href*="/download/midi-transpose/"]')
    assert '/audition/' not in (midi_link.get_attribute('href') or '')

    # 400 以上のレスポンスが無い（試聴の読み込みも含めて）
    page.wait_for_timeout(500)
    assert not failed, f'400 以上のレスポンスがあった: {failed}'


def test_transpose_table_has_no_audition_column(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """行ごとの「試聴」列は無い（TODO-068）。"""
    upload_midi(page, live_server, sample_midi)

    expect(page.locator('#transpose-table [data-audition]')).to_have_count(0)
    # 移調 / 音符 / 音の長さ / 移調後の音域 / MIDI の 5 列
    expect(page.locator('#transpose-table thead th')).to_have_count(5)


def test_selecting_transpose_switches_the_audition(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """別の移調を選ぶと、作り直したページで試聴の対象も切り替わる。"""
    upload_midi(page, live_server, sample_midi)

    other = page.locator(
        '#transpose-table tbody tr:not(.is-current) button[data-transpose]'
    ).first
    transpose = other.get_attribute('data-transpose')
    assert transpose is not None

    other.click()
    page.wait_for_load_state()

    expect(page.locator('#audition-player')).to_have_attribute(
        'src', re.compile(rf'\?t={re.escape(transpose)}&')
    )
    # 選んだ行が、いま出しているブックの行になっている
    expect(
        page.locator('#transpose-table tbody tr.is-current button')
    ).to_have_attribute('data-transpose', transpose)


def test_audition_player_enables_play_button_after_loading(
    live_server: str, page: Page, sample_midi: Path
) -> None:
    """読み込みが済むと、プレーヤーの再生ボタンが押せるようになる。"""
    upload_midi(page, live_server, sample_midi)

    player = page.locator('#audition-player')
    # <midi-player> はカスタム要素で、再生ボタンは shadow DOM の中にある
    # （Playwright のロケーターはシャドウ DOM を貫通する）
    play_button = player.locator('button.play')
    expect(play_button).to_be_enabled(timeout=15000)
