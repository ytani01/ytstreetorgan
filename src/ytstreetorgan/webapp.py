#
# (c) 2026 Yoichi Tanibayashi
#
import os
import tornado.ioloop
import tornado.httpserver
import tornado.web
from .handler1 import Handler1, Download
from loguru import logger
from .conf import Conf


class WebServer:
    """
    Web application server
    """
    DEF_PORT = 10081

    DEF_WEBROOT = './webroot'
    URL_PREFIX = '/storgan'
    URL_PREFIX_HANDLER1 = URL_PREFIX + '/handler1'

    DEF_WORKDIR = '/tmp/storgan'

    DEF_SIZE_LIMIT = 100*1024*1024  # 100MB

    def __init__(
        self, port=DEF_PORT,
        webroot=DEF_WEBROOT, workdir=DEF_WORKDIR,
        size_limit=DEF_SIZE_LIMIT,
        version='current',
        debug=False
    ):
        """ Constructor

        Parameters
        ----------
        port: int
            port number
        webroot: str

        workdir: str

        size_limit: int
            max upload size
        version: str
            version string
        """
        self._dbg = debug
        logger.info('port={}, webroot={}, workdir={}, size_limit={}',
                    port, webroot, workdir, size_limit)
        logger.info('version={}', version)

        self._port = port
        self._webroot = webroot
        self._workdir = workdir
        self._size_limit = size_limit
        self._version = version

        self._models = Conf().models
        logger.info('_models={}', self._models)

        try:
            os.makedirs(self._workdir, exist_ok=True)
        except Exception as ex:
            raise ex

        self._app = tornado.web.Application(
            [
                (r'/', Handler1),
                (r'%s' % self.URL_PREFIX, Handler1),
                (r'%s/' % self.URL_PREFIX, Handler1),
                (r'%s.*' % self.URL_PREFIX_HANDLER1, Handler1),
                (r'%s/download/.*' % self.URL_PREFIX, Download),
            ],
            static_path=os.path.join(self._webroot, "static"),
            static_url_prefix=self.URL_PREFIX + '/static/',
            template_path=os.path.join(self._webroot, "templates"),
            autoreload=True,
            # xsrf_cookies=False,

            # url_prefix_handler1=self.URL_PREFIX_HANDLER1,
            url_prefix_handler1=self.URL_PREFIX,

            webroot=self._webroot,
            workdir=self._workdir,
            size_limit=self._size_limit,
            version=self._version,
            models=self._models,

            debug=self._dbg
        )
        logger.debug('app={}', self._app.__dict__)

        self._svr = tornado.httpserver.HTTPServer(
            self._app, max_buffer_size=self._size_limit
        )
        logger.debug('svr={}', self._svr.__dict__)

    def main(self):
        """ main """
        logger.debug('')

        self._svr.listen(self._port)
        logger.info('start server: run forever ..')

        tornado.ioloop.IOLoop.current().start()

        logger.debug('done')
