"""single_instance 模块的单元测试：验证单实例互斥量的判定逻辑。"""

import ctypes
import sys

import pytest

from stay_awake import single_instance

# 本模块依赖 Windows 命名互斥量，其他平台跳过全部用例。
pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="单实例互斥量仅支持 Windows"
)


class FakeKernel32:
    """替身 kernel32:记录互斥量名称，返回预设句柄并模拟线程错误码。"""

    def __init__(self, handle: int, error_code: int = 0) -> None:
        self.handle = handle
        self.error_code = error_code
        self.requested_names: list[str] = []

    def CreateMutexW(self, _attributes: object, _initial_owner: bool, name: str) -> int:
        self.requested_names.append(name)
        ctypes.set_last_error(self.error_code)
        return self.handle


def test_acquire_returns_true_for_new_instance(monkeypatch) -> None:
    """错误码不是 ERROR_ALREADY_EXISTS 时表示首次创建，应返回 True。"""
    fake = FakeKernel32(handle=1)
    monkeypatch.setattr(single_instance, "_kernel32", fake)
    assert single_instance.acquire_single_instance_lock() is True


def test_acquire_returns_false_when_mutex_exists(monkeypatch) -> None:
    """错误码为 ERROR_ALREADY_EXISTS 时表示已有实例，应返回 False。"""
    fake = FakeKernel32(handle=1, error_code=single_instance.ERROR_ALREADY_EXISTS)
    monkeypatch.setattr(single_instance, "_kernel32", fake)
    assert single_instance.acquire_single_instance_lock() is False


def test_acquire_raises_when_create_fails(monkeypatch) -> None:
    """CreateMutexW 返回空句柄表示创建失败，应抛出携带错误码的 OSError。"""
    fake = FakeKernel32(handle=0, error_code=5)
    monkeypatch.setattr(single_instance, "_kernel32", fake)
    with pytest.raises(OSError, match="错误码 5"):
        single_instance.acquire_single_instance_lock()


def test_acquire_uses_session_scoped_mutex_name(monkeypatch) -> None:
    """互斥量名称应保持 Local\\ 前缀，将会话范围限定在当前登录会话内。"""
    fake = FakeKernel32(handle=1)
    monkeypatch.setattr(single_instance, "_kernel32", fake)
    single_instance.acquire_single_instance_lock()
    assert fake.requested_names == [single_instance._MUTEX_NAME]
