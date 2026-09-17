"""app 模块的单元测试：验证资源定位与托盘应用的状态切换逻辑。"""

import sys
from pathlib import Path
from typing import cast

import pystray

from stay_awake import app
from stay_awake.app import TrayIcon


class FakeTrayIcon:
    """替身托盘图标：记录属性赋值与方法调用，替代 pystray.Icon。"""

    def __init__(self) -> None:
        self.icon: object = None
        self.title: str | None = None
        self.update_menu_calls = 0
        self.stop_calls = 0

    def update_menu(self) -> None:
        self.update_menu_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1


def _fake_menu_item() -> pystray.MenuItem:
    """构造仅用于占位的真实菜单项，其回调在测试中不会被触发。"""
    return pystray.MenuItem("测试项", lambda _icon: None)


def _as_tray_icon(fake_icon: FakeTrayIcon) -> TrayIcon:
    """将替身图标按托盘图标类型传入，替身只实现测试触及的属性与方法。"""
    return cast(TrayIcon, fake_icon)


def test_resolve_asset_path_in_source_mode() -> None:
    """源码模式下资源应位于包目录的 assets 子目录内且真实存在。"""
    path = app._resolve_asset_path(app.ICON_FILENAME_AWAKE)
    assert path.parent.name == app.ASSETS_DIRNAME
    assert path.exists()


def test_resolve_asset_path_in_frozen_mode(monkeypatch) -> None:
    """打包模式下资源应位于 PyInstaller 临时解压目录的包内 assets 子目录。"""
    fake_root = "C:/_meipass"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", fake_root, raising=False)
    path = app._resolve_asset_path(app.ICON_FILENAME_AWAKE)
    expected = Path(fake_root) / "stay_awake" / app.ASSETS_DIRNAME / app.ICON_FILENAME_AWAKE
    assert path == expected


def test_toggle_pause_switches_state_and_appearance(monkeypatch) -> None:
    """暂停时应发起恢复请求并切换为睡眠外观，恢复时发起保持唤醒请求。"""
    power_calls: list[str] = []
    monkeypatch.setattr(app, "prevent_sleep", lambda: power_calls.append("prevent"))
    monkeypatch.setattr(app, "restore_default", lambda: power_calls.append("restore"))
    application = app.StayAwakeApp()
    icon = FakeTrayIcon()

    application._toggle_pause(_as_tray_icon(icon), _fake_menu_item())
    assert application._paused is True
    assert power_calls == ["restore"]
    assert icon.title == app.TITLE_PAUSED
    assert icon.icon == application._sleep_image
    assert icon.update_menu_calls == 1

    application._toggle_pause(_as_tray_icon(icon), _fake_menu_item())
    assert application._paused is False
    assert power_calls == ["restore", "prevent"]
    assert icon.title == app.TITLE_RUNNING
    assert icon.icon == application._awake_image


def test_pause_menu_text_follows_state() -> None:
    """菜单文本应随暂停状态切换，暂停中显示恢复入口。"""
    application = app.StayAwakeApp()
    assert application._pause_menu_text(_fake_menu_item()) == app.MENU_PAUSE
    application._paused = True
    assert application._pause_menu_text(_fake_menu_item()) == app.MENU_RESUME


def test_quit_stops_icon_and_restores_power(monkeypatch) -> None:
    """退出时应停止托盘事件循环，并完成恢复请求。"""
    restore_calls: list[int] = []
    monkeypatch.setattr(app, "restore_default", lambda: restore_calls.append(1))
    application = app.StayAwakeApp()
    icon = FakeTrayIcon()

    application._quit(_as_tray_icon(icon), _fake_menu_item())
    assert icon.stop_calls == 1
    assert restore_calls == [1]
