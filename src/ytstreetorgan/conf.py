#
# (c) 2026 Yoichi Tanibayashi
#
import json
from loguru import logger
from pathlib import Path
from ytstreetorgan.mylog import exmsg

class Conf:
    """Configuration File"""
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

        self.config_file: Path | None = None
        self.data: list[dict] = []
        self.models: list[str] = []

        conf_path: Path = Path(config_file).expanduser()
        logger.debug(f'conf_path=\'{conf_path}\'')

        if conf_path.is_file():
            self.config_file = conf_path
        else:
            self.config_file = self.search()

        if self.config_file is None:
            logger.error('config_file is None')
        else:
            self.load()

    def search(self) -> Path | None:
        """Search config file."""
        logger.debug('')

        for dir in self.SEARCH_PATH:
            conf_path: Path = (dir / self.CONF_FNAME).expanduser()
            logger.debug(f'conf_path=\'{conf_path}\'')
            
            if conf_path.is_file():  # file is found
                logger.debug(f'find: \'{conf_path}\'')
                self.config_file = conf_path
                return self.config_file

        logger.error(f'\'{self.CONF_FNAME}\': not found')
        return None
        
    def load(self) -> list:
        """Load config file."""
        logger.debug(f'config_file={self.config_file}')

        if self.config_file is None:
            logger.error('config_file is None')
            return []

        try:
            json_text = self.config_file.read_text(encoding='utf-8')
            self.data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(exmsg(e))
            return []
        except Exception as e:
            logger.error(exmsg(e))
            return []
            
        self.models = self.get_models()
        return self.data

    def get(self, model_name=''):
        """Get config data for ``model_name``."""
        logger.debug(f'model_name=\'{model_name}\'')

        if self.data is None:
            return None

        for d in self.data:
            if d['model'] == model_name:
                return d

        logger.error(f'mode:\'{model_name}\' not found')
        return None

    def get_models(self) -> list[str]:
        """Get model_name list."""
        logger.debug('')

        self.models = []

        if self.data is None:
            logger.error('data is None')
        else:
            try:
                self.models = [d['model'] for d in self.data]
            except KeyError as e:
                logger.error(exmsg(e))
            except Exception as e:
                logger.error(exmsg(e))
        return self.models
