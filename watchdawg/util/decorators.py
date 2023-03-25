import time
import functools
import typing as t
import tracemalloc


__all__ = ["timer", "measure_peak_ram"]


_MEGA = 10**6
_GIGA = 10**9


def timer(func: t.Callable) -> t.Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> t.Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(
            f"TIMER: Function `{func.__name__}` took "
            f"{time.perf_counter() - start: .3f} seconds"
        )
        return result

    return wrapper


def measure_peak_ram(func: t.Callable) -> t.Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> t.Any:
        tracemalloc.start()
        result = func(*args, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
        print(
            f"RAM USAGE: Function `{func.__name__}`'s peak RAM usage: "
            f"{peak / _MEGA:.2f} MB ({peak / _GIGA:.4f} GB)"
        )
        tracemalloc.stop()
        return result

    return wrapper
