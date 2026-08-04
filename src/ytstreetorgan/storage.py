#
# (c) 2026 Yoichi Tanibayashi
#
"""`webroot/midi/` と `webroot/svg/` に置いたファイルの扱い。

**ファイル名を外（URL やフォーム）から受け取る経路はここに集める。**
削除まであるため、`..` や区切り文字が混ざった名前で置き場の外に
出られると事故になる。名前を受け取ったら必ず `resolve_in()` を通すこと。
"""
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import TypedDict
from urllib.parse import quote

from loguru import logger

from .utils import get_size_unit

# 置き場の名前 → webroot 下のディレクトリ名
KINDS = {'midi': 'midi', 'svg': 'svg'}

# ヘッダの quoted-string を壊す文字と、制御文字
_UNSAFE_IN_HEADER_RE = re.compile(r'["\\]|[\x00-\x1f\x7f]')

# <svg ... width="4133.20mm" height="126.00mm" ...>
_SVG_SIZE_RE = re.compile(
    r'<svg\b[^>]*?\bwidth="([\d.]+)mm"[^>]*?\bheight="([\d.]+)mm"'
)


class FileInfo(TypedDict):
    """一覧の 1 行。"""

    name: str
    size: str
    mtime: str


def safe_name(name: str) -> str:
    """ファイル名として受け取ってよい形か確かめ、そのまま返す。

    Args:
        name (str): 外から来た名前。

    Returns:
        str: 問題なければ ``name`` そのもの。

    Raises:
        ValueError: 区切り文字や `..` を含む、あるいは空のとき。

    Note:
        置き場の中に収まることは、これに加えて呼び出し側が
        `resolve()` して確かめる（`resolve_in()` を使う）。
    """
    if not name or name in ('.', '..'):
        raise ValueError(f'使えない名前です: {name!r}')

    if '/' in name or '\\' in name or '\x00' in name:
        raise ValueError(f'区切り文字は使えません: {name!r}')

    if Path(name).name != name:
        raise ValueError(f'ファイル名ではありません: {name!r}')

    return name


def resolve_in(base: Path, name: str) -> Path:
    """``base`` の中の ``name`` を指すパスを返す。

    `safe_name()` を通したうえで、**解決後も ``base`` の下にあること**を
    確かめる（シンボリックリンクで外へ出られないように）。

    Raises:
        ValueError: 名前が不正、または置き場の外を指すとき。
    """
    path = (base / safe_name(name)).resolve()

    if not path.is_relative_to(base.resolve()):
        raise ValueError(f'置き場の外を指しています: {name!r}')

    return path


def list_files(dir_path: Path) -> list[FileInfo]:
    """ディレクトリの中身を、新しい順に並べて返す。"""
    if not dir_path.is_dir():
        return []

    entries = [
        p for p in dir_path.iterdir()
        if p.is_file() and not p.name.startswith('.')
    ]
    entries.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    files: list[FileInfo] = []
    for p in entries:
        st = p.stat()
        size, unit = get_size_unit(st.st_size)
        files.append({
            'name': p.name,
            'size': f'{size:.1f} {unit}',
            'mtime': datetime.fromtimestamp(st.st_mtime).strftime(
                '%Y-%m-%d %H:%M'
            ),
        })

    return files


def book_from_svg(svg: str) -> dict:
    """保存済みの SVG から、ビューアに渡す諸元を読めるだけ読む。

    `width` / `height` は `<svg width="…mm" height="…mm">` に出ているので
    読める。**穴の数と `mm_per_sec` は SVG に無い**ので None にする
    （画面では `---` と出す）。穴は長いものがブリッジで分割されて
    1 音符が `<path>` 複数本になるため、数えても求まらない。

    Returns:
        dict: `width` / `height` は float か None。ほかは None。
    """
    m = _SVG_SIZE_RE.search(svg)

    book: dict = {
        'width': float(m.group(1)) if m else None,
        'height': float(m.group(2)) if m else None,
        'mm_per_sec': None,
        'notes': None,
        'hole_notes': None,
        'holes': None,
        'off_scale_notes': None,
        'off_scale': None,
    }
    logger.debug('book={}', book)
    return book


def content_disposition(name: str) -> str:
    """ダウンロード用の ``Content-Disposition`` の値を組み立てる。

    **名前をそのまま入れてはいけない。** HTTP ヘッダは latin-1 しか通らず、
    日本語のファイル名だと tornado が弾いて 500 になる（実際なっていた）。
    引用符も無かったので、空白入りの名前はブラウザが途中で切りうる。

    RFC 6266 に従い、UTF-8 のままの名前を ``filename*`` に入れ、
    それを読まないもの向けに ASCII へ落とした ``filename`` を引用符付きで
    併記する。今のブラウザは ``filename*`` を優先する。

    Args:
        name (str): 元のファイル名。

    Returns:
        str: ``attachment; filename="…"; filename*=UTF-8''…``
    """
    # NFKD で分解してから ASCII に落とす（'é' → 'e'。日本語は消える）
    def to_ascii(part: str) -> str:
        ascii_part = unicodedata.normalize('NFKD', part).encode(
            'ascii', 'ignore'
        ).decode('ascii')
        return _UNSAFE_IN_HEADER_RE.sub('_', ascii_part).strip()

    src = Path(name)
    stem = to_ascii(src.stem) or 'download'
    fallback = stem + to_ascii(src.suffix)

    return (
        f'attachment; filename="{fallback}"; '
        f"filename*=UTF-8''{quote(name, safe='')}"
    )
