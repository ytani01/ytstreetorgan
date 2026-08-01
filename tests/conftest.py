"""
tests/conftest.py - 共通フィクスチャ
"""
import pytest
from loguru import logger


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
