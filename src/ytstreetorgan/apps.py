#
# (c) 2026 Yoichi Tanibayashi
#
"""CLI の各サブコマンドの中身。

**`__main__.py` は click の定義だけの薄い層に保つ**という決めごとがある
（テストしやすくするため）。ロジックはここに置く。
"""
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from loguru import logger
from ytmidilib import NoteInfo, Parser, Player

from .conf import Conf, ModelConf, validate_config
from .rollbook import RollBook, merge_overlapping_notes, note2scale
from .transpose import (
    TransposeCandidate,
    parse_transpose_arg,
    plan_transpose,
    transpose_notices,
)


def transpose_summary(
    cand: TransposeCandidate, model_name: str, auto: bool
) -> str:
    """どう移調したかを 1 行にする。

    **移調量を生で見せない。** `-24` だけでは何が起きたか分からないので、
    「調 ±0・2 オクターブ下」に分けて添える。
    """
    key = '±0' if cand['key'] == 0 else f'{cand["key"]:+d}'
    octave = '±0' if cand['octave'] == 0 else f'{cand["octave"]:+d}'
    how = 'おまかせで' if auto else ''

    if cand['transpose'] == 0:
        head = f'[{model_name}] {how}移調しません'
    else:
        head = (
            f'[{model_name}] {how}移調 {cand["transpose"]:+d} 半音'
            f'（調 {key}・オクターブ {octave}）'
        )

    return (
        f'{head} → 鳴らせる音符 {cand["notes"]} 個'
        f'（{cand["note_pct"]:.1f}%、音の長さ {cand["sec_pct"]:.1f}%）'
    )


def format_transpose_table(
    candidates: Sequence[TransposeCandidate], chosen: int | None = None
) -> str:
    """移調の候補を、端末に出す表にする（TODO-039）。

    **移調量を生で見せない。** 「-18」では何が起きるか分からないので、
    「調 +6・2 オクターブ下」に分けて出す。並び順は鳴らせる音符の数。

    Args:
        candidates (Sequence[TransposeCandidate]): `transpose_candidates()`
            が返したもの。
        chosen (int | None): いま選ばれている移調量。その行に印を付ける。

    Returns:
        str: 複数行の文字列（末尾に改行は付けない）。
    """
    if not candidates:
        return '移調の候補がありません（音符が読めませんでした）。'

    lines = [
        '  調  ｵｸﾀｰﾌﾞ   移調     音符   音の長さ      音域',
        '  ---------------------------------------------------',
    ]
    for c in candidates:
        mark = ''
        if c['key'] == 0:
            mark += ' 調そのまま'
        if chosen is not None and c['transpose'] == chosen:
            mark += ' ←選択'

        lines.append(
            f'  {c["key"]:+3d} {c["octave"]:+6d} {c["transpose"]:+6d} '
            f'{c["note_pct"]:7.1f}% {c["sec_pct"]:8.1f}% '
            f'{c["lo"]:5d}-{c["hi"]:<5d}{mark}'
        )

    for notice in transpose_notices(list(candidates)):
        lines.append(f'  * {notice}')

    return '\n'.join(lines)


class RollBookApp:
    """`rollbook` コマンド。MIDI から SVG を作ってファイルに書く。

    Attributes:
        DEF_OUT_DIR: `-o` を省略したときの出力先。
    """
    DEF_OUT_DIR = '~/Desktop'

    def __init__(
        self, midi_file: str, conf_file: str,
        model_name: str,
        channel: Sequence[int] = (),
        out_file: str | None = None,
        transpose: int | str = 0,
    ) -> None:
        """出力先を決めて、`RollBook` を用意する。

        Args:
            midi_file (str): 対象の MIDI ファイル。
            conf_file (str): 設定ファイル。空なら `Conf` が探す。
            model_name (str): 機種名。
            channel (Sequence[int]): 対象の MIDI チャンネル（空なら全部）。
            out_file (str | None): 出力先。**省略すると
                `DEF_OUT_DIR` に「MIDI 名 + .svg」で書く。**
            transpose (int | str): 移調する半音数。``'auto'`` なら
                候補の 1 位を選ぶ（TODO-039）。

        Note:
            version と debug は受け取っていたが使っていなかったので外した
            （ログの初期化は `__main__` の `loggerInit()` が済ませている）。
        """
        logger.debug('midi_file={}, conf_file={}', midi_file, conf_file)
        logger.debug('model_name={}', model_name)
        logger.debug('channel={}', channel)
        logger.debug('out_file={}', out_file)
        logger.debug('transpose={}', transpose)

        self._midi_file = midi_file
        self._conf_file = conf_file
        self._model_name = model_name
        self._channel = list(channel)
        self._transpose = transpose

        if out_file:
            # 明示指定されたパスはそのまま使う（相対パスは cwd 基準）
            self._out_file = str(Path(out_file).expanduser())
        else:
            # 未指定なら DEF_OUT_DIR に <MIDIファイル名>.svg で出す
            name = Path(f'{self._midi_file}.svg').name
            self._out_file = str((Path(self.DEF_OUT_DIR) / name).expanduser())
        logger.debug('[fix] out_file={}', self._out_file)

        self._rollbook = RollBook(
            self._model_name, self._conf_file, self._transpose
        )

    def main(self) -> None:
        """MIDI を解析して SVG を書き出す。

        移調の候補は**指定の有無によらず**出す。1 つに定まらないことが
        多いので、選び直せるように見せておく（TODO-039）。
        """
        logger.debug('')

        self._rollbook.parse_to_file(
            self._midi_file, self._out_file, self._channel
        )

        rb = self._rollbook
        print(f'移調: {rb.transpose:+d} 半音'
              f'  鳴らせる音符: {rb.hole_note_count}/{rb.note_count}',
              flush=True)
        print(format_transpose_table(rb.candidates, rb.transpose), flush=True)

    def end(self) -> None:
        """後片付け（いまは何もしない）。`main()` と対で呼ぶ。"""


