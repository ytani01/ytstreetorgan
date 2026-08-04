#
# (c) 2026 Yoichi Tanibayashi
#
from pathlib import Path

import tornado.web
from loguru import logger

from . import __author__, __copyright_year__
from .conf import Conf
from .mylog import exmsg
from .rollbook import RollBook
from .utils import get_size_unit


class StorganBaseHandler(tornado.web.RequestHandler):
    """
    Common base handler that extracts shared settings from app.settings.
    """
    def __init__(self, app, req):
        """ Constructor """
        logger.debug('app={}', app)
        logger.debug('req={}', req)

        self._urlprefix = app.settings.get('urlprefix')
        logger.debug('urlprefix={}', self._urlprefix)

        # WebServer が Path に正規化して渡している
        self._webroot: Path = app.settings['webroot']
        logger.debug('webroot={}', self._webroot)

        self._workdir: Path = app.settings['workdir']
        logger.debug('workdir={}', self._workdir)

        self._size_limit = app.settings.get('size_limit')
        logger.debug('size_limit={}', self._size_limit)

        # [!! 重要 !!] 末尾の「/」
        # Handler1.get() がリクエスト URI とこれを突き合わせ、
        # 末尾スラッシュなしのアクセスをここへリダイレクトする。
        self._url_path = self._urlprefix + '/'

        self._version = app.settings.get('version')

        super().__init__(app, req)

    def get_filesize(self, file_path: Path) -> tuple[float, str] | None:
        """
        Parameters
        ----------
        file_path: Path
        """
        if not file_path.exists():
            return None

        return get_size_unit(file_path.stat().st_size)

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


class Download(StorganBaseHandler):
    """
    Download SVG file
    """
    def __init__(self, app, req):
        """ Constructor """
        self._model = ''
        self._model_name = RollBook.DEF_MODEL_NAME
        self._conf_file = RollBook.DEF_CONF_FILE
        self._rollbook = RollBook(self._model_name, self._conf_file)

        super().__init__(app, req)

    def get(self):
        """
        GET method and rendering
        """
        logger.debug('request={}', self.request)

        uri = self.request.uri
        assert uri is not None
        fname = uri.split('/')[-1]
        logger.debug('fname={}', fname)

        path_name = self._webroot / 'svg' / fname
        logger.debug('path_name={}', path_name)

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition',
                        'attachment; filename=' + fname)

        buf_size = 4096
        with path_name.open() as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)

        self.finish()


class Handler1(StorganBaseHandler):
    """
    Web handler1
    """
    TITLE = 'Street Organ Roll Book Maker'

    HTML_FILE = 'storgan.html'

    def __init__(self, app, req):
        """ Constructor """
        self._conf_file = RollBook.DEF_CONF_FILE
        self._model_name = RollBook.DEF_MODEL_NAME

        # 画面上で「選んだ機種の寸法」を出すため、名前だけでなく設定本体も渡す
        conf = Conf(self._conf_file)
        self._conf_data = conf.data
        self._models = conf.models
        self._model = ''

        super().__init__(app, req)

        logger.debug(
            "conf_file={}, model_name={}", self._conf_file, self._model_name
        )

    DEF_MSG = 'MIDI ファイルを選んでください'

    def get(self):
        """
        GET method
        """
        logger.debug('request={}', self.request)

        if self.request.uri != self._url_path:
            self.redirect(self._url_path, permanent=True)
            return

        self._render()

    def _render(self, svg_data='', svg_filename='', msg=DEF_MSG, book=None,
                src_size='', msg_error=False):
        """テンプレートを描画する。

        ``svg_data`` が空なら「ファイル選択」、そうでなければ「生成結果」の
        画面になる。

        SVG は文字列のままテンプレートに埋め込む（別リクエストにすると
        ビューアの初期表示までに 2 往復かかるため）。ただし**寸法は SVG から
        は取り出せない**ので、``book`` に入れて別に渡す。ビューアはこれで
        初期倍率とスクロール位置を決める。

        Parameters
        ----------
        book: dict | None
            ``RollBook`` の寸法（width / height / holes / mm_per_sec）。
            ファイル選択の画面では None。
        src_size: str
            元 MIDI のサイズ（'12.3 KB'）。ファイル名は SVG 名
            （＝ MIDI 名 + '.svg'）に含まれるので渡さない。
        msg_error: bool
            ``msg`` が失敗の知らせなら True（画面上で赤くする）。
        """
        size_limit, size_unit = get_size_unit(self._size_limit)

        self.render(self.HTML_FILE,
                    title=self.TITLE,
                    author=__author__,
                    version=self._version,
                    copyright_year=__copyright_year__,
                    urlprefix=self._urlprefix,
                    size_limit=size_limit,
                    size_unit=size_unit,
                    # 表示用に丸めた値とは別に、素のバイト数も渡す。
                    # JS が送信前に大きさを比べるのに使う。
                    size_limit_bytes=self._size_limit,
                    msg_error=msg_error,
                    uploaded_names=self.uploaded_midi_names(),
                    models=self._models,
                    models_data=self._conf_data,
                    svg_data=svg_data,
                    svg_filename=svg_filename,
                    book=book or {},
                    src_size=src_size,
                    msg=msg)

    async def post(self):
        """
        POST method
        """
        logger.debug(dir(self.request))

        file1 = self.request.files['file1'][0]
        file1_fname = file1['filename']
        file1_path = self._webroot / 'midi' / file1_fname
        svg1_fname = f'{file1_fname}.svg'
        svg1_path = self._webroot / 'svg' / svg1_fname

        self._model = self.get_argument('model')
        logger.debug('model=\'{}\'', self._model)

        rollbook = RollBook(self._model, self._conf_file)

        # 同じ名前が既にあるなら、確かめてからでないと置き換えない。
        # かつては送られてきた中身を捨てて古いほうを解析していたので、
        # MIDI を直して同じ名前で上げ直すと**前回の結果がそのまま返っていた**。
        # 成功したように見えるぶん、エラーになるより質が悪い。
        # 画面は storgan.js が先に訊くので、ここへは来ない。
        if file1_path.exists() and self.get_argument('overwrite', '') != '1':
            self._render(
                msg=f'{file1_fname} は既にあります。'
                    '置き換えるか、名前を変えてください。',
                msg_error=True,
            )
            return

        file1_path.write_bytes(file1['body'])

        result = self.get_filesize(file1_path)
        assert result is not None
        f_size, unit = result
        src_size = f'{f_size:.1f} {unit}'

        try:
            svg_data = rollbook.parse_to_file(file1_path, svg1_path)
        except Exception as e:
            # 捕まえないと tornado 既定の 500 ページに置き換わり、
            # 画面ごと失われて選び直すこともできなくなる。
            logger.error(exmsg(e))

            # 読めなかったものは残さない。残すと、次に同じ名前で正しい
            # ファイルを送るたびに「既にあります」と言われることになる。
            file1_path.unlink(missing_ok=True)

            self._render(
                msg=f'{file1_fname} を読み込めませんでした。'
                    'MIDI ファイルではないか、壊れている可能性があります。',
                msg_error=True,
            )
            return

        logger.debug('len(svg_data)={}', len(svg_data))

        self._render(
            svg_data=svg_data,
            svg_filename=svg1_fname,
            src_size=src_size,
            book={
                'width': round(rollbook.width, 2),
                'height': round(rollbook.height, 2),
                'holes': rollbook.hole_count,
                'mm_per_sec': rollbook.mm_per_sec,
            },
        )
