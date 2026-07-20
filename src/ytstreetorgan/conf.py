#
# (c) 2026 Yoichi Tanibayashi
#
import json
from typing import TypedDict
from loguru import logger
from pathlib import Path
from .mylog import exmsg


class ModelConf(TypedDict):
    """
    Typed schema for a single model's configuration entry in storgan-conf.json.

    Keys correspond exactly to the JSON field names in the config file.
    """
    model: str
    book_height: float   # JSON key: "book height"
    margin: float
    pitch: float
    hole_height: float   # JSON key: "hole height"
    sec_per_sec: float   # JSON key: "1sec"
    note_name: list[str]   # JSON key: "note name"
    note_offset: list[int]   # JSON key: "note offset"
    base_note: int   # JSON key: "base note"
    bridge_width: float   # JSON key: "bridge width"
    bridge_interval: float   # JSON key: "bridge interval"
    bridge_threshold: float  # JSON key: "bridge threshold"
    memo: str


class Conf:
    """Configuration data class."""
    SEARCH_PATH = [
        Path('.'),
        Path('~/.config'),
        Path('~/etc'),
        Path('/usr/local/etc'),
        Path('/etc')
    ]
    CONF_FNAME = 'storgan-conf.json'

    def __init__(self, config_file: str = '', debug=False):
        """Constructor."""
        logger.debug(f'config_file=\'{config_file}\'')

        self.config_file = Path(config_file).expanduser()

        self.data: list[dict] = []
        self.models: list[str] = []

        #
        # `config_file`が指定されなければ、SEARCH_PATHを探す
        #
        if config_file == '':
            for dir in self.SEARCH_PATH:
                self.config_file = (dir / self.CONF_FNAME).expanduser()
                logger.debug(f'search config_file=\'{self.config_file}\'')

                if self.config_file.is_file():
                    logger.debug(f'find: \'{self.config_file}\'')
                    break

        if self.config_file.is_file():
            self.load()
        else:
            logger.error(f'{self.config_file.name}: not found')
            raise FileNotFoundError(self.config_file.name)

    def load(self) -> list:
        """Load config file."""
        logger.debug(f'config_file=\'{self.config_file}\'')

        try:
            json_text = self.config_file.read_text(encoding='utf-8')
            self.data = json.loads(json_text)
            self.models = [d['model'] for d in self.data]
        except UnicodeDecodeError as e:
            logger.error(exmsg(e))
            return []
        except json.JSONDecodeError as e:
            logger.error(exmsg(e))
            return []
        except KeyError as e:
            logger.error(exmsg(e))
            return []
        except Exception as e:
            logger.error(exmsg(e))
            return []

        return self.data

    def get(self, model_name='') -> dict:
        """Get config data for ``model_name``.

        Returns a dict whose keys match the raw JSON field names
        (e.g. ``'base note'``, ``'note offset'``, ``'1sec'``, …).
        See :class:`ModelConf` for the full schema documentation.
        """
        logger.debug(f'model_name=\'{model_name}\'')

        if self.data is None:
            return {}

        for d in self.data:
            if d.get('model') == model_name:
                return d

        logger.error(f'mode:\'{model_name}\' not found')
        return {}
