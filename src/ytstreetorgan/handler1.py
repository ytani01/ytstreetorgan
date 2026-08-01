#
# (c) 2026 Yoichi Tanibayashi
#
import os

import tornado.web
from loguru import logger

from . import __author__, __copyright_year__
from .conf import Conf
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

        self._webroot = app.settings.get('webroot')
        logger.debug('webroot={}', self._webroot)

        self._workdir = app.settings.get('workdir')
        logger.debug('workdir={}', self._workdir)

        self._size_limit = app.settings.get('size_limit')
        logger.debug('size_limit={}', self._size_limit)

        # [!! 重要 !!] 末尾の「/」
        self._url_path = app.settings.get('url_prefix_handler1') + '/'

        self._version = app.settings.get('version')

        super().__init__(app, req)

    def get_filesize(self, file_path: str) -> tuple[float, str] | None:
        """
        Parameters
        ----------
        file_path: str
        """
        if not os.path.exists(file_path):
            return None

        f_size = os.path.getsize(file_path)
        return get_size_unit(f_size)


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

        path_name = f'{self._webroot}/svg/{fname}'
        logger.debug('path_name={}', path_name)

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition',
                        'attachment; filename=' + fname)

        buf_size = 4096
        with open(path_name) as f:
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

        self._models = Conf(self._conf_file).models
        self._model = ''

        super().__init__(app, req)

        logger.debug(
            "conf_file={}, model_name={}", self._conf_file, self._model_name
        )

    def get(
        self, svg_data='', svg_filename='', msg='Please select a MIDI file'
    ):
        """
        GET method and rendering
        """
        logger.debug('request={}', self.request)

        if self.request.uri != self._url_path:
            self.redirect(self._url_path, permanent=True)
            return

        size_limit, size_unit = get_size_unit(self._size_limit)

        self.render(self.HTML_FILE,
                    title=self.TITLE,
                    author=__author__,
                    version=self._version,
                    copyright_year=__copyright_year__,
                    urlprefix=self._urlprefix,
                    size_limit=size_limit,
                    size_unit=size_unit,
                    models=self._models,
                    svg_data=svg_data,
                    svg_filename=svg_filename,
                    msg=msg)

    async def post(self):
        """
        POST method
        """
        logger.debug(dir(self.request))

        file1 = self.request.files['file1'][0]
        file1_fname = file1['filename']
        file1_path = f'{self._webroot}/midi/{file1_fname}'
        svg1_fname = f'{file1_fname}.svg'
        svg1_path = f'{self._webroot}/svg/{svg1_fname}'

        self._model = self.get_argument('model')
        logger.debug('model=\'{}\'', self._model)

        rollbook = RollBook(self._model, self._conf_file)

        if not os.path.exists(file1_path):
            with open(file1_path, mode='wb') as f:
                f.write(file1['body'])

        result = self.get_filesize(file1_path)
        assert result is not None
        f_size, unit = result
        msg = '{} ({:.1f} {})'.format(file1['filename'], f_size, unit)

        svg_data = rollbook.parse_to_file(file1_path, svg1_path)
        logger.debug('svg_data={}', svg_data)

        self.get(svg_data=svg_data, svg_filename=svg1_fname, msg=msg)
