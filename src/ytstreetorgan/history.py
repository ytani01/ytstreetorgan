#
# (c) 2026 Yoichi Tanibayashi
#
"""履歴の画面。アップロード済み MIDI と生成済み SVG の一覧・削除。

`webroot/` の中を触るので、名前の検証は `storage.py` に任せる。
"""
from pathlib import Path

from .base_handler import StorganBaseHandler
from .conf import Conf
from .mylog import exmsg, getLogger
from .rollbook import RollBook
from .storage import KINDS, list_files, resolve_in


class HistoryHandler(StorganBaseHandler):
    """履歴の画面と、その削除 API。"""

    __log = getLogger(__qualname__)

    HTML_FILE = 'history.html'
    TITLE = 'Roll Book History'

    def __init__(self, app, req, **kwargs):
        """設定ファイルの位置を決めてから、基底クラスの初期化を呼ぶ。"""
        self._conf_file = RollBook.DEF_CONF_FILE
        super().__init__(app, req, **kwargs)

    def _dir(self, kind: str) -> Path:
        """種別（'midi' / 'svg'）に対応する置き場。"""
        if kind not in KINDS:
            raise ValueError(f'不明な種別です: {kind!r}')

        return self._webroot / KINDS[kind]

    def get(self):
        """一覧を描画する。"""
        self.__log.debug('request uri={}', self.request.uri)

        conf = Conf(self._conf_file)

        self.render_page(
            self.HTML_FILE,
            title=self.TITLE,
            nav='history',
            models=conf.models,
            midi_files=list_files(self._dir('midi')),
            svg_files=list_files(self._dir('svg')),
        )

    def post(self):
        """削除。JSON で受けて JSON で返す（設定エディタと同じ形）。"""
        try:
            req = self.request_json()
        except ValueError as e:
            self.__log.error(exmsg(e))
            self.write_json_error(400, self.BAD_JSON_MSG)
            return

        kind = req.get('kind', '')
        name = req.get('name', '')
        delete_all = bool(req.get('all', False))

        try:
            target_dir = self._dir(kind)
        except ValueError as e:
            self.write_json_error(400, str(e))
            return

        try:
            if delete_all:
                removed = self._delete_all(target_dir)
            else:
                resolve_in(target_dir, name).unlink()
                removed = 1
        except ValueError as e:
            self.write_json_error(400, str(e))
            return
        except FileNotFoundError:
            self.write_json_error(404, f'{name} は見つかりません')
            return
        except Exception as e:
            self.__log.error(exmsg(e))
            self.write_json_error(500, f'削除できませんでした: {exmsg(e)}')
            return

        self.write_json({
            'status': 'ok',
            'removed': removed,
            'midi_files': list_files(self._dir('midi')),
            'svg_files': list_files(self._dir('svg')),
        })

    def _delete_all(self, target_dir: Path) -> int:
        """置き場の中のファイルを全部消す（隠しファイルは残す）。"""
        removed = 0
        for info in list_files(target_dir):
            resolve_in(target_dir, info['name']).unlink(missing_ok=True)
            removed += 1

        return removed
