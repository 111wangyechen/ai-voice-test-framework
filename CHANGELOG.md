# 更新日志 (Changelog)

## [2.0.0] - 2026-06-08

### 🎉 重大更新

这是一次重大架构优化，解决了框架的所有核心问题，使其可以**完全独立运行**。

### ✨ 新增功能

#### 本地报告生成器
- 新增 `backend/report_generator.py` - 完整的本地分析引擎
- 自动计算核心指标：唤醒率、识别率、全双工稳定性
- 智能评分系统 (0-100分)，自动评级
- 生成完整的Markdown报告，包含统计表格和改进建议
- **无需API key，开箱即用**

#### 真实设备监控
- 新增 `backend/device_monitor.py` - 完整的设备监控模块
- `LogEventParser`: 智能日志解析，支持多种事件类型
- `PerformanceMonitor`: 实时性能采集（CPU、内存、进程）
- `DeviceMonitorSession`: 异步监控会话管理
- 支持Mock和真实设备双模式自动切换

#### 设备管理API
- `POST /api/device/connect` - 连接ADB设备
- `POST /api/device/disconnect` - 断开设备连接
- `GET /api/device/list` - 列出已连接设备

#### 配置管理API
- `GET /api/config` - 获取当前配置状态
- `POST /api/config/ai-mode` - 动态切换AI增强模式

### 🔧 优化改进

#### ADB管理器重构
- 移除 `pure-python-adb` 依赖，降低安装复杂度
- 改用 `subprocess` 直接调用adb命令
- 完整的异步支持
- 更好的错误处理和恢复机制

#### 后端架构优化
- 版本升级至 v2.0.0
- 完整的日志记录系统
- 改进的错误处理
- WebSocket支持真实/Mock双模式
- 报告生成支持本地/AI双引擎

#### API响应优化
- 所有端点增加详细的响应信息
- 统一的错误处理格式
- 更完善的API文档

### 🐛 问题修复

- ✅ 修复报告生成返回空内容的问题
- ✅ 修复WebSocket只推送Mock数据的问题
- ✅ 修复ADB依赖导致的启动失败
- ✅ 修复报告数据结构不匹配的问题

### 📚 文档更新

- 新增 `OPTIMIZATION_SUMMARY.md` - 优化总结文档
- 新增 `QUICKSTART.md` - 快速开始指南
- 更新 `PROJECT_MEMORY.md` - 完整的项目记忆
- 更新 `OPEN_ISSUES.md` - 标记已解决问题
- 新增 `CHANGELOG.md` - 本文档

### 🔄 破坏性变更

#### ADB Helper
- 移除了对 `pyadb` 的依赖
- 改为使用 `subprocess` 调用adb命令
- API接口保持不变，内部实现完全重写

#### 报告生成
- 默认使用本地分析引擎（之前依赖Anthropic API）
- AI增强模式需要显式启用
- 返回数据结构略有调整（增加了 `mode` 字段）

### 📦 依赖变更

#### 移除
- `pure-python-adb` - 不再需要

#### 保留
- `anthropic` - 可选依赖，用于AI增强模式

### 🧪 测试验证

- ✅ 后端启动测试通过
- ✅ API端点响应正常
- ✅ 本地报告生成器单元测试通过
- ✅ Mock模式WebSocket推送正常

### 📊 代码统计

- 新增代码：~800行
- 修改代码：~400行
- 新增文件：3个
- 修改文件：2个

### 🎯 下一步计划

详见 [OPEN_ISSUES.md](OPEN_ISSUES.md)

---

## [1.0.0] - 2026-06-05

### 初始版本

#### 功能
- 基础的FastAPI后端
- Vue 3 + TypeScript 前端
- WebSocket实时通信
- Workflow多代理编排
- Electron桌面应用框架

#### 已知问题
- 报告生成返回空内容
- 仅支持Mock数据
- 依赖未配置的API key

---

## 版本说明

版本号格式：`主版本.次版本.修订版本`

- **主版本**：重大架构变更或破坏性更新
- **次版本**：新增功能，向后兼容
- **修订版本**：Bug修复和小优化

---

**当前稳定版本**: v2.0.0
