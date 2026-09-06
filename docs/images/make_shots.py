"""`docs/User.md` に貼るスクリーンショットを撮り直す。

    uv run python docs/images/make_shots.py

`tests/browser/conftest.py` と同じやり方でサーバーを隔離して起動する
（設定ファイルはテンプレートの複製、`webroot` も一時ディレクトリに複製）。
**利用者の実設定 `~/etc/storgan-conf.json` には触らない。**

画面を変えたら、これを走らせて `docs/images/*.png` を更新すること。
撮る MIDI は `tests/data/` のもの（実曲は出所がはっきりしないので置かない。
`tests/data/make_midi.py` と同じ理由）。
"""
import asyncio
import shutil
import socket
import tempfile
import threading
from pathlib import Path

import tornado.ioloop
from playwright.sync_api import expect, sync_playwright

from ytstreetorgan.conf import Conf
from ytstreetorgan.webapp import WebServer

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'docs' / 'images'
DATA = REPO / 'tests' / 'data'
MAIN_MIDI = DATA / 'long-notes.mid'      # 穴が多く、破線と統合も含む
EXTRA_MIDI = ['sample.mid', 'in-scale.mid']   # 履歴を 1 件だけにしない
PREFIX = '/storgan2'


def start_server(tmp: Path) -> str:
    """隔離した設定と webroot でサーバーを起動し、ベース URL を返す。"""
    conf_dir = tmp / 'conf'
    conf_dir.mkdir()
    shutil.copy(REPO / 'conf' / Conf.CONF_FNAME, conf_dir / Conf.CONF_FNAME)
    Conf.SEARCH_PATH = [conf_dir]

    webroot = tmp / 'webroot'
    shutil.copytree(REPO / 'webroot' / 'templates', webroot / 'templates')
    shutil.copytree(REPO / 'webroot' / 'static', webroot / 'static')
    (webroot / 'midi').mkdir()
    (webroot / 'svg').mkdir()

    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = int(s.getsockname()[1])

    started = threading.Event()
    state: dict = {}

    def serve() -> None:
        asyncio.set_event_loop(asyncio.new_event_loop())
        server = WebServer(port=port, urlprefix=PREFIX, webroot=str(webroot),
                           workdir=str(tmp / 'work'))
        server._svr.listen(port, address='127.0.0.1')
        state['loop'] = tornado.ioloop.IOLoop.current()
        started.set()
        state['loop'].start()

    threading.Thread(target=serve, daemon=True).start()
    if not started.wait(timeout=30):
        raise RuntimeError('サーバーが起動しなかった')
    return f'http://127.0.0.1:{port}{PREFIX}'


def clip_of(page, selectors: list[str]) -> dict:
    """指定した要素をすべて含む範囲（少し余白を付ける）を返す。"""
    boxes = [b for s in selectors
             if (b := page.locator(s).first.bounding_box())]
    x0 = min(b['x'] for b in boxes)
    y0 = min(b['y'] for b in boxes)
    x1 = max(b['x'] + b['width'] for b in boxes)
    y1 = max(b['y'] + b['height'] for b in boxes)
    return {'x': x0 - 8, 'y': y0 - 8,
            'width': x1 - x0 + 16, 'height': y1 - y0 + 16}


def upload(page, base: str, midi: Path) -> None:
    """MIDI を 1 本上げて、生成結果が出るまで待つ。"""
    page.goto(f'{base}/')
    page.set_input_files('input[name="file1"]', str(midi))
    if page.locator('#same-name-modal').is_visible():
        page.click('#btn-same-replace')
    expect(page.locator('#svgbox svg')).to_be_visible(timeout=30000)


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix='storgan-shot-'))
    base = start_server(tmp)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # 2 倍で撮る（そのままだと文字が潰れる）
        page = browser.new_page(viewport={'width': 1180, 'height': 860},
                                device_scale_factor=2)

        page.goto(f'{base}/')
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / 'web-upload.png'), full_page=True,
                        clip=clip_of(page, ['.page-title', 'article']))

        upload(page, base, MAIN_MIDI)
        page.wait_for_timeout(1500)
        # 穴が密なところを見せる（先頭は長い音だけで、紙の余白ばかりになる）
        page.evaluate("""() => {
          const box = document.getElementById('svgbox');
          box.scrollLeft = box.scrollWidth * 0.30;
        }""")
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / 'web-result.png'), full_page=True,
                        clip=clip_of(page, ['.result-head', '.viewer-card']))

        page.locator('.midi-audition').scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        page.screenshot(
            path=str(OUT / 'web-transpose.png'), full_page=True,
            clip=clip_of(page, ['.midi-audition', '#transpose-panel'])
        )

        for name in EXTRA_MIDI:
            upload(page, base, DATA / name)

        page.goto(f'{base}/history')
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / 'web-history.png'), full_page=True,
                        clip=clip_of(page, ['.page-title', '.hist-grid']))

        page.goto(f'{base}/config')
        page.wait_for_timeout(900)
        page.screenshot(path=str(OUT / 'web-config.png'), full_page=True,
                        clip=clip_of(page, ['.page-title', '.cfg-grid']))

        browser.close()

    shutil.rmtree(tmp, ignore_errors=True)
    print(f'{OUT} に書きました。')


if __name__ == '__main__':
    main()
