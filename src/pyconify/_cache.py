import atexit
import shelve
from functools import update_wrapper
from typing import Any, Callable

CACHE = "/Users/talley/Desktop/cache"
db = shelve.open(CACHE)
atexit.register(db.close)


def cache(maxsize=None):
    def decorating_function(user_function):
        return update_wrapper(_shelve_cache_wrapper(user_function), user_function)

    return decorating_function


def _shelve_cache_wrapper(user_function: Callable) -> Callable[..., Any]:
    sentinel = object()  # unique object used to signal cache misses
    make_key = _make_key  # build a key from the function arguments
    cache = db
    hits = misses = 0
    cache_get = cache.get  # bound method to lookup a key or return None

    def wrapper(*args: Any, **kwds: Any) -> Any:
        # Simple caching without ordering or size limit
        nonlocal hits, misses
        key = make_key((user_function.__qualname__, *args), kwds)
        result = cache_get(key, sentinel)
        if result is not sentinel:
            hits += 1
            return result
        misses += 1
        result = user_function(*args, **kwds)
        cache[key] = result
        return result

    def cache_info() -> tuple[int, int]:
        """Report cache statistics."""
        return (hits, misses)

    def cache_clear() -> None:
        """Clear the cache and cache statistics."""
        nonlocal hits, misses
        cache.clear()
        hits = misses = 0

    wrapper.cache_info = cache_info
    wrapper.cache_clear = cache_clear
    return wrapper


def _make_key(args: tuple, kwds: dict[str, Any]) -> str:
    """Make a cache key from optionally typed positional and keyword arguments.

    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.

    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.

    """
    # All of code below relies on kwds preserving the order input by the user.
    # Formerly, we sorted() the kwds before looping.  The new way is *much*
    # faster; however, it means that f(x=1, y=2) will now be treated as a
    # distinct call from f(y=2, x=1) which will be cached separately.
    key = args
    if kwds:
        for item in kwds.items():
            key += item
    if len(key) == 1 and isinstance(key[0], (int, str)):
        return str(key[0])
    return "-".join(map(str, key))
