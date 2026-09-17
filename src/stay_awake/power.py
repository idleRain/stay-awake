"""电源管理 API 封装，基于 Win32 SetThreadExecutionState。"""

import ctypes
from ctypes import wintypes

# Windows API 常量：持续请求系统保持运行且显示器常亮。
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# 惰性初始化的 kernel32 绑定，延迟到首次调用时创建，避免非 Windows 平台导入本模块时报错。
_kernel32: ctypes.WinDLL | None = None


def _get_kernel32() -> ctypes.WinDLL:
    """返回已完成签名绑定的 kernel32 实例，首次调用时执行初始化。"""
    global _kernel32
    if _kernel32 is None:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.SetThreadExecutionState.argtypes = [wintypes.DWORD]
        kernel32.SetThreadExecutionState.restype = wintypes.DWORD
        _kernel32 = kernel32
    return _kernel32


def _request_execution_state(flags: int) -> None:
    """向系统发起一次执行状态请求，API 报告失败时抛出携带错误码的异常。"""
    result = _get_kernel32().SetThreadExecutionState(flags)
    if result == 0:
        raise OSError(f"SetThreadExecutionState 调用失败，错误码 {ctypes.get_last_error()}")


def prevent_sleep() -> None:
    """请求系统保持运行且屏幕常亮。

    该状态绑定调用线程，线程退出后由系统自动恢复默认电源行为，
    因此进程无论正常退出还是被强制结束，均不会遗留唤醒标记。
    """
    _request_execution_state(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)


def restore_default() -> None:
    """清除保持唤醒标记，恢复系统默认电源管理行为。"""
    _request_execution_state(ES_CONTINUOUS)
