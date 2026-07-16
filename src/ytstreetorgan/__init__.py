#
# (c) 2026 Yoichi Tanibayashi
#
"""
storgan
"""
from importlib.metadata import PackageNotFoundError, version
from loguru import logger


__author__ = '(c) 2026 Yoichi Tanibayashi'


__version__: str = ''
if __package__:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = "0.0.0"
else:
    __version__ = "_._._"

from .rollbook import RollBook
from .webapp import WebServer
from .conf import Conf
from .mylog import loggerInit, exmsg

__all__ = [
    "__author__",
    "__version__",
    "logger",
    "Conf",
    "loggerInit",
    "exmsg",
    "RollBook",
    "WebServer"
]
