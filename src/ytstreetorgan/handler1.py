#
# (c) 2026 Yoichi Tanibayashi
#
import os
import tornado.web
from loguru import logger
from .rollbook import RollBook
from .conf import Conf


__author__ = 'Yoichi Tanibayashi'


class Download(tornado.web.RequestHandler):
    """
    Download SVG file
    """
    def __init__(self, app, req):
        """ Constructor """
        self._dbg = app.settings.get('debug')
        logger.debug('debug={}', self._dbg)
        logger.debug('app={}', app)
        logger.debug('req={}', req)

        self._webroot = app.settings.get('webroot')
        logger.debug('webroot={}', self._webroot)

        self._workdir = app.settings.get('workdir')
        logger.debug('workdir={}', self._workdir)

        self._size_limit = app.settings.get('size_limit')
        logger.debug('size_limit={}', self._size_limit)

        # [!! 重要 !!] 末尾の「/」
        self._url_path = app.settings.get('url_prefix_handler1') + '/'

        self._version = app.settings.get('version')

        self._model = ''

        self._model_name = RollBook.DEF_MODEL_NAME
        self._conf_file = RollBook.DEF_CONF_FILE

        self._rollbook = RollBook(self._model_name, self._conf_file,
                                  debug=self._dbg)

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

        path_name = '%s/svg/%s' % (self._webroot, fname)
        logger.debug('path_name={}', path_name)

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition',
                        'attachment; filename=' + fname)

        buf_size = 4096
        with open(path_name, 'r') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)

        self.finish()


class Handler1(tornado.web.RequestHandler):
    """
    Web handler1
    """
    TITLE = 'Street Organ Roll Book Maker'

    HTML_FILE = 'storgan.html'

    def __init__(self, app, req):
        """ Constructor """
        self._dbg = app.settings.get('debug')
        logger.debug('debug={}', self._dbg)
        logger.debug('app={}', app)
        logger.debug('req={}', req)

        self._webroot = app.settings.get('webroot')
        logger.debug('webroot={}', self._webroot)

        self._workdir = app.settings.get('workdir')
        logger.debug('workdir={}', self._workdir)

        self._size_limit = app.settings.get('size_limit')
        logger.debug('size_limit={}', self._size_limit)

        # [!! 重要 !!] 末尾の「/」
        self._url_path = app.settings.get('url_prefix_handler1') + '/'

        self._version = app.settings.get('version')

        self._conf_file = RollBook.DEF_CONF_FILE
        self._model_name = RollBook.DEF_MODEL_NAME
        logger.debug("conf_file={}, model_name={}", self._conf_file, self._model_name)

        self._models = Conf(self._conf_file).models
        
        self._rollbook = RollBook(
            self._model_name, self._conf_file, debug=self._dbg
        )

        super().__init__(app, req)

    def get_size_unit(self, f_size):
        """
        Parameters
        ----------
        f_size: int
            file size (bytes)
        """
        size_unit = ['B', 'KB', 'MB', 'GB', 'TB']

        while f_size >= 1024:
            size_unit.pop(0)
            f_size /= 1024

        return f_size, size_unit[0]

    def get_filesize(self, file_path: str) -> tuple[float, str] | None:
        """
        Parameters
        ----------
        file_path: str

        """
        if not os.path.exists(file_path):
            return None

        f_size = os.path.getsize(file_path)

        return self.get_size_unit(f_size)

    def get(self, svg_data='', svg_filename='',
            msg='Please select a MIDI file'):
        """
        GET method and rendering
        """
        logger.debug('request={}', self.request)

        if self.request.uri != self._url_path:
            self.redirect(self._url_path, permanent=True)
            return

        size_limit, size_unit = self.get_size_unit(self._size_limit)

        self.render(self.HTML_FILE,
                    title=self.TITLE,
                    author=__author__,
                    version=self._version,
                    copyright_year='2021',
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
        file1_path = '%s/midi/%s' % (self._webroot, file1_fname)
        svg1_fname = '%s.svg' % (file1_fname)
        svg1_path = '%s/svg/%s' % (self._webroot, svg1_fname)

        self._model = self.get_argument('model')
        logger.debug('model=\'{}\'', self._model)

        self._rollbook = RollBook(self._model, self._conf_file)
        
        if not os.path.exists(file1_path):
            with open(file1_path, mode='wb') as f:
                f.write(file1['body'])

        result = self.get_filesize(file1_path)
        assert result is not None
        f_size, unit = result
        msg = '%s (%.1f %s)' % (file1['filename'], f_size, unit)

        svg_data = self._rollbook.parse(file1_path)
        logger.debug('svg_data=%a', svg_data)

        with open(svg1_path, mode='w') as f:
            f.write(svg_data)

        self.get(svg_data=svg_data, svg_filename=svg1_fname, msg=msg)
