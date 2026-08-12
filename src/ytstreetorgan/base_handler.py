#
# (c) 2026 Yoichi Tanibayashi
#
"""全ハンドラの土台（TODO-075）。

`handler1.py` に置いてあったが、`history.py` と `config_handler.py` が
**「ロールブックを作る画面」のモジュールから基底クラスを import する**
形になっていた。役割から見て逆なので、独立させた。

依存は一方向に保つこと::

    base_handler.py → handler1.py / download.py / history.py /
                      config_handler.py
"""
from pathlib import Path

import tornado.web
from loguru import logger

from . import __author__, __copyright_year__
from .mylog import exmsg
from .storage import resolve_in


class StorganBaseHandler(tornado.web.RequestHandler):
    """全ハンドラの土台。`app.settings` から共通の設定を取り出す。

    `webroot` / `workdir` は `WebServer` が `Path` に正規化して渡している。
    """

    def __init__(self, app, req, **kwargs):
        """設定を取り出してから、tornado の初期化を呼ぶ。

        `**kwargs` はルート定義の 3 要素目（`Download` の `kind` など）。
        tornado がそのまま渡してくるので、受けて `initialize()` へ流す。
        """
        self._urlprefix = app.settings.get('urlprefix')

        # WebServer が Path に正規化して渡している
        self._webroot: Path = app.settings['webroot']
        self._workdir: Path = app.settings['workdir']
        self._size_limit = app.settings.get('size_limit')

        # app や request を丸ごと出すと -d のとき数百行になるので、
        # 使う値だけ 1 行にまとめる
        logger.debug(
            'urlprefix={}, webroot={}, workdir={}, size_limit={}',
            self._urlprefix, self._webroot, self._workdir, self._size_limit
        )

        # [!! 重要 !!] 末尾の「/」
        # Handler1.get() がリクエスト URI とこれを突き合わせ、
        # 末尾スラッシュなしのアクセスをここへリダイレクトする。
        self._url_path = self._urlprefix + '/'

        self._version = app.settings.get('version')

        # 開発用。True ならテンプレートが livereload.js を読み込む
        self._livereload = app.settings.get('livereload', False)

        super().__init__(app, req, **kwargs)

    def render_page(self, html_file: str, title: str, nav: str, **kwargs):
        """テンプレートを描画する。**全ページ共通の引数はここで足す。**

        `base.html` が使う author / version / copyright_year / urlprefix /
        livereload はどのページでも同じ値なので、各ハンドラで並べない。

        Args:
            html_file (str): テンプレートのファイル名。
            title (str): `<title>` とフッターに出す名前。
            nav (str): ナビの現在地（'top' / 'history' / 'config'）。
            **kwargs: そのページだけの変数。
        """
        self.render(
            html_file,
            title=title,
            author=__author__,
            version=self._version,
            copyright_year=__copyright_year__,
            urlprefix=self._urlprefix,
            livereload=self._livereload,
            nav=nav,
            **kwargs,
        )

    def uploaded_midi_names(self) -> list[str]:
        """これまでにアップロードされた MIDI のファイル名。

        同じ名前で上げ直すと中身が置き換わるので、画面 (storgan.js) が
        送る前に確認するのに使う。
        """
        midi_dir = self._webroot / 'midi'
        if not midi_dir.is_dir():
            return []

        return sorted(
            p.name for p in midi_dir.iterdir()
            if p.is_file() and not p.name.startswith('.')
        )

    def stored_file(self, subdir: str, name: str) -> Path:
        """置き場（`webroot/<subdir>/`）の中のファイルを引く。

        名前は URL から来るので、**必ず `resolve_in()` を通す**
        （置き場の外を指していないか確かめる）。

        `Handler1._stored_path()` は同じことを画面に理由を出す形で
        やっている。**あちらと混ぜないこと**（持ち帰りの経路で HTML を
        返しても読まれない）。

        Args:
            subdir (str): 置き場（'midi' / 'svg'）。
            name (str): ファイル名。URL から来る。

        Returns:
            Path: 実在するファイルのパス。

        Raises:
            tornado.web.HTTPError: 名前が置き場の外を指していれば 400、
                ファイルが無ければ 404。
        """
        try:
            path_name = resolve_in(self._webroot / subdir, name)
        except ValueError as e:
            logger.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='bad file name') from e

        if not path_name.is_file():
            raise tornado.web.HTTPError(404)

        return path_name

    def transpose_arg(self) -> int:
        """クエリの `t`（移調の半音数）を読む。

        Returns:
            int: 半音数。

        Raises:
            tornado.web.HTTPError: 整数として読めなければ 400。
        """
        transpose = self.get_argument('t', '')

        try:
            return int(transpose)
        except ValueError as e:
            logger.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='bad transpose') from e
