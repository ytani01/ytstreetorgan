#
# (c) 2026 Yoichi Tanibayashi
#
import json
from loguru import logger
from pathlib import Path

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
        """Constructor"""
        logger.debug(f'config_file=\'{config_file}\'')

        self.config_file: Path | None = None
        self.data: dict | None = None

        conf_path: Path = Path(config_file).expanduser()
        logger.debug(f'conf_path=\'{conf_path}\'')

        if conf_path.is_file():
            self.config_file = conf_path
        else:
            self.config_file = self.search()

        if self.config_file is None:
            logger.error('config_file is None')

    def search(self) -> Path | None:
        """Search config file"""
        logger.debug('')

        for dir in self.SEARCH_PATH:
            conf_path: Path = (dir / self.CONF_FNAME).expanduser()
            logger.debug(f'conf_path=\'{conf_path}\'')
            
            if conf_path.is_file():  # file is found
                logger.debug(f'find: \'{conf_path}\'')
                self.config_file = conf_path
                return self.config_file
            
        return None
        
    def load(self):
        """Load config file"""
        logger.debug(f'config_file={self.config_file}')

        if self.config_file is None:
            logger.error('config_file is None')
            return None

        try:
            json_text = self.config_file.read_text(encoding='utf-8')
            self.data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f'{type(e).__name__}: {e} ')
            return None
        except Exception as e:
            logger.error(f'{type(e).__name__}: {e} ')
            return None
            
        return self.data
