#
# (c) 2026 Yoichi Tanibayashi
#
"""storgan — MIDI から手回しオルガン用ロールブック（SVG）を作る。"""
import os
from importlib.metadata import PackageNotFoundError, version

# pygame は import されるだけでバナーを出す。`ytmidilib.Player` 経由で
# 必ず読み込まれるので、**その前に**黙らせる（ytmidilib 0.1.0 の回答書。
# ライブラリ側からは触らない方針なので、利用側でやる）。
# `setdefault` なのは、外から明示的に設定されていればそれに従うため
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', 'hide')

__author__ = 'ytani01'
__copyright_year__ = "2026"


__version__: str = ''
if __package__:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = "0.0.0"
else:
    __version__ = "_._._"

from .conf import Conf
from .mylog import exmsg, getLogger, loggerInit
from .rollbook import RollBook
from .webapp import WebServer

__all__ = [
    "__author__",
    "__copyright_year__",
    "__version__",
    "getLogger",
    "Conf",
    "loggerInit",
    "exmsg",
    "RollBook",
    "WebServer"
]
