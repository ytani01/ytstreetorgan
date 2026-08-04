#
# (c) 2026 Yoichi Tanibayashi
#
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from loguru import logger

from .mylog import exmsg


class NoteConf(TypedDict):
    """トラック 1 本の定義。

    Attributes:
        name: 音名（例: 'F#'）。表示用で、穴の位置には影響しない。
        offset: ``base_note`` からの半音数。
    """

    name: str
    offset: int


class ModelConf(TypedDict, total=False):
    """機種 1 つ分の設定。

    キーはそのまま JSON のフィールド名。**すべて Python の識別子**なので、
    この TypedDict を class 形式で書ける。かつては ``'book height'`` の
    ように空白入りで、関数形式でしか書けなかった。
    **旧形式はもう読めない。**

    Attributes:
        model: 機種名。設定の中で一意。
        book_height: ブックの高さ [mm]。
        margin: 上端から 1 本目のトラックまで [mm]。
        pitch: トラックの間隔 [mm]。
        hole_height: 穴の高さ [mm]。
        mm_per_sec: 秒 → mm の変換係数。旧 ``'1sec'``（数字始まりで識別子に
            できないため、``RollBook.mm_per_sec`` に合わせて改名した）。
        base_note: オフセットを数える起点の MIDI ノート番号。
        bridge_width: ブリッジ（紙のつなぎ）の幅 [mm]。
        bridge_threshold: これを超える穴を分割する [mm]。
        notes: トラックの定義。並び順がそのままトラック番号。
        memo: 覚え書き（動作には影響しない）。
    """

    model: str
    book_height: float
    margin: float
    pitch: float
    hole_height: float
    mm_per_sec: float
    base_note: int
    bridge_width: float
    bridge_threshold: float
    notes: list[NoteConf]
    memo: str


# 必須の数値項目と、その値に適用する変換。
# validate_config() の検証と coerce_numeric_fields() の型変換の両方が
# この定義を使うので、設定項目を増減させるときはここだけ直せばよい。
# 挿入順がそのまま検証順（＝エラーメッセージに出る項目の順）になる。
NUMERIC_FIELDS: dict[str, Callable[[Any], Any]] = {
    'book_height': float,
    'margin': float,
    'pitch': float,
    'hole_height': float,
    'mm_per_sec': float,
    'base_note': int,
    'bridge_width': float,
    'bridge_threshold': float,
}


def coerce_numeric_fields(conf: dict) -> dict:
    """Return a copy of ``conf`` with numeric fields converted to their type.

    ``validate_config()` must have passed first: this assumes every key in
    :data:`NUMERIC_FIELDS` is present and convertible.
    """
    cleaned = dict(conf)
    for field, cast in NUMERIC_FIELDS.items():
        cleaned[field] = cast(cleaned[field])
    cleaned['notes'] = [
        {'name': str(n['name']), 'offset': int(n['offset'])}
        for n in cleaned['notes']
    ]
    return cleaned


def validate_config(conf: object) -> tuple[bool, str]:
    """Validate a ModelConf dictionary structure and values.

    ``conf`` is untrusted input: it comes straight from the JSON body of a
    ``ConfigHandler`` POST, so it may be any JSON type, not just a dict.
    """

    if not isinstance(conf, dict):
        return False, "設定はオブジェクト（辞書）である必要があります"

    model_name = conf.get('model')
    if not model_name or not isinstance(model_name, str) or not model_name.strip():
        return False, "機種名は必須です（空でない文字列）"

    for field, cast in NUMERIC_FIELDS.items():
        val = conf.get(field)
        if val is None:
            return False, f"必須項目 '{field}' がありません"
        try:
            # 変換そのものを検証に使う。float() で検証して int() で変換すると
            # "60.5" のような値が検証を通ったあとで例外になる。
            cast(val)
        except (ValueError, TypeError):
            return False, f"項目 '{field}' は数値である必要があります"

    notes = conf.get('notes')

    if not isinstance(notes, list):
        return False, "'notes' は {'name', 'offset'} のリストである必要があります"

    for idx, note in enumerate(notes):
        if not isinstance(note, dict):
            return False, (
                f"{idx + 1} 番目のトラックは"
                " 'name' と 'offset' を持つオブジェクトである必要があります"
            )

        if not isinstance(note.get('name'), str):
            return False, (
                f"{idx + 1} 番目のトラックの 'name' は文字列である必要があります"
            )

        try:
            int(note.get('offset'))  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return False, (
                f"{idx + 1} 番目のトラックの 'offset' は整数である必要があります"
            )

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
            self.models = [
                d['model']  # pyright: ignore[reportTypedDictNotRequiredAccess]
                for d in self.data
            ]
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
        (e.g. ``'base_note'``, ``'hole_height'``, ``'mm_per_sec'``, …).
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
            msg = "設定ファイルのパスが設定されていません"
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
            with tmp_file.open('w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.write('\n')

            tmp_file.replace(self.config_file)
            self.models = [
                d['model'] for d in self.data
                if isinstance(d, dict) and 'model' in d
            ]
            logger.info(f"Saved configuration to {self.config_file}")
            return True, "設定を保存しました"

        except Exception as e:
            msg = f"設定の保存に失敗しました: {exmsg(e)}"
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
            msg = f"機種 '{model_name}' が見つかりません"
            logger.error(msg)
            return False, msg

        self.data[target_idx] = coerce_numeric_fields(new_conf)  # type: ignore
        return self.save()

    def add_model(self, new_conf: dict) -> tuple[bool, str]:
        """Add a new model configuration and save."""
        valid, msg = validate_config(new_conf)
        if not valid:
            return False, msg

        model_name = new_conf['model']
        if model_name in self.models:
            msg = f"機種 '{model_name}' は既に存在します"
            logger.error(msg)
            return False, msg

        self.data.append(coerce_numeric_fields(new_conf))  # type: ignore
        return self.save()

    def delete_model(self, model_name: str) -> tuple[bool, str]:
        """Delete a model configuration by name and save."""
        target_idx = None
        for idx, d in enumerate(self.data):
            if d.get('model') == model_name:
                target_idx = idx
                break

        if target_idx is None:
            msg = f"機種 '{model_name}' が見つかりません"
            logger.error(msg)
            return False, msg

        del self.data[target_idx]
        return self.save()
