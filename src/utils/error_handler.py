# -*- coding: utf-8 -*-
"""
统一错误处理模块
提供全局异常捕获装饰器、API重试机制、超时控制和用户友好提示
"""
import os
import sys
import time
import signal
import functools
import traceback
from typing import Callable, Any, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TimeoutException(Exception):
    pass


def _timeout_handler(signum, frame):
    raise TimeoutException("操作超时")


def with_timeout(seconds: int = 30):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            return result
        return wrapper
    return decorator


def retry(max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0,
          exceptions: Tuple = (Exception,)):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"[RETRY] {func.__name__} 第{attempt + 1}次失败，{delay:.1f}s后重试: {e}")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        print(f"[RETRY] {func.__name__} 已达最大重试次数({max_retries})")
            raise last_exception
        return wrapper
    return decorator


def safe_execute(default_return=None, show_error: bool = True, user_message: str = ""):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if show_error:
                    msg = user_message or f"操作执行失败: {str(e)}"
                    print(f"[ERROR] {func.__name__}: {msg}")
                    try:
                        import streamlit as st
                        st.error(msg)
                    except Exception:
                        pass
                return default_return
        return wrapper
    return decorator


def global_exception_handler(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TimeoutException as e:
            msg = f"操作超时，请稍后重试"
            print(f"[TIMEOUT] {func.__name__}: {e}")
            _show_user_error(msg)
            return None
        except ConnectionError as e:
            msg = f"网络连接失败，请检查网络后重试"
            print(f"[CONNECTION] {func.__name__}: {e}")
            _show_user_error(msg)
            return None
        except PermissionError as e:
            msg = f"权限不足，无法执行此操作"
            print(f"[PERMISSION] {func.__name__}: {e}")
            _show_user_error(msg)
            return None
        except FileNotFoundError as e:
            msg = f"所需文件不存在，请检查数据路径"
            print(f"[FILE] {func.__name__}: {e}")
            _show_user_error(msg)
            return None
        except ValueError as e:
            msg = f"数据格式异常: {str(e)[:100]}"
            print(f"[VALUE] {func.__name__}: {e}")
            _show_user_error(msg)
            return None
        except Exception as e:
            msg = f"未知错误，请稍后重试"
            print(f"[FATAL] {func.__name__}: {traceback.format_exc()}")
            _show_user_error(msg)
            return None
    return wrapper


def _show_user_error(message: str):
    try:
        import streamlit as st
        st.error(message)
    except Exception:
        print(f"[USER_ERROR] {message}")


def user_friendly_message(error: Exception) -> str:
    error_map = {
        TimeoutException: "操作超时，请稍后重试",
        ConnectionError: "网络连接失败，请检查网络设置",
        PermissionError: "权限不足，请联系管理员",
        FileNotFoundError: "所需文件不存在",
        ValueError: "输入数据格式有误",
        KeyError: "数据字段缺失",
        TypeError: "数据类型不匹配",
        MemoryError: "内存不足，请减少数据量后重试",
    }
    for error_type, friendly_msg in error_map.items():
        if isinstance(error, error_type):
            return friendly_msg
    return "操作失败，请稍后重试"
