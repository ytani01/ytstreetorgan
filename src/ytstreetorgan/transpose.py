#
# (c) 2026 Yoichi Tanibayashi
#
"""移調（曲全体を上下させて、機種の音階に合わせる）。

**`rollbook.py` から独立させてある**（TODO-043）。移調は「どの高さで
鳴らすか」だけの話で、穴の位置や SVG の描き方とは関係が無い。`play`
（`MidiApp`）も同じ手順を使うので、ブックの組み立てから切り離してある。

依存は一方向に保つこと::

    conf.py → transpose.py → rollbook.py → apps.py / handler1.py

**このモジュールから `rollbook.py` を import しない**（循環する）。
`note2scale()` と `merge_overlapping_notes()` を向こうに残してあるのは
そのため。前者は穴の位置を決めるためのもので、後者は「実機は 1 音に
1 パイプ」という別の話（TODO-038）。
"""
from collections.abc import Sequence
from typing import Literal, NamedTuple, TypedDict

from loguru import logger
from ytmidilib import NoteInfo

from .conf import ModelConf


def playable_notes(conf: ModelConf) -> set[int]:
    """機種が鳴らせる MIDI ノート番号の集合。

    `note2scale()` はトラック番号（穴の列）が要るときに使う。こちらは
    「鳴らせるかどうか」だけを何万回も調べる用（移調の候補を作るとき）。
    """
    base_note = conf.get('base_note', 0)
    return {base_note + n['offset'] for n in conf.get('notes', [])}


def model_note_range(conf: ModelConf) -> tuple[int, int]:
    """機種が鳴らせる MIDI ノート番号の最低・最高。

    Returns:
        tuple[int, int]: ``(最低, 最高)``。トラックが 1 つも無ければ
            どちらも ``base_note``。
    """
    base_note = conf.get('base_note', 0)
    notes = conf.get('notes', [])
    if not notes:
        return (base_note, base_note)

    offsets = [n['offset'] for n in notes]
    return (base_note + min(offsets), base_note + max(offsets))


def transpose_notes(
    note_info: list[NoteInfo], semitones: int
) -> list[NoteInfo]:
    """全 MIDI ノート番号に ``semitones`` を足した写しを返す（移調）。

    曲を丸ごと上下させる。機種の設定を読まないので、`RollBook` からも
    `MidiApp`（`play`）からも同じように使える。

    Args:
        note_info (list[NoteInfo]): 対象の音符。
        semitones (int): 足す半音数。0 なら写すだけ。

    Returns:
        list[NoteInfo]: 移調後の音符（元のリストは変えない）。
    """
    if semitones == 0:
        return list(note_info)

    return [
        NoteInfo(
            abs_time=ni.abs_time,
            channel=ni.channel,
            note=ni.note + semitones,
            velocity=ni.velocity,
            end_time=ni.end_time,
        )
        for ni in note_info
    ]


def key_label(semitones: int) -> int:
    """移調量を「調の動き」に直す（-5〜+6 の半音数）。

    +7 は -5 と同じ調なので、動きの小さいほうで表す。0 は調が変わらない。
    """
    key = semitones % 12
    return key - 12 if key > 6 else key


class TransposeCandidate(TypedDict):
    """移調の候補 1 つ。**調ごとに 1 つだけ**作る。

    Attributes:
        key: 調の動き（-5〜+6 の半音数）。0 なら**キーが変わらない**。
        octave: どのオクターブに置くか。
        transpose: 合計の半音数（＝実際に足す数）。``key + octave * 12``。
        notes: 鳴らせる音符の数。
        note_pct: 鳴らせる音符の数の割合 [%]。**並び順はこれ**。
        sec_pct: 鳴らせる音符の長さ（秒）の合計の割合 [%]。
            画面では「音の長さ」と呼ぶ（ブック全体の「演奏時間」とは別物）。
        lo: 移調後の最低 MIDI ノート番号。
        hi: 移調後の最高 MIDI ノート番号。
    """

    key: int
    octave: int
    transpose: int
    notes: int
    note_pct: float
    sec_pct: float
    lo: int
    hi: int


