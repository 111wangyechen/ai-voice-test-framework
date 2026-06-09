# 打包指南 - 将框架打包成Windows应用

本指南详细说明如何将AI辅助语音自动化测试框架打包成独立的Windows桌面应用。

---

## 📋 打包前准备

### 1. 环境检查

确保已安装以下工具：

```bash
# Python 3.12+
python --version

# Node.js 23.3.0+
node --version

# npm 10.9.0+
npm --version

# PyInstaller
pip install pyinstaller

# electron-builder
npm install -g electron-builder
```

### 2. 依赖安装

**后端依赖**:
```bash
cd backend
pip install -r requirements.txt
```

**前端依赖**:
```bash
cd frontend
npm install
```

**Electron依赖**:
```bash
cd electron
npm install electron electron-builder
```

---

## 🔧 打包步骤

### 步骤1: 打包Python后端为exe

#### 方式A: 使用PyInstaller命令行

```bash
cd backend

# 使用backend.spec配置文件打包
pyinstaller ../build/backend.spec

# 输出位置: backend/dist/ai-voice-test-backend.exe
```

#### 方式B: 使用打包脚本

```bash
cd build
python build-backend.py
```

**预期输出**:
```
backend/dist/
└── ai-voice-test-backend.exe  (约50-80MB)
```

**验证**:
```bash
# 测试后端exe能否启动
cd backend/dist
./ai-voice-test-backend.exe
# 应该看到: INFO: Uvicorn running on http://127.0.0.1:8000
# Ctrl+C停止
```

---

### 步骤2: 构建前端

```bash
cd frontend

# 安装依赖（如果还没安装）
npm install

# 构建生产版本
npm run build

# 输出位置: frontend/dist/
```

**预期输出**:
```
frontend/dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   └── index-[hash].css
└── ...
```

**验证**:
```bash
# 本地预览
npm run preview
# 访问: http://localhost:4173
```

---

### 步骤3: 配置Electron

创建Electron package.json:

```bash
cd electron
```

创建 `package.json`:
```json
{
  "name": "ai-voice-test-tool",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder"
  },
  "build": {
    "appId": "com.aivoice.test.framework",
    "productName": "AI语音测试工具",
    "directories": {
      "buildResources": "../assets",
      "output": "../release"
    },
    "files": [
      "../frontend/dist/**/*",
      "main.js",
      "preload.js",
      "package.json"
    ],
    "extraResources": [
      {
        "from": "../backend/dist/ai-voice-test-backend.exe",
        "to": "backend/"
      },
      {
        "from": "../workflows/",
        "to": "workflows/"
      }
    ],
    "win": {
      "target": [
        {
          "target": "nsis",
          "arch": ["x64"]
        }
      ],
      "icon": "../assets/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "shortcutName": "AI语音测试工具",
      "license": "../LICENSE.txt"
    }
  },
  "dependencies": {
    "electron": "^28.0.0"
  },
  "devDependencies": {
    "electron-builder": "^24.0.0"
  }
}
```

---

### 步骤4: 打包完整应用

```bash
# 回到项目根目录
cd ..

# 打包整个应用
cd electron
npm run build
```

electron-builder会自动：
1. 读取package.json配置
2. 收集frontend/dist文件
3. 打包backend exe和workflows
4. 生成NSIS安装程序

**预期输出**:
```
release/
└── AI语音测试工具-Setup-1.0.0.exe  (约100-150MB)
```

---

## 📦 打包结果

### 安装程序结构

```
AI语音测试工具-Setup-1.0.0.exe
├── [NSIS安装向导]
├── 应用文件
│   ├── AI语音测试工具.exe  (Electron主程序)
│   ├── resources/
│   │   ├── app.asar  (前端代码)
│   │   ├── backend/
│   │   │   └── ai-voice-test-backend.exe
│   │   └── workflows/
│   │       ├── test-monitoring.js
│   │       ├── error-diagnosis.js
│   │       ├── report-generation.js
│   │       └── log-file-analysis.js
│   └── ...
└── 卸载程序
```

### 安装后目录

