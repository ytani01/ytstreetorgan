"""
tests/test_mylog.py - mylog.py の動作確認テスト
"""
import sys

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


class TestNamedLogger:
    """getLogger() / setLevel() のテスト（名前ごとの水準）

    `setLevel(name, None)` で必ず戻すこと。名前ごとの水準はモジュールの
    辞書に残るので、そのままだと後のテストに効いてしまう
    （`conftest.py` の `reset_logger` は loguru のシンクしか消さない）。
    """

    def test_named_level_overrides_default(self, capsys):
        """名前に水準を付けると、既定より下でも出る"""
        from ytstreetorgan.mylog import getLogger, loggerInit, setLevel
        loggerInit(debug=False, out=sys.stderr)  # 既定は INFO
        noisy = getLogger("Noisy", "DEBUG")
        try:
            noisy.debug("noisy_debug")
            assert "noisy_debug" in capsys.readouterr().err
        finally:
            setLevel("Noisy", None)

    def test_other_names_keep_default(self, capsys):
        """水準を付けていない名前は既定のまま"""
        from ytstreetorgan.mylog import getLogger, loggerInit, setLevel
        loggerInit(debug=False, out=sys.stderr)  # 既定は INFO
        noisy = getLogger("Noisy", "DEBUG")
        quiet = getLogger("Quiet")
        try:
            quiet.debug("quiet_debug")
            noisy.debug("noisy_debug")
            captured = capsys.readouterr()
            assert "quiet_debug" not in captured.err
            assert "noisy_debug" in captured.err
        finally:
            setLevel("Noisy", None)

    def test_named_level_can_be_higher(self, capsys):
        """既定より高い水準にすると、その名前だけ出なくなる"""
        from ytstreetorgan.mylog import getLogger, loggerInit, setLevel
        loggerInit(debug=True, out=sys.stderr)  # 既定は DEBUG
        silent = getLogger("Silent", "WARNING")
        try:
            silent.info("silent_info")
            assert "silent_info" not in capsys.readouterr().err
        finally:
            setLevel("Silent", None)

    def test_setlevel_none_restores_default(self, capsys):
        """setLevel(name, None) で既定水準に戻る"""
        from ytstreetorgan.mylog import getLogger, loggerInit, setLevel
        loggerInit(debug=False, out=sys.stderr)  # 既定は INFO
        log = getLogger("Tmp", "DEBUG")
        setLevel("Tmp", None)
        log.debug("after_reset")
        assert "after_reset" not in capsys.readouterr().err

    def test_setlevel_keeps_default_entry(self, capsys):
        """既定水準（名前 ''）は setLevel('', None) では消えない"""
        from ytstreetorgan.mylog import loggerInit, setLevel
        loggerInit(debug=False, out=sys.stderr)
        setLevel("", None)
        logger.debug("still_hidden")
        logger.info("still_shown")
        captured = capsys.readouterr()
        assert "still_hidden" not in captured.err
        assert "still_shown" in captured.err

    def test_unnamed_logger_uses_default(self, capsys):
        """名前を付けない logger は既定水準で判定される"""
        from ytstreetorgan.mylog import loggerInit
        loggerInit(debug=False, out=sys.stderr)
        logger.debug("plain_debug")
        logger.info("plain_info")
        captured = capsys.readouterr()
        assert "plain_debug" not in captured.err
        assert "plain_info" in captured.err


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
