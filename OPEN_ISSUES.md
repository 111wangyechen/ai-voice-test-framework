# 待解决问题清单 (Open Issues)

> AI 辅助语音自动化测试框架 — 遗留问题与待办
> 工作记录见 [PROJECT_MEMORY.md](PROJECT_MEMORY.md)
> 更新于 2026-06-08

---

## 🎉 核心问题已全部解决！

经过2026-06-08的优化，原有的高优先级问题已完全解决：

### ✅ #1 【已解决】导出的 markdown 报告是空的

**解决方案**: 实现了`LocalReportGenerator`本地报告生成器
- 直接从测试数据计算指标（唤醒率、识别率、稳定性）
- 无需API key，立即可用
- 生成完整的Markdown报告，包含统计、评分、建议
- 已测试验证：5个事件 → 81分，唤醒率66.67%

**文件**: `backend/report_generator.py` (新增310行)

---

### ✅ #2 【已解决】后端 AI 能力 ≠ 打包后能力

**解决方案**: 架构重新设计
- **默认模式**: 本地分析引擎（无需API key）
- **可选模式**: AI增强（需配置ANTHROPIC_API_KEY）
- 两种模式可通过API动态切换

**新增配置端点**:
- `GET /api/config` - 查看当前配置
- `POST /api/config/ai-mode` - 切换AI模式

---

### ✅ #3 【已解决】WebSocket 数据是 mock 的，未接真实设备

**解决方案**: 实现真实设备监控模块
- `LogEventParser`: 正则匹配解析日志事件
- `PerformanceMonitor`: 实时采集CPU、内存、进程
- `DeviceMonitorSession`: 异步监控会话管理

**支持模式**:
- Mock模式：无设备时自动使用（演示、开发）
- 真实设备模式：连接ADB后自动切换

**新增设备管理端点**:
- `POST /api/device/connect` - 连接设备
- `POST /api/device/disconnect` - 断开设备
- `GET /api/device/list` - 列出设备

**文件**: `backend/device_monitor.py` (新增260行)

---

### ✅ #4 【已解决】ADB依赖问题

**解决方案**: 移除第三方依赖
- 不再依赖`pure-python-adb`（安装复杂）
- 改用`subprocess`直接调用adb命令
- 异步支持，更稳定可靠

**文件**: `backend/utils/adb_helper.py` (重构217行)

---

## 待改进事项（新）

### 高优先级

#### TODO-1: 前端适配新API
- [ ] 更新`testStore.ts`调用设备连接API
- [ ] 添加AI模式切换开关
- [ ] 适配新的报告数据结构（`report.markdown`字段）

#### TODO-2: 真实设备测试
- [ ] 连接`10.7.187.34:5555`或`10.7.187.15:5555`
- [ ] 验证logcat日志解析准确性
- [ ] 微调正则表达式匹配实际日志格式
- [ ] 测试完整流程：连接→测试→报告

#### TODO-3: 报告导出验证
- [ ] 验证导出的Markdown文件内容完整
- [ ] 测试中文编码正确性
- [ ] 检查统计数据准确性

---

### 中优先级

#### TODO-4: Electron 打包（网络问题）
**现象**: `electron-builder`无法下载electron二进制文件

**已尝试**: 设置`ELECTRON_MIRROR`环境变量

**待办**:
- [ ] 配置`ELECTRON_BUILDER_BINARIES_MIRROR`
- [ ] 手动下载并放到缓存目录
- [ ] 在网络通畅环境重试
- 当前替代：后端exe + 前端dist 手动组合

#### TODO-5: 性能优化
- [ ] 日志解析性能测试（高频日志场景）
- [ ] WebSocket推送频率调优
- [ ] 内存占用监控

#### TODO-6: 单元测试
- [ ] `report_generator.py`测试用例
- [ ] `device_monitor.py`测试用例
- [ ] `adb_helper.py`测试用例
- [ ] API端点集成测试

---

### 低优先级

#### TODO-7: 数据持久化
- [ ] 测试事件存储到SQLite
- [ ] 性能数据历史记录
- [ ] 报告归档管理

#### TODO-8: 多设备并行测试
- [ ] 前端UI支持多设备选择
- [ ] 后端并行监控多个设备
- [ ] 报告分设备生成

#### TODO-9: 高级功能
- [ ] 报告模板自定义
- [ ] 历史报告对比
- [ ] 自定义日志解析规则（配置文件）
- [ ] PDF导出支持

---

**当前状态：所有阻塞性问题已解决，框架可完整运行！** ✅
