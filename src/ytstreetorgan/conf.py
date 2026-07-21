#
# (c) 2026 Yoichi Tanibayashi
#
import json
from typing import TypedDict
from loguru import logger
from pathlib import Path
from .mylog import exmsg


ModelConf = TypedDict(
    'ModelConf',
    {
        'model': str,
        'book height': float,
        'margin': float,
        'pitch': float,
        'hole height': float,
        '1sec': float,
        'note name': list[str],
        'note offset': list[int],
        'base note': int,
        'bridge width': float,
        'bridge interval': float,
        'bridge threshold': float,
        'memo': str,
    },
    total=False,
)


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

        self.data: list[ModelConf] = []
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

    def load(self) -> list[ModelConf]:
        """Load config file."""
        logger.debug(f'config_file=\'{self.config_file}\'')

        try:
            json_text = self.config_file.read_text(encoding='utf-8')
            self.data = json.loads(json_text)
            self.models = [d['model'] for d in self.data]  # pyright: ignore[reportTypedDictNotRequiredAccess]
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

    def get(self, model_name: str = '') -> ModelConf:
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
