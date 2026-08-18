#
# (c) 2026 Yoichi Tanibayashi
#
"""ダウンロードと試聴のハンドラ（TODO-075）。

どれも「置き場のファイルを引いて、その場で作って返す」だけで、画面は
持たない。`Handler1`（ロールブックを作る画面）とは役割が違うので分けた。

**URL は 4 つとも別にしてある。** 同じ名前で中身の違う MIDI が出回らない
ようにするため（それぞれの docstring に理由がある）。

依存は一方向に保つこと::

    base_handler.py → handler1.py / download.py / history.py /
                      config_handler.py
"""
import tornado.web

from .audition import playable_midi_bytes
from .base_handler import StorganBaseHandler
from .mylog import exmsg, getLogger
from .transpose import (
    transpose_midi_bytes,
    transposed_midi_name,
    transposed_midi_zip_bytes,
    transposed_zip_name,
)


class Download(StorganBaseHandler):
    """生成した SVG と、アップロードした MIDI をダウンロードする。

    URL は `/download/<name>`（SVG）と `/download/midi/<name>`。
    SVG 側に種別が入っていないのは、生成結果の画面のリンクが
    元からこの形だったため。**どちらの置き場かはルートが
    `kind` で渡す**（URL から読み取らない）。
    """

    __log = getLogger(__qualname__)

    def initialize(self, kind: str = 'svg') -> None:
        """置き場の種別を受け取る（`WebServer` のルート定義から）。

        Args:
            kind (str): 'midi' か 'svg'。
        """
        self._kind = kind

    def get(self, fname: str = ''):
        """ファイルを返す。

        Args:
            fname (str): ファイル名。URL から来る。
        """
        self.__log.debug('kind={}, fname={}', self._kind, fname)

        path_name = self.stored_file(self._kind, fname)

        self.__log.debug('path_name={}', path_name)

        # write() は応答へ積むだけで finish() まで送り出さないので、
        # 分けて読んでも同じ量がメモリに載る（TODO-096）
        self.finish_download(
            path_name.read_bytes(),
            'application/octet-stream',
            path_name.name,
        )


class DownloadTransposedMidi(StorganBaseHandler):
    """アップロード済みの MIDI を、指定の調に移調してダウンロードする（TODO-042）。

    URL は `/download/midi-transpose/<name>?t=<半音数>`。

    **`Download` とは別にしてある。** あちらは実在するファイルを
    そのまま返す作りで、こちらは「名前 ＋ 移調量」からその場で作る
    別物。**作った MIDI は保存しない**（`webroot/midi/` を太らせない）。
    """

    __log = getLogger(__qualname__)

    def get(self, fname: str = ''):
        """元の MIDI を移調して返す。

        Args:
            fname (str): 元の MIDI のファイル名。URL から来る。
        """
        self.__log.debug('fname={}, t={}', fname, self.get_argument('t', ''))

        path_name = self.stored_file('midi', fname)
        semitones = self.transpose_arg()

        try:
            data = transpose_midi_bytes(path_name, semitones)
        except Exception as e:
            # 読めない MIDI など。既定の 500 ページより理由が分かる
            self.__log.error(exmsg(e))
            raise tornado.web.HTTPError(
                400, reason='cannot transpose'
            ) from e

        self.finish_download(
            data,
            'application/octet-stream',
            transposed_midi_name(path_name.name, semitones),
        )


class DownloadTransposedMidiZip(StorganBaseHandler):
    """移調した MIDI を、まとめて ZIP でダウンロードする（TODO-050）。

    URL は `/download/midi-transpose-zip/<name>?t=-5,-2,0,3`。

    **半音数はクエリで受け取る**（候補をサーバー側で作り直さない）。
    `DownloadTransposedMidi` と同じく、名前と半音数だけから作れる。
    **作った MIDI も ZIP も保存しない。**
    """

    __log = getLogger(__qualname__)

    # 候補は最大 7 行（TODO-041）。外から好きな数を投げられると
    # 1 リクエストで何百回も移調させられるので、余裕を見て頭打ちにする
    MAX_ITEMS = 32

    def get(self, fname: str = ''):
        """元の MIDI を、指定された調ぶんだけ移調して ZIP で返す。

        Args:
            fname (str): 元の MIDI のファイル名。URL から来る。
        """
        transpose = self.get_argument('t', '')
        self.__log.debug('fname={}, t={}', fname, transpose)

        path_name = self.stored_file('midi', fname)
        semitones_list = self._parse_transpose(transpose)

        try:
            data = transposed_midi_zip_bytes(path_name, semitones_list)
        except Exception as e:
            # 読めない MIDI など。既定の 500 ページより理由が分かる
            self.__log.error(exmsg(e))
            raise tornado.web.HTTPError(
                400, reason='cannot transpose'
            ) from e

        self.finish_download(
            data,
            'application/zip',
            transposed_zip_name(path_name.name),
        )

    def _parse_transpose(self, transpose: str) -> list[int]:
        """``-5,-2,0,3`` を整数の並びに直す。

        重複は**最初に出たほうを残して削除する**（同じ名前の要素が
        2 つ入った ZIP を作らないため）。並び順は画面の表と同じ。

        Raises:
            tornado.web.HTTPError: 空、整数でない、多すぎる場合は 400。
        """
        try:
            values = [int(s) for s in transpose.split(',')]
        except ValueError as e:
            self.__log.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='bad transpose') from e

        # dict は挿入順を保つので、これで重複だけ削除できる
        uniq = list(dict.fromkeys(values))

        if not uniq or len(uniq) > self.MAX_ITEMS:
            raise tornado.web.HTTPError(400, reason='bad transpose')

        return uniq


class AuditionMidi(StorganBaseHandler):
    """ブラウザで試聴するための MIDI を返す（TODO-063）。

    URL は `/audition/midi/<name>?t=<半音数>&model=<機種名>`。

    **`DownloadTransposedMidi` とは別にしてある。** あちらはダウンロード用の
    素材（元のファイルを移調しただけ）で、こちらは実機の再現
    （音階に無い音は鳴らない）。目的が違うものを同じ URL から返すと、
    同じ名前で中身の違う MIDI が 2 種類出回ることになる。

    **`Content-Disposition` は付けない**（ダウンロードさせない。試聴のための
    ものなので、欲しくなったらここに足すのが答え）。**保存もしない。**
    """

    __log = getLogger(__qualname__)

    def get(self, fname: str = ''):
        """鳴る音だけの MIDI を返す。

        Args:
            fname (str): 元の MIDI のファイル名。URL から来る。
        """
        model = self.get_argument('model', '')
        self.__log.debug('fname={}, t={}, model={}',
                         fname, self.get_argument('t', ''), model)

        path_name = self.stored_file('midi', fname)
        semitones = self.transpose_arg()

        try:
            data = playable_midi_bytes(path_name, model, semitones)
        except ValueError as e:
            # 知らない機種名、設定の項目が足りない
            self.__log.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='bad model') from e
        except Exception as e:
            # 読めない MIDI など。既定の 500 ページより理由が分かる
            self.__log.error(exmsg(e))
            raise tornado.web.HTTPError(400, reason='cannot audition') from e

        self.set_header('Content-Type', 'audio/midi')
        self.write(data)
        self.finish()