class _NoteTally:
    """MIDI ノート番号ごとの「何個あるか・合計で何秒鳴るか」。

    移調量を総当たりするとき、音符 1 つずつ数え直すと重い
    （曲 2000 音 × 移調 100 通り）。ここへ畳んでおくと、1 つの移調量
    あたり高々 128 回で済む。
    """

    def __init__(self, note_info: list[NoteInfo]) -> None:
        self.count_of: dict[int, int] = {}
        self.sec_of: dict[int, float] = {}
        for ni in note_info:
            self.count_of[ni.note] = self.count_of.get(ni.note, 0) + 1
            self.sec_of[ni.note] = self.sec_of.get(ni.note, 0.0) + ni.length()

        self.total_notes = len(note_info)
        self.total_sec = sum(self.sec_of.values())
        self.note_min = min(self.count_of) if self.count_of else 0
        self.note_max = max(self.count_of) if self.count_of else 0

    def score(self, t: int, playable: set[int]) -> TransposeCandidate:
        """移調量 `t` 1 つぶんの成績。"""
        notes = 0
        sec = 0.0
        for n, c in self.count_of.items():
            if n + t in playable:
                notes += c
                sec += self.sec_of[n]

        key = key_label(t)
        return {
            'key': key,
            'octave': (t - key) // 12,
            'transpose': t,
            'notes': notes,
            'note_pct': notes / self.total_notes * 100,
            'sec_pct': (sec / self.total_sec * 100) if self.total_sec else 0.0,
            'lo': self.note_min + t,
            'hi': self.note_max + t,
        }


def transpose_score(
    note_info: list[NoteInfo], conf: ModelConf, semitones: int
) -> TransposeCandidate | None:
    """移調量 1 つぶんの成績を出す（音符が無ければ None）。

    候補に挙がらない移調量（``±0`` や手で指定した値）を、候補と同じ形で
    表に並べるために使う。**候補だけを出すと ±0 に戻れなくなる。**
    """
    if not note_info:
        return None

    return _NoteTally(note_info).score(semitones, playable_notes(conf))


def transpose_candidates(
    note_info: list[NoteInfo], conf: ModelConf
) -> list[TransposeCandidate]:
    """移調の候補を、鳴らせる音符の多い順に返す（TODO-039）。

    移調量を総当たりして、**調ごとに 1 つずつ残す**。

    1. 移調量 `t` の範囲を決める。1 音でも鳴りうるぶんだけ見れば足りる::

           t = (機種の最低 - 曲の最高) 〜 (機種の最高 - 曲の最低)

       **固定幅にしないこと。** 曲が機種より 2 オクターブ以上高いと
       最適値が範囲の端に張り付き、その先を見ていないことに気づけない。
    2. `t` を `t % 12` でグループ分けする（12 個）。同じグループの `t` は
       **調が同じで、違いはオクターブだけ**。
    3. 各グループから、鳴らせる音符が最多の `t` を 1 つ選ぶ。同点なら
       `|t|` が小さいほう。これで「その調で、いちばん音域に収まる
       オクターブ」が選ばれる。
    4. 音符の多い順に並べて返す。

    Returns:
        list[TransposeCandidate]: 最大 12 個。音符が 0 個の曲なら空。
    """
    if not note_info:
        return []

    playable = playable_notes(conf)
    lo, hi = model_note_range(conf)
    tally = _NoteTally(note_info)

    best_of_key: dict[int, TransposeCandidate] = {}

    for t in range(lo - tally.note_max, hi - tally.note_min + 1):
        cand = tally.score(t, playable)
        key = cand['key']

        cur = best_of_key.get(key)
        # 同じ調なら、音符が多いほう → 同点なら移調量が小さいほう
        if cur is None or (
            (cand['notes'], -abs(t))
            > (cur['notes'], -abs(cur['transpose']))
        ):
            best_of_key[key] = cand

    # 数が同じなら**調を変えない案を上に**する。キーを変えずに済むなら
    # そのほうが良いのに、僅差で下に沈むと気づかれない。次いで移調量が小さい順。
    return sorted(
        best_of_key.values(),
        key=lambda c: (-c['notes'], c['key'] != 0, abs(c['transpose']))
    )


def add_transpose_rows(
    candidates: list[TransposeCandidate],
    note_info: list[NoteInfo], conf: ModelConf, wanted: Sequence[int],
) -> list[TransposeCandidate]:
    """候補に無い移調量の行を足して、並べ直したものを返す。

    `transpose_candidates()` は調ごとに「いちばん音域に収まるオクターブ」
    しか返さないので、**`±0` や手で指定した値は並ばないことが多い**。
    それだと表から ±0 に戻せず、「移調しないと何 % なのか」も分からない。

    Args:
        candidates (list[TransposeCandidate]): `transpose_candidates()` の結果。
        note_info (list[NoteInfo]): 成績を測る対象（移調する**前**）。
        conf (ModelConf): 機種の設定。
        wanted (Sequence[int]): 必ず行にしたい移調量。既にあるものは飛ばす。

    Returns:
        list[TransposeCandidate]: 鳴らせる音符の多い順。元のリストは変えない。
    """
    if not candidates:
        return list(candidates)

    rows = list(candidates)
    for t in wanted:
        if any(c['transpose'] == t for c in rows):
            continue
        row = transpose_score(note_info, conf, t)
        if row is not None:
            rows.append(row)

    rows.sort(key=lambda c: (-c['notes'], c['key'] != 0, abs(c['transpose'])))
    return rows


