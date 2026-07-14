"""
tests/conftest.py - 共通フィクスチャ
"""
import pytest
from loguru import logger
import sys


@pytest.fixture(autouse=True)
def reset_logger():
    """各テスト前後に loguru のシンクをリセットする"""
    logger.remove()
    yield
    logger.remove()