默认安装路径: `C:\Program Files\AI语音测试工具\`

```
C:\Program Files\AI语音测试工具\
├── AI语音测试工具.exe  (主程序)
├── resources/
│   ├── app.asar
│   ├── backend/
│   │   └── ai-voice-test-backend.exe
│   └── workflows/
│       └── (4个workflow脚本)
└── Uninstall.exe
```

桌面快捷方式: `桌面\AI语音测试工具.lnk`

---

## ✅ 验证打包结果

### 1. 安装测试

```bash
# 双击安装程序
AI语音测试工具-Setup-1.0.0.exe

# 选择安装路径
# 等待安装完成
# 勾选"运行AI语音测试工具"
# 点击"完成"
```

### 2. 功能验证

**验证清单**:
- [ ] 应用能正常启动
- [ ] 后端服务自动启动（约3秒）
- [ ] 前端界面正常显示
- [ ] 能连接测试设备（输入IP后测试连接）
- [ ] 能开始测试并看到实时日志
- [ ] 能生成测试报告
- [ ] 所有按钮和功能正常工作

### 3. 性能测试

**验证项**:
- [ ] 启动时间 < 5秒
- [ ] 内存占用 < 200MB（空闲）
- [ ] CPU占用 < 10%（空闲）
- [ ] 无崩溃、无卡顿

### 4. 兼容性测试

在不同Windows版本测试：
- [ ] Windows 10 (64位)
- [ ] Windows 11 (64位)

---

## 🐛 常见打包问题

### 问题1: PyInstaller打包失败

**现象**: ModuleNotFoundError或ImportError

**解决**:
```bash
# 清理缓存
pyinstaller --clean backend.spec

# 检查hiddenimports
# 在backend.spec中添加缺失的模块
hiddenimports = [
    'fastapi',
    'uvicorn',
    # ... 添加缺失的模块
]
```

### 问题2: 前端构建失败

**现象**: npm run build报错

**解决**:
```bash
# 清理node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install

# 重新构建
npm run build
```

### 问题3: electron-builder打包失败

**现象**: 找不到文件或权限错误

**解决**:
```bash
# 检查文件路径是否正确
ls -la backend/dist/ai-voice-test-backend.exe
ls -la frontend/dist/index.html

# 以管理员身份运行
# 右键 -> 以管理员身份运行PowerShell
cd electron
npm run build
```

### 问题4: 安装程序无法运行

**现象**: 双击.exe无反应或报错

**解决**:
1. 检查Windows Defender是否拦截
2. 右键 -> 属性 -> 解除阻止
3. 临时关闭杀毒软件
4. 使用管理员权限运行

### 问题5: 后端服务启动失败

**现象**: 应用启动后显示"后端服务未运行"

**解决**:
1. 检查端口8000是否被占用
   ```bash
   netstat -ano | findstr 8000
   ```
2. 修改main.js中的端口配置
3. 检查后端exe路径是否正确

---

## 🚀 优化建议

### 1. 减小安装包体积

**当前**: 100-150MB

**优化方法**:
- 使用UPX压缩exe（PyInstaller选项）
- 删除不必要的依赖
- 使用asar压缩前端代码

```python
# backend.spec中添加
upx=True,
upx_exclude=[],
```

### 2. 添加自动更新

使用electron-updater实现自动更新：
```bash
npm install electron-updater
```

### 3. 添加崩溃报告

集成Sentry或类似服务：
```bash
npm install @sentry/electron
```

### 4. 代码签名

购买代码签名证书，避免Windows SmartScreen警告：
```bash
electron-builder --win --sign
```

---

## 📝 打包检查清单

打包前确认：
- [ ] 所有依赖已安装
- [ ] 后端代码无语法错误
- [ ] 前端构建成功
- [ ] workflow脚本已更新
- [ ] 版本号已更新
- [ ] 图标文件已准备（icon.ico）
- [ ] LICENSE.txt已准备

打包后测试：
- [ ] 安装程序能正常运行
- [ ] 应用能正常启动
- [ ] 后端服务自动启动
- [ ] 所有功能正常工作
- [ ] 无错误日志
- [ ] 卸载程序正常工作

---

## 📞 技术支持

打包过程中遇到问题？

1. 查看日志文件：
   - PyInstaller: `build/ai-voice-test-backend/warn-ai-voice-test-backend.txt`
   - electron-builder: `electron/dist/builder-debug.yml`

2. 联系技术支持：
   - 邮箱: support@your-org.com
   - 企业微信: AI测试框架支持群

---

**准备开始打包？运行以下命令开始！** 🚀

```bash
# 一键打包脚本
cd build
python build-all.py
```
