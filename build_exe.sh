#!/usr/bin/env bash
# ============================================================
# 一键打包脚本：前端构建 + 后端 PyInstaller 单文件 EXE
# 产物：backend/dist/ai-voice-test.exe（双击即用，自动开浏览器）
# 用法：bash build_exe.sh
# ============================================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "项目根目录: $ROOT"

echo ""
echo "==> [1/3] 构建前端 (npm run build)..."
cd "$ROOT/frontend"
npm run build

echo ""
echo "==> [2/3] PyInstaller 打包后端 + 前端..."
cd "$ROOT/backend"
rm -rf build dist
pyinstaller ai-voice-test-backend.spec --noconfirm

echo ""
echo "==> [3/3] 整理产物到 release/..."
cd "$ROOT"
mkdir -p release
cp -f "$ROOT/backend/dist/ai-voice-test.exe" "$ROOT/release/ai-voice-test.exe"

echo ""
echo "============================================================"
echo "  打包完成！"
echo "  产物: release/ai-voice-test.exe"
echo "  双击即可运行，会自动打开浏览器界面。"
echo "  注意: 真机测试需系统已安装 adb 并加入 PATH。"
echo "============================================================"
