# AI辅助语音自动化测试框架

## 项目简介

这是一个通用的AI辅助语音测试自动化框架，支持：
- ✅ 全双工语音交互测试
- ✅ 唤醒率测试
- ✅ 语音识别率测试
- ✅ 实时日志监控与AI智能分析
- ✅ 实时设备性能监控
- ✅ 自动生成测试报告

## 技术栈

**后端**
- Python 3.10+
- FastAPI (异步Web框架)
- WebSocket (实时数据推送)
- pure-python-adb (ADB设备控制)
- SQLite (本地数据库)

**前端**
- Vue 3 + TypeScript
- Element Plus (UI组件库)
- ECharts (图表库)
- Socket.IO (WebSocket客户端)

**桌面应用**
- Electron (跨平台桌面框架)
- PyInstaller (Python打包)
- electron-builder (应用打包)

## 项目结构

```
ai-voice-test-framework/
├── backend/           # Python后端
├── frontend/          # Vue前端
├── electron/          # Electron主进程
├── build/             # 打包配置
├── scenarios/         # 测试场景配置
└── data/              # 数据目录
    ├── logs/          # 日志文件
    └── reports/       # 测试报告
```

## 快速开始

### 开发环境

1. 安装Python 3.10+
2. 安装Node.js 16+
3. 安装依赖：
   ```bash
   # 后端
   cd backend
   pip install -r requirements.txt
   
   # 前端
   cd frontend
   npm install
   ```

### 运行开发服务器

```bash
# 后端
cd backend
python main.py

# 前端
cd frontend
npm run dev
```

### 打包应用

```bash
# 完整打包
npm run build
```

## 使用说明

详见 `docs/USER_GUIDE.md`

## 开发文档

- [设计文档](DESIGN_FULL.md)
- [实施计划](IMPLEMENTATION_PLAN.md)
- [API文档](docs/API.md)

## 许可证

MIT License
