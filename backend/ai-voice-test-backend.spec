# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 — 单文件 EXE，内含前端静态文件 + workflows
打包命令（在 backend 目录下执行）:
    pyinstaller ai-voice-test-backend.spec --noconfirm
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# uvicorn / websockets / anthropic 等大量依赖通过字符串动态导入，
# PyInstaller 静态分析抓不到，必须显式声明，否则打包后启动即崩。
hiddenimports = []
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("websockets")
hiddenimports += collect_submodules("anthropic")
hiddenimports += [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "anyio._backends._asyncio",
    # 本地模块（main.py 顶层 import，需显式声明，否则打包后找不到）
    "report_generator",
    "device_monitor",
    "utils",
    "utils.adb_helper",
]

# 前端构建产物 + workflows 脚本打入包内。
# 元组格式 (源路径, 包内目标目录)，与 main.py 的 resource_path() 对应。
datas = [
    ("../frontend/dist", "frontend/dist"),
    ("../workflows", "workflows"),
]
# anthropic SDK 自带的数据文件（如有）
datas += collect_data_files("anthropic")


import os

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath(os.getcwd())],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ai-voice-test',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
