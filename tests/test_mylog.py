"""
tests/test_mylog.py - mylog.py の動作確認テスト
"""
import sys
import pytest
from loguru import logger


class TestLogLevel:
    """logLevel() 関数のテスト"""

    def test_debug_true_returns_debug(self):
        """debug=True のとき 'DEBUG' を返す"""
        from ytstreetorgan.mylog import logLevel
        assert logLevel(True) == "DEBUG"

    def test_debug_false_returns_info(self):
        """debug=False のとき 'INFO' を返す"""
        from ytstreetorgan.mylog import logLevel
        assert logLevel(False) == "INFO"

    def test_default_returns_info(self):
        """引数なしのとき 'INFO' を返す"""
        from ytstreetorgan.mylog import logLevel
        assert logLevel() == "INFO"


class TestLoggerInit:
    """loggerInit() 関数のテスト"""

    def test_loggerinit_adds_handler(self):
        """loggerInit() 呼び出し後、loguru logger にハンドラが追加される"""
        from ytstreetorgan.mylog import loggerInit
        # loguru では _core.handlers で登録済みハンドラ数を確認できる
        loggerInit(debug=False)
        handler_count = len(logger._core.handlers)
        assert handler_count >= 1

    def test_loggerinit_debug_mode(self, capsys):
        """loggerInit(debug=True) でDEBUGメッセージが出力される"""
        from ytstreetorgan.mylog import loggerInit
        loggerInit(debug=True, out=sys.stderr)
        logger.debug("debug_test_message")
        captured = capsys.readouterr()
        assert "debug_test_message" in captured.err

    def test_loggerinit_info_mode_hides_debug(self, capsys):
        """loggerInit(debug=False) でDEBUGメッセージが出力されない"""
        from ytstreetorgan.mylog import loggerInit
        loggerInit(debug=False, out=sys.stderr)
        logger.debug("should_not_appear")
        captured = capsys.readouterr()
        assert "should_not_appear" not in captured.err

    def test_loggerinit_info_message_appears(self, capsys):
        """loggerInit(debug=False) でINFOメッセージは出力される"""
        from ytstreetorgan.mylog import loggerInit
        loggerInit(debug=False, out=sys.stderr)
        logger.info("info_test_message")
        captured = capsys.readouterr()
        assert "info_test_message" in captured.err

    def test_loggerinit_removes_previous_handlers(self):
        """loggerInit() を2回呼ぶとハンドラが重複しない"""
        from ytstreetorgan.mylog import loggerInit
        loggerInit(debug=False)
        handler_count = len(logger._core.handlers)
        assert handler_count == 1


class TestLogFormat:
    """LOG_FMT フォーマット文字列のテスト"""

    def test_log_fmt_is_string(self):
        """LOG_FMT が文字列である"""
        from ytstreetorgan.mylog import LOG_FMT
        assert isinstance(LOG_FMT, str)

    def test_log_fmt_contains_message(self):
        """LOG_FMT に {message} プレースホルダが含まれる"""
        from ytstreetorgan.mylog import LOG_FMT
        assert "{message}" in LOG_FMT
