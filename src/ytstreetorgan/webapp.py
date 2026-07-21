#
# (c) 2026 Yoichi Tanibayashi
#
import os
import tornado.ioloop
import tornado.httpserver
import tornado.web
from loguru import logger
from . import __version__
from .conf import Conf
from .mylog import exmsg
from .handler1 import Handler1, Download
from .config_handler import ConfigHandler


class WebServer:
    """
    Web application server
    """
    DEF_PORT = 10081

    DEF_WEBROOT = './webroot'
    URL_PREFIX = '/storgan2'
    URL_PREFIX_HANDLER1 = '/handler1'

    DEF_WORKDIR = '/tmp'

    DEF_SIZE_LIMIT = 100 * 1024 * 1024  # 100MB

    def __init__(
        self, port=DEF_PORT,
        urlprefix=URL_PREFIX,
        webroot=DEF_WEBROOT,
        workdir=DEF_WORKDIR,
        size_limit=DEF_SIZE_LIMIT,
        version=__version__,
        debug=False
    ):
        """ Constructor

        Parameters
        ----------
        port: int
            port number

        urlprefix: str

        webroot: str

        workdir: str

        size_limit: int
            max upload size
        version: str
            version string
        """
        # loggerInit(debug)
        logger.debug(
            'port={}, urlprefix={}, webroot={}, workdir={}, size_limit={}',
            port, urlprefix, webroot, workdir, size_limit
        )
        logger.debug('version={}', version)

        self._port = port
        self._urlprefix = urlprefix
        self._urlprefix_handler1 = self._urlprefix + self.URL_PREFIX_HANDLER1
        self._webroot = webroot
        self._workdir = workdir
        self._size_limit = size_limit
        self._version = version

        self._models = Conf().models
        logger.info('_models={}', self._models)

        try:
            os.makedirs(self._workdir, exist_ok=True)
        except Exception as ex:
            logger.error(exmsg(ex))
            raise ex

        self._app = tornado.web.Application(
            [
                (r'/', Handler1),
                (r'%s' % self._urlprefix, Handler1),
                (r'%s/' % self._urlprefix, Handler1),
                (r'%s/config.*' % self._urlprefix, ConfigHandler),
                (r'%s.*' % self._urlprefix_handler1, Handler1),
                (r'%s/download/.*' % self._urlprefix, Download),
            ],
            static_path=os.path.join(self._webroot, "static"),
            static_url_prefix=self._urlprefix + '/static/',
            template_path=os.path.join(self._webroot, "templates"),
            autoreload=True,
            # xsrf_cookies=False,

            # url_prefix_handler1=self._urlprefix_handler1,
            url_prefix_handler1=self._urlprefix,

            webroot=self._webroot,
            workdir=self._workdir,
            urlprefix=self._urlprefix,
            size_limit=self._size_limit,
            version=self._version,
            models=self._models,
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
