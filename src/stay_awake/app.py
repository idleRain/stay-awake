"""托盘主程序：常驻系统状态栏，控制系统的保持唤醒状态。"""

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path
from typing import TypeAlias

from PIL import Image
import pystray

from stay_awake.power import prevent_sleep, restore_default
from stay_awake.single_instance import acquire_single_instance_lock

# 包内资源相对路径。
ASSETS_DIRNAME = "assets"
ICON_FILENAME_AWAKE = "awake.png"
ICON_FILENAME_SLEEP = "sleep.png"

# 托盘提示文本，与当前唤醒状态一一对应。
TITLE_RUNNING = "StayAwake - 阻止休眠中"
TITLE_PAUSED = "StayAwake - 已暂停，系统可正常休眠"

# 菜单文本随状态切换。
MENU_PAUSE = "暂停"
MENU_RESUME = "恢复"

# 消息框标题与图标样式常量：MB_ICONINFORMATION 表示信息图标，MB_ICONERROR 表示错误图标。
MESSAGE_BOX_TITLE = "StayAwake"
_MB_ICONINFORMATION = 0x00000040
_MB_ICONERROR = 0x00000010

# 启动失败时返回给操作系统的退出码。
_EXIT_FAILURE = 1

# 本项目依赖 Windows 专属 API,仅支持在该平台运行。
SUPPORTED_PLATFORM = "win32"

# pystray 的 Icon 由平台后端动态导出，且库未提供类型存根，静态检查器无法解析其类型。
# 统一经由此别名引用，并在此处集中压制无效类型表达式警告。
TrayIcon: TypeAlias = pystray.Icon  # pyright: ignore[reportInvalidTypeForm]


def _resolve_asset_path(filename: str) -> Path:
    """定位包内资源文件，兼容 PyInstaller 打包环境与源码运行环境。"""
    if getattr(sys, "frozen", False):
        # PyInstaller 单文件模式将资源解压到临时目录 _MEIPASS。
        # 该属性由 bootloader 在运行时注入，静态类型存根中不存在，须以动态方式访问。
        return Path(getattr(sys, "_MEIPASS")) / "stay_awake" / ASSETS_DIRNAME / filename
    return Path(__file__).resolve().parent / ASSETS_DIRNAME / filename


class StayAwakeApp:
    """托盘应用：同步维护唤醒状态、托盘图标与菜单显示。"""

    def __init__(self) -> None:
        self._paused = False
        self._awake_image = Image.open(_resolve_asset_path(ICON_FILENAME_AWAKE))
        self._sleep_image = Image.open(_resolve_asset_path(ICON_FILENAME_SLEEP))
        self._icon = pystray.Icon(
            name="stay_awake",
            icon=self._awake_image,
            title=TITLE_RUNNING,
            menu=pystray.Menu(
                pystray.MenuItem(
                    self._pause_menu_text,
                    self._toggle_pause,
                    checked=lambda _item: self._paused,
                ),
                pystray.MenuItem("退出", self._quit),
            ),
        )

    def run(self) -> None:
        """发起保持唤醒请求并进入托盘事件循环，阻塞至用户点击退出。"""
        prevent_sleep()
        self._icon.run()

    def _pause_menu_text(self, _item: pystray.MenuItem) -> str:
        """菜单文本随状态切换：暂停中显示恢复入口，反之显示暂停入口。"""
        return MENU_RESUME if self._paused else MENU_PAUSE

    def _toggle_pause(self, icon: TrayIcon, _item: pystray.MenuItem) -> None:
        """切换暂停状态，并同步电源请求、托盘图标与提示文本。

        先执行电源请求再翻转状态，请求抛出异常时保持原有状态与显示一致。
        """
        if self._paused:
            prevent_sleep()
        else:
            restore_default()
        self._paused = not self._paused
        self._refresh_appearance(icon)

    def _refresh_appearance(self, icon: TrayIcon) -> None:
        """根据当前状态刷新托盘图标、提示文本与菜单勾选。"""
        icon.icon = self._sleep_image if self._paused else self._awake_image
        icon.title = TITLE_PAUSED if self._paused else TITLE_RUNNING
        icon.update_menu()

    def _quit(self, icon: TrayIcon, _item: pystray.MenuItem) -> None:
        """退出回调：先停止托盘事件循环，再恢复电源设置。

        先停止事件循环是为了即使恢复请求抛出异常，退出流程也不会被阻塞。
        """
        icon.stop()
        restore_default()


def _show_message_box(text: str, style: int) -> None:
    """弹出系统消息框，在无控制台环境下向用户展示提示信息。

    user32 绑定延迟到调用时创建，避免非 Windows 平台导入本模块时报错。
    """
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.MessageBoxW.argtypes = [
        wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT,
    ]
    user32.MessageBoxW.restype = ctypes.c_int
    user32.MessageBoxW(None, text, MESSAGE_BOX_TITLE, style)


def _notify_already_running() -> None:
    """通过系统消息框提示用户应用已在运行，避免无窗口环境下静默退出。"""
    _show_message_box("StayAwake 已在运行，请查看系统托盘图标。", _MB_ICONINFORMATION)


def _notify_startup_failure(error: Exception) -> None:
    """通过系统消息框报告启动失败原因，避免无控制台环境下静默退出。"""
    _show_message_box(f"StayAwake 启动失败：\n{error}", _MB_ICONERROR)


def _ensure_supported_platform() -> None:
    """校验运行平台，非 Windows 时给出明确提示并退出。"""
    if sys.platform != SUPPORTED_PLATFORM:
        sys.exit(f"StayAwake 仅支持 Windows,当前平台 {sys.platform} 无法运行。")


def main() -> None:
    """应用入口：校验运行平台与单实例后启动托盘应用，启动失败时弹出错误提示。"""
    _ensure_supported_platform()
    if not acquire_single_instance_lock():
        _notify_already_running()
        return
    try:
        StayAwakeApp().run()
    except Exception as error:
        _notify_startup_failure(error)
        sys.exit(_EXIT_FAILURE)


if __name__ == "__main__":
    main()
