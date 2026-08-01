"""ブラウザテスト用の土台。

実サーバーを空きポートで起動し、Playwright から叩けるようにする。

隔離について:
- ``Conf.SEARCH_PATH`` を一時ディレクトリに差し替える。これをしないと
  ``~/etc/storgan-conf.json``（利用者の実設定）を読み書きしてしまう。
- ``webroot`` も一時ディレクトリに複製する。アップロードすると
  ``webroot/midi/`` と ``webroot/svg/`` にファイルが書かれるため。
"""
import asyncio
import shutil
import socket
import threading
from pathlib import Path

import pytest
import tornado.ioloop

from ytstreetorgan.conf import Conf
from ytstreetorgan.webapp import WebServer

REPO_ROOT = Path(__file__).resolve().parents[2]
URL_PREFIX = '/storgan2'


def _free_port() -> int:
    """使用可能なポート番号を 1 つ確保する。"""
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope='session')
def sample_midi() -> Path:
    """アップロードテスト用の実 MIDI ファイル。"""
    return REPO_ROOT / 'webroot' / 'midi' / 'd-kaeru.mid'


@pytest.fixture(scope='session')
def live_server(tmp_path_factory) -> str:
    """WebServer を別スレッドで起動し、ベース URL を返す。"""
    tmp = tmp_path_factory.mktemp('storgan')

    # 設定ファイルを隔離する（テンプレートを複製して使う）
    conf_dir = tmp / 'conf'
    conf_dir.mkdir()
    shutil.copy(REPO_ROOT / 'conf' / 'storgan.conf-dist',
                conf_dir / Conf.CONF_FNAME)
    original_search_path = Conf.SEARCH_PATH
    Conf.SEARCH_PATH = [conf_dir]

    # webroot を隔離する（アップロード先が書き込まれるため）
    webroot = tmp / 'webroot'
    shutil.copytree(REPO_ROOT / 'webroot' / 'templates', webroot / 'templates')
    shutil.copytree(REPO_ROOT / 'webroot' / 'static', webroot / 'static')
    (webroot / 'midi').mkdir()
    (webroot / 'svg').mkdir()

    port = _free_port()
    started = threading.Event()
    state: dict = {}

    def serve() -> None:
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            server = WebServer(
                port=port, urlprefix=URL_PREFIX,
                webroot=str(webroot), workdir=str(tmp / 'work'),
            )
            server._svr.listen(port, address='127.0.0.1')
            state['loop'] = tornado.ioloop.IOLoop.current()
        except Exception as e:  # 起動失敗をテスト側に伝える
            state['error'] = e
            started.set()
            return
        started.set()
        state['loop'].start()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()

    if not started.wait(timeout=30):
        Conf.SEARCH_PATH = original_search_path
        pytest.fail('サーバーが起動しなかった')
    if 'error' in state:
        Conf.SEARCH_PATH = original_search_path
        pytest.fail(f'サーバーの起動に失敗: {state["error"]}')

    yield f'http://127.0.0.1:{port}{URL_PREFIX}'

    state['loop'].add_callback(state['loop'].stop)
    thread.join(timeout=10)
    Conf.SEARCH_PATH = original_search_path
