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
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import tornado.ioloop
from playwright.sync_api import expect

from ytstreetorgan.conf import Conf
from ytstreetorgan.webapp import WebServer

from ..conftest import LONG_MIDI, TEST_URL_PREFIX

REPO_ROOT = Path(__file__).resolve().parents[2]

# あえて既定値 (WebServer.URL_PREFIX = '/storgan2') 以外を使う。
# テンプレートや JS が prefix を直書きしていると、ここで 404 になって
# test_static_assets_load が落ちる。実際にその不具合があった。
URL_PREFIX = TEST_URL_PREFIX


def _free_port() -> int:
    """使用可能なポート番号を 1 つ確保する。"""
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return int(s.getsockname()[1])


def _make_webroot(tmp: Path) -> Path:
    """テンプレートと静的ファイルを複製した webroot を作る。

    アップロード先（``midi/`` と ``svg/``）は書き込まれるので空で用意する。
    """
    webroot = tmp / 'webroot'
    shutil.copytree(REPO_ROOT / 'webroot' / 'templates', webroot / 'templates')
    shutil.copytree(REPO_ROOT / 'webroot' / 'static', webroot / 'static')
    (webroot / 'midi').mkdir()
    (webroot / 'svg').mkdir()
    return webroot


def _start_server(tmp: Path, **kwargs) -> tuple[str, Callable[[], None]]:
    """WebServer を別スレッドで起動し、(ベース URL, 停止関数) を返す。"""
    port = _free_port()
    started = threading.Event()
    state: dict = {}

    def serve() -> None:
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            server = WebServer(
                port=port, urlprefix=URL_PREFIX,
                webroot=str(_make_webroot(tmp)), workdir=str(tmp / 'work'),
                **kwargs,
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
        pytest.fail('サーバーが起動しなかった')
    if 'error' in state:
        pytest.fail(f'サーバーの起動に失敗: {state["error"]}')

    def stop() -> None:
        state['loop'].add_callback(state['loop'].stop)
        thread.join(timeout=10)

    return f'http://127.0.0.1:{port}{URL_PREFIX}', stop


@pytest.fixture(scope='session')
def sample_midi() -> Path:
    """アップロードテスト用の MIDI（`tests/data/make_midi.py` が作る）。

    **ビューアのテストがこれを使う**ので、高さを合わせた状態で横に
    大きくはみ出すもの（全長 2350mm）を渡す。
    """
    return LONG_MIDI


@pytest.fixture(scope='session')
def live_server(tmp_path_factory) -> Iterator[str]:
    """WebServer を別スレッドで起動し、ベース URL を返す。"""
    tmp = tmp_path_factory.mktemp('storgan')

    # 設定ファイルを隔離する（テンプレートを複製して使う）
    conf_dir = tmp / 'conf'
    conf_dir.mkdir()
    shutil.copy(REPO_ROOT / 'conf' / Conf.CONF_FNAME,
                conf_dir / Conf.CONF_FNAME)
    original_search_path = Conf.SEARCH_PATH
    Conf.SEARCH_PATH = [conf_dir]

    url, stop = _start_server(tmp)
    try:
        yield url
    finally:
        stop()
        Conf.SEARCH_PATH = original_search_path


@pytest.fixture(scope='session')
def small_limit_server(live_server: str, tmp_path_factory) -> Iterator[str]:
    """アップロード上限を 4 KB にしたサーバー。

    既定の上限は 100 MB で、超えさせるには 100 MB 送る必要がある。
    上限そのものの挙動だけ見たいので、小さい上限のサーバーを別に立てる。

    ``live_server`` に依存しているのは順序のため。``Conf.SEARCH_PATH`` は
    クラス変数なので、こちらが先に走って別の場所を指すと、あとから起動する
    ``live_server`` の設定と食い違う。隔離済みの設定に相乗りする。
    """
    tmp = tmp_path_factory.mktemp('storgan-small')
    url, stop = _start_server(tmp, size_limit=4096)
    try:
        yield url
    finally:
        stop()


@pytest.fixture(scope='session')
def conf_file() -> Path:
    """``live_server`` が読み書きしている設定ファイル。

    ``live_server`` が ``Conf.SEARCH_PATH`` を一時ディレクトリ 1 本に
    差し替えているので、そこから引ける。
    """
    return Conf.SEARCH_PATH[0] / Conf.CONF_FNAME


@pytest.fixture
def restore_conf(live_server: str, conf_file: Path) -> Iterator[None]:
    """設定を書き換えるテストのために、テスト後に内容を元へ戻す。

    ``live_server`` はセッション全体で 1 個なので、機種を足したり消したり
    したままにすると後続のテストが影響を受ける。ハンドラはリクエストごとに
    ``Conf()`` を作り直すため、ファイルを戻せばサーバー側の状態も戻る。
    """
    saved = conf_file.read_text(encoding='utf-8')
    yield
    conf_file.write_text(saved, encoding='utf-8')


def upload_midi(page, live_server: str, midi: Path,
                choice: str = 'btn-same-replace',
                wait_result: bool = True) -> None:
    """MIDI を 1 本アップロードして、生成結果の画面まで進む。

    `live_server` はセッション全体で 1 個なので、同じ名前のファイルを
    先に別のテストが送っていると同名ダイアログが出る。既定では
    「置き換えて変換」を押す。

    **既定では生成結果が出るまで待つ。** 待たずに次へ進むと、
    書き終える前に履歴を読みにいって落ちることがある。

    Args:
        page: Playwright のページ。
        live_server (str): サーバーの URL（prefix 込み）。
        midi (Path): 送る MIDI ファイル。
        choice (str): 同名だったときに押すボタンの id。
        wait_result (bool): 生成結果を待つか。送信そのものが止まる場合
            （上限超えなど）は False にする。
    """
    page.goto(f'{live_server}/')
    page.set_input_files('input[name="file1"]', str(midi))

    modal = page.locator('#same-name-modal')
    if modal.is_visible():
        page.click(f'#{choice}')

    if wait_result:
        expect(page.locator('#svgbox svg')).to_be_visible()
