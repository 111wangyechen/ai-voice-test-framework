# 快速开始指南 (Quick Start)

**版本**: v2.0.0  
**更新日期**: 2026-06-08

---

## 前置要求

- Python 3.10+
- Node.js 16+
- ADB工具（真实设备模式需要）

---

## 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

---

## 启动方式

### 方式1：Mock模式（无需设备，快速演示）

**1. 启动后端**
```bash
cd backend
python main.py
```
看到以下输出表示成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**2. 启动前端**
```bash
cd frontend
npm run dev
```
访问 http://localhost:5173

**3. 使用**
- 点击「开始测试」
- 观察实时日志和性能数据（模拟数据）
- 点击「生成报告」→「导出Markdown」

---

### 方式2：真实设备模式

**1. 连接ADB设备**
```bash
# 确保设备可访问
adb connect 10.7.187.34:5555
adb devices
```

**2. 启动后端**
```bash
cd backend
python main.py
```

**3. 连接设备（API方式）**
```bash
curl -X POST http://localhost:8000/api/device/connect \
  -H "Content-Type: application/json" \
  -d '{"deviceIP": "10.7.187.34:5555"}'
```

或通过前端UI连接（TODO-1，待实现）

**4. 启动前端并开始测试**
```bash
cd frontend
npm run dev
```

此时WebSocket会推送真实的设备日志和性能数据

---

## API快速测试

### 查看API文档
```bash
curl http://localhost:8000/
```

### 查看配置
```bash
curl http://localhost:8000/api/config
```

### 测试报告生成
```bash
curl -X POST http://localhost:8000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_001",
    "test_events": [
      {"type": "wakeup", "severity": "info", "timestamp": "2024-01-01 10:00:00", "description": "唤醒成功"}
    ],
    "performance_data": [
      {"cpu_usage": 30.5, "mem_available_mb": 220.0}
    ],
    "test_config": {"deviceIP": "10.7.187.34:5555"}
  }'
```

---

## 启用AI增强模式（可选）

如果你有Claude API Key：

**1. 设置环境变量**
```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows
set ANTHROPIC_API_KEY=sk-ant-...
```

**2. 启用AI模式**
```bash
curl -X POST http://localhost:8000/api/config/ai-mode \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

**3. 重新生成报告**
此时报告将使用Claude API进行深度分析

---

## 常见问题

### Q1: 后端启动失败，提示模块未找到
```bash
# 确保在backend目录下安装了依赖
cd backend
pip install -r requirements.txt
```

### Q2: 前端无法连接后端
- 检查后端是否运行在8000端口
- 检查CORS配置（已设置为允许所有来源）
- 检查防火墙设置

### Q3: WebSocket没有数据推送
- 确保点击了「开始测试」按钮
- 检查浏览器控制台是否有错误
- Mock模式：后端会自动推送模拟数据
- 真实设备模式：确保设备已连接

### Q4: ADB连接设备失败
```bash
# 检查设备是否可达
adb connect 10.7.187.34:5555
adb devices

# 如果失败，检查网络和设备ADB配置
```

### Q5: 报告是空的
v2.0.0已修复此问题。如果仍然为空：
- 检查test_events是否为空
- 查看后端日志中的错误信息
- 确认LocalReportGenerator已正确导入

---

## 目录结构

```
ai-voice-test-framework/
├── backend/
│   ├── main.py                    # 主API服务
│   ├── report_generator.py        # 本地报告生成器 [新]
│   ├── device_monitor.py          # 设备监控模块 [新]
│   ├── utils/
│   │   └── adb_helper.py          # ADB管理器 [优化]
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── stores/testStore.ts    # 状态管理
│   │   └── components/            # Vue组件
│   └── package.json
├── workflows/                      # Workflow脚本（AI增强模式）
├── PROJECT_MEMORY.md              # 项目记忆
├── OPEN_ISSUES.md                 # 待办事项
├── OPTIMIZATION_SUMMARY.md        # 优化总结 [新]
└── QUICKSTART.md                  # 本文档 [新]
```

---

## 下一步

1. **真实设备测试**：连接10.7.187.34:5555，验证完整流程
2. **前端适配**：更新testStore.ts调用新API
3. **查看优化文档**：阅读 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)

---

**问题反馈**: 查看 [OPEN_ISSUES.md](OPEN_ISSUES.md) 或提交issue
