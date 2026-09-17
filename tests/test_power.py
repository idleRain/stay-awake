"""power 模块的单元测试：验证执行状态请求的参数组装与返回值检查。"""

import ctypes

import pytest

from stay_awake import power


class FakeKernel32:
    """替身 kernel32:记录请求参数，返回预设结果并模拟线程错误码。"""

    def __init__(self, return_value: int, error_code: int = 0) -> None:
        self.return_value = return_value
        self.error_code = error_code
        self.requested_flags: list[int] = []

    def SetThreadExecutionState(self, flags: int) -> int:
        self.requested_flags.append(flags)
        ctypes.set_last_error(self.error_code)
        return self.return_value


def test_prevent_sleep_requests_continuous_system_and_display(monkeypatch) -> None:
    """保持唤醒时应同时携带持续标志、系统保持标志与显示器保持标志。"""
    fake = FakeKernel32(return_value=power.ES_CONTINUOUS)
    monkeypatch.setattr(power, "_kernel32", fake)
    power.prevent_sleep()
    assert fake.requested_flags == [
        power.ES_CONTINUOUS | power.ES_SYSTEM_REQUIRED | power.ES_DISPLAY_REQUIRED
    ]


def test_restore_default_requests_continuous_flag_only(monkeypatch) -> None:
    """恢复默认时应仅携带持续标志，用于清除此前的保持唤醒请求。"""
    fake = FakeKernel32(return_value=power.ES_CONTINUOUS)
    monkeypatch.setattr(power, "_kernel32", fake)
    power.restore_default()
    assert fake.requested_flags == [power.ES_CONTINUOUS]


def test_request_raises_when_api_reports_failure(monkeypatch) -> None:
    """API 返回 0 表示调用失败，应抛出携带错误码的 OSError。"""
    fake = FakeKernel32(return_value=0, error_code=2)
    monkeypatch.setattr(power, "_kernel32", fake)
    with pytest.raises(OSError, match="错误码 2"):
        power.prevent_sleep()
