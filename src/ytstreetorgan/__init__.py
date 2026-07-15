#
# (c) 2026 Yoichi Tanibayashi
#
"""
storgan
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021/01'

from importlib.metadata import PackageNotFoundError, version
from loguru import logger

if __package__:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = "0.0.0"
else:
    __version__ = "_._._"

from .rollbook import RollBook
from .webapp import WebServer

__all__ = [
    "__version__",
    "logger",
    "RollBook",
    "WebServer"
]
