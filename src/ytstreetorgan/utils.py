#
# (c) 2026 Yoichi Tanibayashi
#
"""ytstreetorgan 全体で使う小物。"""


def get_size_unit(f_size: int | float) -> tuple[float, str]:
    """バイト数を、読める大きさと単位の組に直す。

    Args:
        f_size (int | float): バイト数。

    Returns:
        tuple[float, str]: 例: ``(1.5, 'MB')``。

    Note:
        画面に出す文字列にするのは `storage.size_text()`。書式は
        あちらが決める。
    """
    size_units = ['B', 'KB', 'MB', 'GB', 'TB']
    idx = 0
    while f_size >= 1024 and idx < len(size_units) - 1:
        f_size /= 1024
        idx += 1
    return f_size, size_units[idx]
