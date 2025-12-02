import os
import folder_paths


# Shared cache so multiple callers can reuse results without rescanning disk
_filename_list_cache = {}


def apply_filename_list_cache():
    """Wrap ``folder_paths.get_filename_list`` with a simple in-memory cache.

    Some environments keep LoRA or model folders on slow or remote storage,
    which makes every page load trigger long rescans when nodes build their
    input choices.  The cache avoids repeated scans across requests while still
    allowing opt-out via the ``EASYUSE_DISABLE_FILENAME_CACHE`` environment
    variable.
    """

    if os.environ.get("EASYUSE_DISABLE_FILENAME_CACHE"):
        return

    # Avoid double-wrapping if the cache was already applied (e.g. prestartup
    # and module import both call this helper).
    if getattr(folder_paths.get_filename_list, "__easyuse_cached__", False):
        return

    original_get_filename_list = folder_paths.get_filename_list

    def cached_get_filename_list(*args, **kwargs):
        cache_key = (args, tuple(sorted(kwargs.items())))
        if cache_key not in _filename_list_cache:
            _filename_list_cache[cache_key] = tuple(original_get_filename_list(*args, **kwargs))
        return list(_filename_list_cache[cache_key])

    cached_get_filename_list.__easyuse_cached__ = True
    cached_get_filename_list.__easyuse_original__ = original_get_filename_list

    folder_paths.get_filename_list = cached_get_filename_list