def transpose_has_improvement(candidates: list[TransposeCandidate]) -> bool:
    """``candidates`` の中に、±0（移調しない）より良いものが 1 つでもあるか。

    音符の数・音の長さの**どちらか**が ±0 を上回っていれば「改善」とする
    （TODO-039 で決めた「両方を出して選べるように」の考え方に合わせる）。

    Args:
        candidates (list[TransposeCandidate]): 比べる候補。``±0``
            （``transpose == 0``）の行を含んでいること。

    Returns:
        bool: 改善が無ければ False（候補が空、または ``±0`` の行が
            無いときも False。呼び方が誤っているとみなす）。
    """
    zero = next((c for c in candidates if c['transpose'] == 0), None)
    if zero is None:
        return False

    return any(
        c['transpose'] != 0
        and (c['note_pct'] > zero['note_pct'] or c['sec_pct'] > zero['sec_pct'])
        for c in candidates
    )


def select_transpose_rows(
    candidates: list[TransposeCandidate],
    note_info: list[NoteInfo], conf: ModelConf, transpose: int,
    limit: int = 5,
) -> list[TransposeCandidate]:
    """比べやすい数に絞った候補を返す（TODO-041）。

    `transpose_candidates()` は調ごとに 1 つ＝常に最大 12 行を返すが、
    多すぎて比べにくいうえ、下のほうには「移調しないほうがまし」な行まで
    並ぶ。ここで、画面に**出す**行だけに絞る。

    - **±0 より改善しない候補は出さない。** 音符の数・音の長さの
      どちらか一方でも ±0 を超えていれば残す（`transpose_has_improvement()`
      と同じ判定）。**閾値は設けない**（TODO-039 で決めたとおり、
      「◯ ポイント以上」の妥当性を延々と調整することになるため）。
      その代わり `limit` で数を絞る
    - **改善する候補は、上位 `limit` 個まで**（既定 5）
    - **±0 といまの移調量は、上の 2 つの規則から外して必ず残す。**
      ±0 が無いと一度移調したら戻れず、いまの値が無いと自分がどれを
      見ているのか分からなくなる（TODO-039）

    `transpose_candidates()` が返すものの決まり（調ごとに 1 つ・最大 12 個）
    はここでは変えない。絞り込みは見せるときの都合。

    Args:
        candidates (list[TransposeCandidate]): `transpose_candidates()` の
            結果（絞り込み前）。
        note_info (list[NoteInfo]): 成績を測る対象（移調する**前**）。
        conf (ModelConf): 機種の設定。
        transpose (int): いま適用している移調量。
        limit (int): 改善する候補として残す最大数。

    Returns:
        list[TransposeCandidate]: 鳴らせる音符の多い順。
            最大 ``limit + 2``（±0 といまの値のぶん）個。
    """
    rows = add_transpose_rows(candidates, note_info, conf, (0, transpose))
    if not rows:
        return rows

    zero = next(c for c in rows if c['transpose'] == 0)

    kept: list[TransposeCandidate] = []
    for c in rows:
        if c['transpose'] in (0, transpose):
            continue
        if c['note_pct'] > zero['note_pct'] or c['sec_pct'] > zero['sec_pct']:
            kept.append(c)
        if len(kept) >= limit:
            break

    result = [*kept, zero]
    if transpose != 0:
        result.append(next(c for c in rows if c['transpose'] == transpose))

    result.sort(key=lambda c: (-c['notes'], c['key'] != 0, abs(c['transpose'])))
    return result


