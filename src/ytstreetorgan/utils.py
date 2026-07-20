#
# (c) 2026 Yoichi Tanibayashi
#
"""
Shared utility functions for ytstreetorgan.
"""


def get_size_unit(f_size: int | float) -> tuple[float, str]:
    """
    Convert byte count to human-readable (value, unit) pair.

    Parameters
    ----------
    f_size: int | float
        file size in bytes

    Returns
    -------
    (value, unit): tuple[float, str]
        e.g. (1.5, 'MB')
    """
    size_units = ['B', 'KB', 'MB', 'GB', 'TB']
    idx = 0
    while f_size >= 1024 and idx < len(size_units) - 1:
        f_size /= 1024
        idx += 1
    return f_size, size_units[idx]
