#
# (c) 2026 Yoichi Tanibayashi
#
"""mylog.py

# sample

```python
from .mylog import loggerInit, exmsg

def main(debug: bool = False):
    logInit(debug=debug)
    logger.debug(debg)

    try:
     :
    except Exception as e:
      logger.error(exmsg(e))
```
"""

import sys

from loguru import logger

LOG_FMT = (
    "<level>"
    "<white>{time:MM/DD HH:mm:ss}</white> "
    "{level.icon} {level} "
    "{file}<green>:</green>{line} "
    "{function}()<green>></green> "
    "<white>{message}</white>"
    "</level>"
)


def logLevel(debug: bool = False) -> str:
    """ログの水準。``debug`` なら DEBUG、そうでなければ INFO。"""
    return "DEBUG" if debug else "INFO"


def loggerInit(debug: bool = False, out=sys.stderr) -> None:
    """logger を初期化する。

    各 CLI コマンドの先頭で 1 度だけ呼ぶ。

    Args:
        debug (bool): デバッグ出力を出すか。
        out: 出力先。既定は標準エラー。
    """
    logger.remove()
    logger.add(out, format=LOG_FMT, level=logLevel(debug))


def exmsg(ex) -> str:
    """例外を 1 行の文字列にする（``ValueError: 使えない名前です`` の形）。"""
    return f'{type(ex).__name__}: {ex}'