def transpose_notices(candidates: list[TransposeCandidate]) -> list[str]:
    """候補について、利用者に言っておくべきことを返す（TODO-039）。

    **最適解は 1 つに定まらないことのほうが多い。** 一覧を出すだけでは
    気づけない状況だけを言葉にする。**`candidates` は画面に出す行そのもの
    を渡すこと**（TODO-041）。見送った行を「こちらが上です」と言っても
    確かめられない。

    - 改善が無い → 移調しても改善しない（黙って ±0 を返すと壊れて見える）
    - 音符の数の 1 位と、音の長さの 1 位が違う → 両方を示す
    - 調を変えない案が 1 位でないが上位にある → それで済むと知らせる

    Returns:
        list[str]: 画面に出す文（日本語）。何も無ければ空。
    """
    if not candidates:
        return []

    notices: list[str] = []
    best = candidates[0]

    if not transpose_has_improvement(candidates):
        zero = next(c for c in candidates if c['transpose'] == 0)
        notices.append(
            'どの調に移調しても、鳴らせる音符は増えません'
            f'（そのまま {zero["note_pct"]:.0f}%）。移調しても改善しません。'
        )
        return notices

    best_sec = max(
        candidates, key=lambda c: (c['sec_pct'], -abs(c['transpose']))
    )
    if best_sec['transpose'] != best['transpose']:
        notices.append(
            f'音符の数では 調{best["key"]:+d}'
            f'（{best["note_pct"]:.0f}%）ですが、'
            f'音の長さでは 調{best_sec["key"]:+d}'
            f'（{best_sec["sec_pct"]:.0f}%）が上です。'
        )

    if best['key'] != 0:
        same_key = next((c for c in candidates if c['key'] == 0), None)
        # 1 位に迫るなら、キーを変えずに済むことを知らせる
        if same_key and best['note_pct'] - same_key['note_pct'] <= 5.0:
            notices.append(
                '調を変えずに（オクターブだけで）'
                f'{same_key["note_pct"]:.0f}% 鳴らせます。'
            )

    return notices


def parse_transpose_arg(transpose: int | str) -> int | Literal['auto']:
    """移調量の指定を、整数か ``'auto'`` に正規化する。

    **外から来る値を受ける。** CLI の `-t` と Web のフォームがそのまま
    渡すので、整数にならない文字列がありうる。ここで弾かないと、あとで
    静かに 0 として扱われる。

    `RollBook` の非公開メソッドだったものを module 関数にした（TODO-043）。
    `MidiApp` は `RollBook` を作らないのに検証だけ borrow していて、
    `RollBook` の内部を触ると黙って壊れる形になっていた。

    Args:
        transpose (int | str): 移調する半音数、または ``'auto'``。

    Returns:
        int | Literal['auto']: 正規化した値。

    Raises:
        ValueError: 整数にも ``'auto'`` にもならないとき
            （メッセージはそのまま画面に出る）。
    """
    if isinstance(transpose, str):
        if transpose.strip().lower() == 'auto':
            return 'auto'
        try:
            return int(transpose)
        except ValueError as e:
            raise ValueError(
                f"移調量 '{transpose}' は整数か 'auto' で指定してください"
            ) from e

    return int(transpose)


class TransposePlan(NamedTuple):
    """移調をどうするか決めた結果（TODO-043）。

    Attributes:
        transpose: 実際に使う半音数。``'auto'`` を頼まれた場合も、
            ここには**選ばれた値**が入る。
        candidates: 画面に出す候補の行（`select_transpose_rows()` 済み）。
        chosen: `transpose` に当たる行。音符が 0 個なら None。
        notes: 移調したあとの音符。
    """

    transpose: int
    candidates: list[TransposeCandidate]
    chosen: TransposeCandidate | None
    notes: list[NoteInfo]


def plan_transpose(
    note_info: list[NoteInfo], conf: ModelConf,
    requested: int | Literal['auto'],
) -> TransposePlan:
    """移調量を決めて、候補と移調後の音符までまとめて返す（TODO-043）。

    `RollBook.parse()` と `MidiApp._convert_for_model()` が同じ手順を
    それぞれ持っていたのを 1 か所にした。**片方だけ直して食い違うのを
    防ぐのが目的。**

    手順:

    1. `transpose_candidates()` で候補を作る
    2. ``'auto'`` なら**絞る前**の 1 位を採る（候補が空なら 0）。
       絞り込みは見せるときの都合なので、選ぶのとは分ける
    3. `select_transpose_rows()` で画面に出す行に絞る
    4. `transpose_notes()` で実際にずらす

    Args:
        note_info (list[NoteInfo]): 対象の音符。**重なりの統合
            （`merge_overlapping_notes()`）は済ませて渡すこと。**
            あれは「実機は 1 音に 1 パイプ」という別の話なので、
            ここには含めない。
        conf (ModelConf): 機種の設定。
        requested (int | Literal['auto']): 頼まれた移調量。
            `parse_transpose_arg()` を通したもの。

    Returns:
        TransposePlan: 決めた内容と、移調後の音符。
    """
    raw_candidates = transpose_candidates(note_info, conf)

    if requested == 'auto':
        # 1 位を採る。候補が空（音符 0 個）なら移調しない
        transpose = raw_candidates[0]['transpose'] if raw_candidates else 0
        logger.info('transpose=auto -> {}', transpose)
    else:
        transpose = requested

    candidates = select_transpose_rows(
        raw_candidates, note_info, conf, transpose
    )
    chosen = transpose_score(note_info, conf, transpose)

    return TransposePlan(
        transpose=transpose,
        candidates=candidates,
        chosen=chosen,
        notes=transpose_notes(note_info, transpose),
    )
