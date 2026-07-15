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
    """Log level."""
    return "DEBUG" if debug else "INFO"


def loggerInit(debug: bool = False, out=sys.stderr) -> None:
    """Initialize logger."""
    logger.remove()
    logger.add(out, format=LOG_FMT, level=logLevel(debug))

def exmsg(ex) -> str:
    """exception to message string."""
    return f'{type(ex).__name__}: {ex}'
