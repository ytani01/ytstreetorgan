#
# (c) 2026 Yoichi Tanibayashi
#
"""開発中にブラウザを自動リロードさせる仕掛け（``webapp --debug`` のときだけ）。

**サーバー側にファイル監視のロジックは無い。**

1. tornado の autoreload に、テンプレートと静的ファイルも見張らせる。
   これで `.py` だけでなく HTML / CSS / JS を直したときも**プロセスが
   再起動する**（`autoreload=True` だけでは `.py` しか見ていない）。
2. ここの WebSocket は繋がるだけで、中身は何も送らない。
3. ブラウザ側 (`static/js/livereload.js`) は繋いだまま待ち、**切れたら
   ＝再起動が始まった**と見なして、繋ぎ直せるようになるまで試してから
   `location.reload()` する。

つまり「切断」そのものが更新の合図で、通知は要らない。
"""
from pathlib import Path

import tornado.autoreload
import tornado.websocket

from .mylog import getLogger

_log = getLogger('livereload')


class LiveReloadHandler(tornado.websocket.WebSocketHandler):
    """繋がるだけの WebSocket。

    ブラウザは切断を再起動の合図として使うので、こちらから送るものは無い。
    """

    __log = getLogger(__qualname__)

    def open(self, *args, **kwargs) -> None:
        """接続。"""
        self.__log.debug('live reload: connected')

    def on_close(self) -> None:
        """切断。"""
        self.__log.debug('live reload: closed')

    def on_message(self, message) -> None:
        """受け取るものは無い（ブラウザ側は送ってこない）。"""
        self.__log.debug('live reload: unexpected message: {}', message)


def watch_webroot(webroot: Path) -> int:
    """テンプレートと静的ファイルを autoreload の監視対象に加える。

    ``webapp --debug`` のときだけ呼ぶこと。

    Args:
        webroot (Path): `templates/` と `static/` を含むディレクトリ。

    Returns:
        int: 監視対象に加えたファイル数。

    Note:
        `tornado.autoreload.watch()` は**起動時にあるファイルしか見ない**。
        新しく足したテンプレートを見張らせるには、一度手で再起動する。
    """
    count = 0

    for sub in ('templates', 'static'):
        target = webroot / sub
        if not target.is_dir():
            continue

        for path in sorted(target.rglob('*')):
            if path.is_file():
                tornado.autoreload.watch(str(path))
                count += 1

    _log.info('live reload: watching {} files under {}', count, webroot)
    return count
