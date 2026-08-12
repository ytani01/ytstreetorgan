"""
tests/conftest.py - 共通フィクスチャ
"""
import shutil
from pathlib import Path

import pytest
from loguru import logger

from ytstreetorgan.conf import Conf

REPO_ROOT = Path(__file__).resolve().parents[1]

# テスト用に合成した MIDI（TODO-081）。中身と作り方は
# `tests/data/make_midi.py` にある。**`webroot/midi/` は追跡していない**
# ので、そこから読むとクローン直後に落ちる（実際そうなっていた）
DATA_DIR = Path(__file__).resolve().parent / 'data'
SAMPLE_MIDI = DATA_DIR / 'sample.mid'
LONG_MIDI = DATA_DIR / 'long-notes.mid'
IN_SCALE_MIDI = DATA_DIR / 'in-scale.mid'

# WebServer / ConfigHandler は Conf() を引数なしで生成するため、
# 何もしないと Conf.SEARCH_PATH 経由で ~/etc/storgan-conf.json
# （利用者の実設定）を読み書きしてしまう。
# 実際 test_config_handler の add/delete テストが実ファイルを書き換えていた。
TEST_URL_PREFIX = '/storgan-test'


@pytest.fixture(scope='session', autouse=True)
def isolate_user_config(tmp_path_factory):
    """全テストで、利用者の実設定を触らないようにする。"""
    conf_dir = tmp_path_factory.mktemp('conf')
    shutil.copy(REPO_ROOT / 'conf' / Conf.CONF_FNAME,
                conf_dir / Conf.CONF_FNAME)

    original = Conf.SEARCH_PATH
    Conf.SEARCH_PATH = [conf_dir]
    yield conf_dir
    Conf.SEARCH_PATH = original


@pytest.fixture(autouse=True)
def reset_logger():
    """各テスト前後に loguru のシンクをリセットする"""
    logger.remove()
    yield
    logger.remove()


def pytest_collection_modifyitems(items):
    """browser マーカーのテストを最後に回す。

    Playwright の sync API はメインスレッドにイベントループを残すため、
    先に実行すると後続の tornado ``AsyncHTTPTestCase`` が
    "Cannot run the event loop while another loop is running" で落ちる。
    逆順なら問題ないので、収集順を並べ替えて両方を同一プロセスで
    実行できるようにする（``pytest -m ""`` やカバレッジ計測で必要）。
    """
    # bool をキーにした安定ソート: False (通常) が先、True (browser) が後
    items.sort(key=lambda item: item.get_closest_marker('browser') is not None)
