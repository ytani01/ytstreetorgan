#
# (c) 2026 Yoichi Tanibayashi
#
"""mylog.py

# sample

```python
from .mylog import LOG_FMT, logLevel

def main(debug: bool = False):
    logger.remove()
    logger.add(sys.stderr, format=LOG_FMT

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
