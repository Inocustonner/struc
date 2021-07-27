from typing import Any, Callable, Optional
from threading import RLock

def cacheOne(f: Callable[..., Any]) -> Callable[..., Any]:
    last_return: Optional[Any] = None
    last_args: tuple[Any, ...] = ()
    lock = RLock()
    def wrapper(*args: Any) -> Any:
        nonlocal last_return, last_args, lock
        with lock:
            if last_return is not None and args == last_args:
                return last_return
            else:
                last_return = f(*args)
                last_args = args
                return last_return
    return wrapper

def cacheOnce(f: Callable[..., Any]) -> Callable[..., Any]:
    stored_results: dict[Any, Any] = {}
    def wrapper(*args: Any) -> Any:
        nonlocal stored_results
        if (result := stored_results.get(args)) is not None:
            return result
        else:
            result = f(*args)
            stored_results[args] = result
            return result
    return wrapper