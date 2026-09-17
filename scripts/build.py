"""打包 StayAwake 为单个 exe 文件。用法：python scripts/build.py"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
ENTRY = SRC_DIR / "stay_awake" / "__main__.py"
ASSETS_DIR = SRC_DIR / "stay_awake" / "assets"
APP_ICON = ASSETS_DIR / "icon.png"
DIST = ROOT / "dist"
BUILD = ROOT / "build"

# 打包后资源在临时解压目录内的相对位置，需与 _resolve_asset_path 的查找逻辑一致。
ASSETS_TARGET_DIR = "stay_awake/assets"

# 打包时排除的无用模块。本应用仅需 Pillow 读取 PNG 与写出 ICO，
# 排除对应格式插件可一并断开其独占的二进制扩展，例如 _avif 与 _webp。
# 格式插件经由 Image.init 的动态导入加载，缺失时静默跳过，因此排除安全；
# 被保留模块静态引用的辅助模块（如 TiffTags 与调色板解析族）必须保留，
# 校验依据为构建产物 build/StayAwake/warn-StayAwake.txt 中的引用记录。
EXCLUDED_MODULES: tuple[str, ...] = (
    # Pillow 未用到的格式插件。
    "PIL.AvifImagePlugin",
    "PIL.BlpImagePlugin",
    "PIL.BufrStubImagePlugin",
    "PIL.CurImagePlugin",
    "PIL.DcxImagePlugin",
    "PIL.DdsImagePlugin",
    "PIL.EpsImagePlugin",
    "PIL.FitsImagePlugin",
    "PIL.FliImagePlugin",
    "PIL.FpxImagePlugin",
    "PIL.FtexImagePlugin",
    "PIL.GbrImagePlugin",
    "PIL.GifImagePlugin",
    "PIL.GribStubImagePlugin",
    "PIL.Hdf5StubImagePlugin",
    "PIL.IcnsImagePlugin",
    "PIL.ImImagePlugin",
    "PIL.ImtImagePlugin",
    "PIL.IptcImagePlugin",
    "PIL.Jpeg2KImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.JpegPresets",
    "PIL.McIdasImagePlugin",
    "PIL.MicImagePlugin",
    "PIL.MpegImagePlugin",
    "PIL.MpoImagePlugin",
    "PIL.MspImagePlugin",
    "PIL.PalmImagePlugin",
    "PIL.PcdImagePlugin",
    "PIL.PcxImagePlugin",
    "PIL.PdfImagePlugin",
    "PIL.PdfParser",
    "PIL.PixarImagePlugin",
    "PIL.PpmImagePlugin",
    "PIL.PsdImagePlugin",
    "PIL.QoiImagePlugin",
    "PIL.SgiImagePlugin",
    "PIL.SpiderImagePlugin",
    "PIL.SunImagePlugin",
    "PIL.TgaImagePlugin",
    "PIL.WebPImagePlugin",
    "PIL.WmfImagePlugin",
    "PIL.XbmImagePlugin",
    "PIL.XpmImagePlugin",
    "PIL.XVThumbImagePlugin",
    # Pillow 未用到的功能组件，字体与色彩管理组件连带独占的二进制扩展。
    "PIL.ImageCms",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    "PIL.ImageMath",
    "PIL.ImageMorph",
    "PIL.ImageQt",
    "PIL.ImageShow",
    "PIL.ImageTk",
    "PIL.ImageWin",
    # pystray 的其他平台后端，Windows 仅使用 _win32。
    "pystray._appindicator",
    "pystray._darwin",
    "pystray._gtk",
    "pystray._util.gtk",
    "pystray._util.notify_dbus",
    "pystray._xorg",
)


def main() -> None:
    if not ENTRY.exists():
        sys.exit(f"未找到入口文件: {ENTRY}")
    if not APP_ICON.exists():
        sys.exit(f"未找到应用图标: {APP_ICON}")

    # 打包前清理旧产物，若文件被占用则提示用户先退出正在运行的实例。
    for path in (DIST, BUILD):
        if path.exists():
            try:
                shutil.rmtree(path)
            except PermissionError:
                sys.exit(
                    f"无法删除 {path}，文件可能正被占用。"
                    "请先退出状态栏中的 StayAwake 后再试。"
                )

    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "StayAwake",
        "--paths", str(SRC_DIR),
        f"--icon={APP_ICON}",
        "--add-data", f"{ASSETS_DIR};{ASSETS_TARGET_DIR}",
    ]
    command.extend(f"--exclude-module={module}" for module in EXCLUDED_MODULES)
    command.append(str(ENTRY))
    subprocess.run(command, cwd=str(ROOT), check=True)
    print(f"打包完成: {DIST / 'StayAwake.exe'}")


if __name__ == "__main__":
    main()