class MidiApp:
    """`parse` と `play` コマンド。MIDI を解析して、表示または再生する。"""
    def __init__(self, midi_file: str,
                 channel: Sequence[int] = (),
                 parse_only: bool = False,
                 visual_flag: bool = False,
                 rate: int = Player.DEF_RATE,
                 sec_min: float = Player.SEC_MIN,
                 sec_max: float = Player.SEC_MAX,
                 pos_sec: float = 0.0,
                 model_name: str | None = None,
                 conf_file: str = RollBook.DEF_CONF_FILE,
                 transpose: int | str = 0,
                 debug: bool = False) -> None:
        """解析器と再生器を用意する。

        Args:
            midi_file (str): 対象の MIDI ファイル。
            channel (Sequence[int]): 対象の MIDI チャンネル（空なら全部）。
            parse_only (bool): 解析結果を出すだけで再生しない（`parse`）。
            visual_flag (bool): 解析結果を図にして出す。
            rate (int): 再生のサンプリング周波数 [Hz]。
            sec_min (float): 音の長さの下限 [秒]。
            sec_max (float): 音の長さの上限 [秒]。
            pos_sec (float): 再生を始める位置 [秒]。
            model_name (str | None): 機種名。指定すると、その機種の音階に
                無い MIDI ノート番号を再生前に取り除く（ロールブックで
                穴が開かないのと同じ音だけを鳴らす）。`None` なら変換しない。
            conf_file (str): 設定ファイル。空なら `Conf` が探す。
                `model_name` を指定したときだけ使う。
            transpose (int | str): 移調する半音数。``'auto'`` なら候補の
                1 位を選ぶ（TODO-039）。**`model_name` と併用する**
                （どの機種に合わせるか決まらないと候補を出せない）。
            debug (bool): 解析器と再生器にそのまま渡す。

        Raises:
            ValueError: `model_name` を指定したのに設定に無い、設定の項目が
                足りない（`RollBook.__init__` と同じ理由）、または
                `transpose` が整数にも ``'auto'`` にもならないとき。
        """
        self._dbg = debug
        logger.debug('midi_file={}, channel={}', midi_file, channel)
        logger.debug('parse_only={}, visual_flag={}', parse_only, visual_flag)
        logger.debug('rate={}', rate)
        logger.debug('sec_min/max={}/{}', sec_min, sec_max)
        logger.debug('pos_sec={}', pos_sec)
        logger.debug('model_name={}, conf_file={}', model_name, conf_file)
        logger.debug('transpose={}', transpose)

        self._midi_file = midi_file
        self._channel = list(channel)
        self._parse_only = parse_only
        self._visual_flag = visual_flag
        self._rate = rate
        self._sec_min = sec_min
        self._sec_max = sec_max
        self._pos_sec = pos_sec

        # 検証は RollBook と同じものを使う（メッセージも揃う）。
        # **型注釈は省かないこと**（`RollBook.__init__` と同じ理由）
        self._transpose_req: int | Literal['auto'] = parse_transpose_arg(
            transpose
        )
        self._transpose = 0 if self._transpose_req == 'auto' else int(
            self._transpose_req
        )

        self._model_name = model_name
        self._model_conf: ModelConf | None = None
        self._candidates: list[TransposeCandidate] = []
        self._chosen: TransposeCandidate | None = None
        self._merged_count = 0
        if self._model_name:
            conf = Conf(conf_file).get(self._model_name)
            if not conf:
                raise ValueError(f"機種 '{self._model_name}' は設定にありません")

            valid, msg = validate_config(conf)
            if not valid:
                raise ValueError(
                    f"機種 '{self._model_name}' の設定が不正です: {msg}"
                )
            self._model_conf = conf

        self._parser = Parser(debug=self._dbg)
        self._player = Player(rate=self._rate, debug=self._dbg)

    def _convert_for_model(self, note_info: list[NoteInfo]) -> list[NoteInfo]:
        """機種に合わせて変換する。重なりの統合 → 移調 → 音階での絞り込み。

        ロールブックは音階に無い音を破線で描くだけで穴を開けない
        （`HoleInfo.scale` が -1）。再生でも同じ音だけを鳴らして、
        実機で聞こえる音を確かめられるようにする。

        `merge_overlapping_notes()` は、同じ MIDI ノート番号の重なりを
        1 つにまとめる（TODO-038）。実機は 1 つの音に 1 本のパイプしか
        無いため、複数パートが同じ高さを同時に鳴らしても実際に聞こえるのは
        1 本ぶんになる。

        移調（TODO-039）は `'auto'` なら候補の 1 位を選ぶ。**候補は移調を
        指定していなくても作る**（表として見せるため）。
        """
        assert self._model_conf is not None

        base_note = self._model_conf.get('base_note', 0)
        notes = self._model_conf.get('notes', [])

        merged = merge_overlapping_notes(note_info)
        # 候補の割合はこの数を分母にしている。画面の「◯/◯」も揃えること
        self._merged_count = len(merged)

        # 移調をどうするかは `plan_transpose()` が決める（TODO-043）。
        # `RollBook` も同じものを呼ぶので、手順はここに写さない
        plan = plan_transpose(merged, self._model_conf, self._transpose_req)
        self._transpose = plan.transpose
        self._candidates = plan.candidates
        self._chosen = plan.chosen

        converted = [
            ni for ni in plan.notes
            if note2scale(ni.note, base_note, notes) >= 0
        ]

        # **どう変換したのかを INFO で残す。** 候補の表は `parse` だけなので、
        # `play` ではこれが唯一の手がかりになる
        if self._chosen is not None:
            logger.info(
                transpose_summary(
                    self._chosen, self._model_name or '',
                    self._transpose_req == 'auto',
                )
            )
        logger.debug(
            '{} -> {} (merge) -> {} (transpose={:+d}, scale)',
            len(note_info), len(merged), len(converted), self._transpose
        )
        return converted

    def main(self) -> None:
        """解析し、必要なら図にして出し、`parse_only` でなければ再生する。"""
        logger.debug('')

        parsed_data = self._parser.parse(self._midi_file, self._channel)

        if self._model_conf is not None:
            parsed_data['note_info'] = self._convert_for_model(
                parsed_data['note_info']
            )
            # 候補の表は `parse`（調べるのが目的）だけ。再生中に 12 行流すと
            # 邪魔なので、`play` は上の INFO 1 行で済ませる
            if self._parse_only:
                # 分母は**統合後**の数。候補の割合と揃えないと食い違って見える
                print(f'機種: {self._model_name}'
                      f'  移調: {self._transpose:+d} 半音'
                      f'  鳴らせる音符: {len(parsed_data["note_info"])}'
                      f'/{self._merged_count}',
                      flush=True)
                print(
                    format_transpose_table(self._candidates, self._transpose),
                    flush=True
                )

        # 音符 1 つずつの一覧は `parse`（中身を見るのが目的）だけ出す。
        # `play` のときは -d を付けた場合のみ、DEBUG のログとして出る
        if self._parse_only:
            for i, data in enumerate(parsed_data['note_info']):
                print(f'({i:4d}) {data}', flush=True)
        else:
            for i, data in enumerate(parsed_data['note_info']):
                logger.debug('({:4d}) {}', i, data)

        print('channel_set=', parsed_data['channel_set'], flush=True)

        if self._visual_flag:
            v_data = self._parser.mk_visual(parsed_data['note_info'])
            print()
            self._parser.print_visual(v_data, parsed_data['channel_set'])

        if self._parse_only:
            return

        # `Player.play()` は既定では何も出さない（ytmidilib 0.1.0。
        # 音符ごとの行は向こうの DEBUG ログへ回った）
        self._player.play(parsed_data, self._pos_sec,
                          self._sec_min, self._sec_max)

    def end(self) -> None:
        """後片付け（いまは何もしない）。`main()` と対で呼ぶ。"""
