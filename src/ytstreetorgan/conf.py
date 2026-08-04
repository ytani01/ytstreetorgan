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
    """数値の項目を型変換した写しを返す。

    **先に `validate_config()` を通してあること。** :data:`NUMERIC_FIELDS`
    のキーが全部あって変換できる前提で書いてある。

    Args:
        conf (dict): 機種 1 つ分の設定。

    Returns:
        dict: 数値項目を float / int に直した写し。
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
    """機種 1 つ分の設定の形と値を確かめる。

    **``conf`` は外から来た値。** `ConfigHandler` の POST の本文がそのまま
    渡るので、dict とは限らず、どんな JSON の型でもありうる。

    Args:
        conf (object): 確かめる設定。

    Returns:
        tuple[bool, str]: 問題なければ ``(True, '')``。
            駄目なら ``(False, 理由)``。**理由はそのまま画面に出る**ので
            日本語で書くこと。`'notes'` の要素を指す番号は 1 始まり。
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
    """設定ファイル（`storgan-conf.json`）の読み書き。

    ファイルは**リポジトリの外**にある。`config_file` を省略すると
    :data:`SEARCH_PATH` を順に探し、最初に見つかったものを使う。

    Attributes:
        SEARCH_PATH: 探す場所の並び。
        CONF_FNAME: 設定ファイルの名前。
    """
    SEARCH_PATH = [
        Path('.'),
        Path('~/.config'),
        Path('~/etc'),
        Path('/usr/local/etc'),
        Path('/etc')
    ]
    CONF_FNAME = 'storgan-conf.json'

    def __init__(self, config_file: str = ''):
        """設定を読み込む。

        Args:
            config_file (str): 設定ファイルのパス。空なら
                :data:`SEARCH_PATH` を探す。

        Raises:
            FileNotFoundError: どこにも見つからないとき（探した場所を
                メッセージに並べる）。
        """
        logger.debug('config_file={!r}', config_file)

        self.config_file = Path(config_file).expanduser()

        self.data: list[ModelConf] = []
        self.models: list[str] = []

        #
        # `config_file`が指定されなければ、SEARCH_PATHを探す
        #
        searched: list[Path] = []
        if config_file == '':
            for dir in self.SEARCH_PATH:
                candidate = (dir / self.CONF_FNAME).expanduser()
                searched.append(candidate)
                logger.debug('search config_file={!r}', candidate)

                if candidate.is_file():
                    logger.debug('find: {!r}', candidate)
                    self.config_file = candidate
                    break
            else:
                # 見つからなかった。探した先を持ったままにすると、
                # 最後の候補（/etc/…）が指定されたかのように見える
                self.config_file = searched[-1] if searched else self.config_file

        if self.config_file.is_file():
            self.load()
        else:
            # どこを探したのかまで出す。名前だけだと、設定を置く場所が
            # 分からないまま「見つかりません」とだけ言われることになる
            if searched:
                where = '、'.join(str(p) for p in searched)
                msg = f'{self.CONF_FNAME} が見つかりません（探した場所: {where}）'
            else:
                msg = f'{self.config_file} が見つかりません'

            logger.error(msg)
            raise FileNotFoundError(msg)

    def load(self) -> list[ModelConf]:
        """設定ファイルを読む。

        Returns:
            list[ModelConf]: 読めた設定。読めなければ空のリスト
                （理由はログに出す。**例外にはしない**）。
        """
        logger.debug('config_file={!r}', self.config_file)

        # 読めない理由（文字コード / JSON / 'model' が無い）で扱いを
        # 変えていないので、まとめて捕まえる
        try:
            json_text = self.config_file.read_text(encoding='utf-8')
            self.data = json.loads(json_text)
            self.models = self._model_names()
        except Exception as e:
            logger.error(exmsg(e))
            return []

        return self.data

    def _model_names(self) -> list[str]:
        """`data` に並んでいる機種名。

        **形が違えばそのまま例外にする**（list でない、要素が dict で
        ない、`'model'` が無い）。`load()` がそれを捕まえて空を返すので、
        壊れた設定を半端に読み込んだ状態にしない。
        """
        return [
            d['model']  # pyright: ignore[reportTypedDictNotRequiredAccess]
            for d in self.data
        ]

    def _index_of(self, model_name: str) -> int | None:
        """`data` の何番目がその機種か。無ければ None。"""
        if not self.data:
            return None

        for idx, d in enumerate(self.data):
            if d.get('model') == model_name:
                return idx

        return None

    def get(self, model_name: str = '') -> ModelConf:
        """機種 1 つ分の設定を取り出す。

        Args:
            model_name (str): 機種名。

        Returns:
            ModelConf: キーは生の JSON のフィールド名（``'base_note'``、
                ``'hole_height'``、``'mm_per_sec'`` …）。
                **知らない機種名には空の dict を返す**ので、
                呼ぶ側が空かどうか確かめること（`RollBook.__init__` は
                空なら `ValueError` にする）。
        """
        logger.debug('model_name={!r}', model_name)

        idx = self._index_of(model_name)
        if idx is None:
            logger.error('model={!r}: not found', model_name)
            return {}

        return self.data[idx]

    def save(self) -> tuple[bool, str]:
        """設定をファイルに書く。

        `.bak` を作ってから一時ファイル経由で置き換える（書いている
        途中で落ちても元が壊れないように）。

        Returns:
            tuple[bool, str]: 成否と、画面に出すメッセージ。
        """
        if not self.config_file:
            msg = "設定ファイルのパスが設定されていません"
            logger.error(msg)
            return False, msg

        try:
            # Create backup if existing config file exists
            if self.config_file.exists():
                bak_file = self.config_file.with_name(self.config_file.name + '.bak')
                shutil.copy2(self.config_file, bak_file)
                logger.debug('created backup: {}', bak_file)

            # Atomic save via temporary file
            tmp_file = self.config_file.with_name(self.config_file.name + '.tmp')
            with tmp_file.open('w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.write('\n')

            tmp_file.replace(self.config_file)
            self.models = self._model_names()  # 壊れていれば下の except へ
            logger.info('saved: {}', self.config_file)
            return True, "設定を保存しました"

        except Exception as e:
            msg = f"設定の保存に失敗しました: {exmsg(e)}"
            logger.error(msg)
            return False, msg

    def update_model(self, model_name: str, new_conf: dict) -> tuple[bool, str]:
        """既にある機種の設定を書き換えて保存する。

        Args:
            model_name (str): 書き換える機種の名前。
            new_conf (dict): 新しい設定（`validate_config()` を通す）。

        Returns:
            tuple[bool, str]: 成否と、画面に出すメッセージ。
        """
        valid, msg = validate_config(new_conf)
        if not valid:
            return False, msg

        target_idx = self._index_of(model_name)
        if target_idx is None:
            msg = f"機種 '{model_name}' が見つかりません"
            logger.error(msg)
            return False, msg

        self.data[target_idx] = coerce_numeric_fields(new_conf)  # type: ignore
        return self.save()

    def add_model(self, new_conf: dict) -> tuple[bool, str]:
        """機種を足して保存する。

        Args:
            new_conf (dict): 足す設定（`validate_config()` を通す）。

        Returns:
            tuple[bool, str]: 成否と、画面に出すメッセージ。
        """
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
        """機種を消して保存する。

        Args:
            model_name (str): 消す機種の名前。

        Returns:
            tuple[bool, str]: 成否と、画面に出すメッセージ。
        """
        target_idx = self._index_of(model_name)
        if target_idx is None:
            msg = f"機種 '{model_name}' が見つかりません"
            logger.error(msg)
            return False, msg

        del self.data[target_idx]
        return self.save()
