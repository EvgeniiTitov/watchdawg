import os
import psutil
import functools


@functools.lru_cache(maxsize=1)
def _get_current_pid() -> int:
    return os.getpid()


@functools.lru_cache(maxsize=1)
def _get_current_psutil_process() -> psutil.Process:
    pid = _get_current_pid()
    return psutil.Process(pid)


def get_current_process_cpu_usage(interval: int = 0) -> float:
    """Returns CPU usage of the current process in percent"""
    process = _get_current_psutil_process()
    return process.cpu_percent(interval)


def get_current_process_ram_usage():
    """Returns the amount of memory in MB used by the current process"""
    process = _get_current_psutil_process()
    return process.memory_info().rss / (1024 * 1024)
