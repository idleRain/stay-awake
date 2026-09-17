# StayAwake

<p align="center">
  <img src="./src/stay_awake/assets/icon.png" width="64" alt="StayAwake">
</p>

常驻 Windows 系统托盘的小工具，一键阻止系统休眠与息屏。

## 为什么需要它

Windows 系统下某些策略组配置或电源管理设置，会把系统无操作的休眠时间调得极短——比如 2 分钟不碰键盘鼠标，屏幕就进入屏保，系统随即休眠。看文档、读代码、开会演示时频繁解锁唤醒，十分的烦人。

StayAwake 就是为解决这一痛点而生：**无需安装，下载后打开即用**。

## 下载

从 [Releases](https://github.com/idleRain/stay-awake/releases/latest) 下载 `StayAwake.exe`, 双击运行即可。

右键托盘的图标可以暂停 / 恢复，不用了就点退出。

## 原理

与视频播放器防止系统在观影时休眠是同一个原理：通过 Windows 自带的 API(`SetThreadExecutionState`)一直告诉系统「我还在用呢，别休眠」。

- 不碰电源计划，不改注册表，退出后一切照旧；
- 进程就算被 kill, 系统也会自动恢复正常，不会出现「锁死不休眠」的副作用。

## 从源码运行 / 构建

需要 Python 3.10 及以上版本，仅支持 Windows。

```powershell
git clone https://github.com/idleRain/stay-awake.git && cd stay-awake

# 以可编辑方式安装本项目(含测试依赖)
pip install -e ".[dev]"

# 源码运行
python -m stay_awake

# 打包为单文件 exe(产物输出至 dist/StayAwake.exe)
pip install pyinstaller
python scripts/build.py
```

## 许可证
[MIT](./LICENSE)
