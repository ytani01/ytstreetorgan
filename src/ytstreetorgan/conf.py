#
# (c) 2026 Yoichi Tanibayashi
#
import json
import shutil
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


def validate_config(conf: dict) -> tuple[bool, str]:
    """Validate a ModelConf dictionary structure and values."""

    model_name = conf.get('model')
    if not model_name or not isinstance(model_name, str) or not model_name.strip():
        return False, "Model name is required and must be a non-empty string"

    required_numeric_fields = [
        'book height', 'margin', 'pitch', 'hole height', '1sec',
        'base note', 'bridge width', 'bridge interval', 'bridge threshold'
    ]

    for field in required_numeric_fields:
        val = conf.get(field)
        if val is None:
            return False, f"Missing required field: '{field}'"
        try:
            float(val)
        except (ValueError, TypeError):
            return False, f"Field '{field}' must be a valid number"

    note_names = conf.get('note name')
    note_offsets = conf.get('note offset')

    if not isinstance(note_names, list):
        return False, "'note name' must be a list of strings"

    if not isinstance(note_offsets, list):
        return False, "'note offset' must be a list of integers"

    if len(note_names) != len(note_offsets):
        return False, f"Length mismatch: 'note name' ({len(note_names)}) and 'note offset' ({len(note_offsets)}) must have equal length"

    for idx, offset in enumerate(note_offsets):
        try:
            int(offset)
        except (ValueError, TypeError):
            return False, f"Item at index {idx} in 'note offset' must be an integer"

    return True, ""


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

    def save(self) -> tuple[bool, str]:
        """Save configuration to JSON file atomically with backup."""
        if not self.config_file:
            msg = "config_file path is not set"
            logger.error(msg)
            return False, msg

        try:
            # Create backup if existing config file exists
            if self.config_file.exists():
                bak_file = self.config_file.with_name(self.config_file.name + '.bak')
                shutil.copy2(self.config_file, bak_file)
                logger.debug(f"Created backup: {bak_file}")

            # Atomic save via temporary file
            tmp_file = self.config_file.with_name(self.config_file.name + '.tmp')
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.write('\n')

            tmp_file.replace(self.config_file)
            self.models = [d['model'] for d in self.data if isinstance(d, dict) and 'model' in d]
            logger.info(f"Saved configuration to {self.config_file}")
            return True, "Configuration saved successfully"

        except Exception as e:
            msg = f"Failed to save configuration: {exmsg(e)}"
            logger.error(msg)
            return False, msg

    def update_model(self, model_name: str, new_conf: dict) -> tuple[bool, str]:
        """Update an existing model configuration and save."""
        valid, msg = validate_config(new_conf)
        if not valid:
            return False, msg

        target_idx = None
        for idx, d in enumerate(self.data):
            if d.get('model') == model_name:
                target_idx = idx
                break

        if target_idx is None:
            msg = f"Model '{model_name}' not found"
            logger.error(msg)
            return False, msg

        # Ensure types for numeric fields
        new_conf_cleaned = dict(new_conf)
        new_conf_cleaned['book height'] = float(new_conf_cleaned['book height'])
        new_conf_cleaned['margin'] = float(new_conf_cleaned['margin'])
        new_conf_cleaned['pitch'] = float(new_conf_cleaned['pitch'])
        new_conf_cleaned['hole height'] = float(new_conf_cleaned['hole height'])
        new_conf_cleaned['1sec'] = float(new_conf_cleaned['1sec'])
        new_conf_cleaned['base note'] = int(new_conf_cleaned['base note'])
        new_conf_cleaned['bridge width'] = float(new_conf_cleaned['bridge width'])
        new_conf_cleaned['bridge interval'] = float(new_conf_cleaned['bridge interval'])
        new_conf_cleaned['bridge threshold'] = float(new_conf_cleaned['bridge threshold'])
        new_conf_cleaned['note offset'] = [int(x) for x in new_conf_cleaned['note offset']]

        self.data[target_idx] = new_conf_cleaned  # type: ignore
        return self.save()

    def add_model(self, new_conf: dict) -> tuple[bool, str]:
        """Add a new model configuration and save."""
        valid, msg = validate_config(new_conf)
        if not valid:
            return False, msg

        model_name = new_conf['model']
        if model_name in self.models:
            msg = f"Model '{model_name}' already exists"
            logger.error(msg)
            return False, msg

        new_conf_cleaned = dict(new_conf)
        new_conf_cleaned['book height'] = float(new_conf_cleaned['book height'])
        new_conf_cleaned['margin'] = float(new_conf_cleaned['margin'])
        new_conf_cleaned['pitch'] = float(new_conf_cleaned['pitch'])
        new_conf_cleaned['hole height'] = float(new_conf_cleaned['hole height'])
        new_conf_cleaned['1sec'] = float(new_conf_cleaned['1sec'])
        new_conf_cleaned['base note'] = int(new_conf_cleaned['base note'])
        new_conf_cleaned['bridge width'] = float(new_conf_cleaned['bridge width'])
        new_conf_cleaned['bridge interval'] = float(new_conf_cleaned['bridge interval'])
        new_conf_cleaned['bridge threshold'] = float(new_conf_cleaned['bridge threshold'])
        new_conf_cleaned['note offset'] = [int(x) for x in new_conf_cleaned['note offset']]

        self.data.append(new_conf_cleaned)  # type: ignore
        return self.save()

    def delete_model(self, model_name: str) -> tuple[bool, str]:
        """Delete a model configuration by name and save."""
        target_idx = None
        for idx, d in enumerate(self.data):
            if d.get('model') == model_name:
                target_idx = idx
                break

        if target_idx is None:
            msg = f"Model '{model_name}' not found"
            logger.error(msg)
            return False, msg

        del self.data[target_idx]
        return self.save()
