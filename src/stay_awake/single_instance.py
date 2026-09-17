"""单实例检测：基于 Windows 命名互斥量防止多开。"""

import ctypes
from ctypes import wintypes

# GetLastError 返回值：同名命名内核对象已经存在。
ERROR_ALREADY_EXISTS = 0x000000B7

# 互斥量名称，Local\ 前缀将会话范围限定在当前登录会话内。
_MUTEX_NAME = "Local\\StayAwakeSingleInstanceMutex"

# 惰性初始化的 kernel32 绑定，延迟到首次调用时创建，避免非 Windows 平台导入本模块时报错。
_kernel32: ctypes.WinDLL | None = None


def _get_kernel32() -> ctypes.WinDLL:
    """返回已完成签名绑定的 kernel32 实例，首次调用时执行初始化。"""
    global _kernel32
    if _kernel32 is None:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        _kernel32 = kernel32
    return _kernel32


def acquire_single_instance_lock() -> bool:
    """获取单实例互斥量，返回 False 表示已有实例正在运行。

    互斥量句柄由进程持有并随进程退出自动释放，因此进程崩溃后同样不会残留锁。
    """
    mutex_handle = _get_kernel32().CreateMutexW(None, False, _MUTEX_NAME)
    if not mutex_handle:
        raise OSError(f"创建单实例互斥量失败，错误码 {ctypes.get_last_error()}")
    return ctypes.get_last_error() != ERROR_ALREADY_EXISTS
