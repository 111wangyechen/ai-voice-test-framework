# AI辅助语音自动化测试框架 - 多代理架构

## 核心理念

使用**多代理协作（Multi-Agent Orchestration）**实现智能化、并行化的测试分析流程。

## 多代理架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow 编排引擎                          │
│                  (主控制器 + 多代理调度)                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ 日志监控Agent  │   │ 性能监控Agent  │   │ 错误诊断Agent  │
│ - 实时采集     │   │ - CPU监控      │   │ - 异常检测     │
│ - 事件识别     │   │ - 内存监控     │   │ - 根因分析     │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    分析Agent团队                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 唤醒分析Agent │ │ 识别分析Agent │ │ 全双工分析    │        │
│  │              │ │              │ │ Agent        │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    报告生成Agent                              │
│  - 指标计算                                                   │
│  - 报告撰写                                                   │
│  - 建议生成                                                   │
└─────────────────────────────────────────────────────────────┘
```

## 核心Workflow流程

### 1. 测试监控Workflow
```javascript
export const meta = {
  name: 'test-monitoring',
  description: '实时监控测试过程，并行分析日志和性能',
  phases: [
    { title: 'Monitor', detail: '并行监控日志流和性能指标' },
    { title: 'Analyze', detail: '多维度分析事件' },
    { title: 'Alert', detail: '检测重大错误' }
  ]
}

// 阶段1: 并行监控
phase('Monitor')
const [logEvents, perfMetrics] = await parallel([
  () => agent('监控设备日志流，识别所有语音事件', {
    schema: LOG_EVENTS_SCHEMA,
    agentType: 'log-monitor'
  }),
  () => agent('监控设备性能，检测异常', {
    schema: PERF_METRICS_SCHEMA,
    agentType: 'performance-monitor'
  })
])

// 阶段2: 多维度分析
phase('Analyze')
const analysis = await pipeline(
  logEvents.events,
  event => agent(`分析事件: ${event.type}`, {
    schema: EVENT_ANALYSIS_SCHEMA
  })
)

// 阶段3: 错误检测
phase('Alert')
const criticalErrors = analysis.filter(a => a.severity === 'critical')
if (criticalErrors.length > 0) {
  await agent('生成错误报告并告警', {
    schema: ERROR_REPORT_SCHEMA
  })
}
```

### 2. 错误诊断Workflow
```javascript
export const meta = {
  name: 'error-diagnosis',
  description: '多Agent协作诊断错误根因',
  phases: [
    { title: 'Detect', detail: '检测错误特征' },
    { title: 'Analyze', detail: '并行分析多个维度' },
    { title: 'Synthesize', detail: '综合诊断结果' }
  ]
}

// 阶段1: 检测错误
phase('Detect')
const errorContext = await agent('提取错误上下文和相关日志', {
  schema: ERROR_CONTEXT_SCHEMA
})

// 阶段2: 多维度并行分析
phase('Analyze')
const analyses = await parallel([
  () => agent('从代码逻辑角度分析', {label: 'code-logic'}),
  () => agent('从系统资源角度分析', {label: 'resource'}),
  () => agent('从时序关系角度分析', {label: 'timing'}),
  () => agent('从历史案例角度分析', {label: 'history'})
])

// 阶段3: 综合诊断
phase('Synthesize')
const diagnosis = await agent(
  `综合以下4个维度的分析，给出根本原因和解决方案：
   ${JSON.stringify(analyses)}`,
  {schema: DIAGNOSIS_SCHEMA}
)

return diagnosis
```

### 3. 测试报告生成Workflow
```javascript
export const meta = {
  name: 'report-generation',
  description: '多Agent协作生成测试报告',
  phases: [
    { title: 'Collect', detail: '收集测试数据' },
    { title: 'Calculate', detail: '并行计算各项指标' },
    { title: 'Generate', detail: '生成完整报告' }
  ]
}

// 阶段1: 收集数据
phase('Collect')
const testData = args.testData  // 从前端传入的测试数据

// 阶段2: 并行计算指标
phase('Calculate')
const metrics = await parallel([
  () => agent('计算唤醒率指标', {
    schema: WAKEUP_METRICS_SCHEMA
  }),
  () => agent('计算识别率指标', {
    schema: RECOGNITION_METRICS_SCHEMA
  }),
  () => agent('计算全双工稳定性', {
    schema: FULLDUPLEX_METRICS_SCHEMA
  }),
  () => agent('计算性能指标', {
    schema: PERFORMANCE_METRICS_SCHEMA
  })
])

// 阶段3: 生成报告
phase('Generate')
const report = await agent(
  `基于以下指标生成详细测试报告（Markdown格式）：
   ${JSON.stringify(metrics)}`,
  {schema: REPORT_SCHEMA}
)

return report
```

## Agent职责定义

### 核心Agent

1. **日志监控Agent (log-monitor)**
   - 实时读取logcat流
   - 识别关键事件（唤醒、识别、全双工退出）
   - 标注事件严重程度

2. **性能监控Agent (performance-monitor)**
   - 采集CPU、内存、进程指标
   - 检测性能异常
   - 生成性能告警

3. **错误诊断Agent (error-diagnostician)**
   - 多维度分析错误
   - 查找根本原因
   - 提供解决建议

4. **指标计算Agent (metrics-calculator)**
   - 计算唤醒率、识别率
   - 统计测试指标
   - 生成数据报表

5. **报告生成Agent (report-writer)**
   - 撰写测试报告
   - 生成可视化图表
   - 提供改进建议

### 专项分析Agent

6. **唤醒分析Agent** - 专注唤醒率分析
7. **识别分析Agent** - 专注识别准确率分析
8. **全双工分析Agent** - 专注全双工稳定性分析
9. **性能分析Agent** - 专注性能瓶颈分析

## 多Agent协作流程

### 测试执行流程
```
1. 用户启动测试
   ↓
2. 启动监控Workflow
   - 日志监控Agent（持续运行）
   - 性能监控Agent（持续运行）
   ↓
3. 实时分析Workflow（每N秒触发）
   - 并行分析各类事件
   - 检测异常情况
   ↓
4. 发现重大错误时
   - 触发错误诊断Workflow
   - 多Agent协作分析
   - 生成诊断报告
   - 通知用户审核
   ↓
5. 测试完成后
   - 触发报告生成Workflow
   - 并行计算各项指标
   - 生成完整报告
   - 等待用户审核
```

## 技术实现

### 后端架构调整

```python
# backend/main.py
from fastapi import FastAPI, WebSocket
from workflows import WorkflowManager

app = FastAPI()
workflow_manager = WorkflowManager()

@app.post("/api/test/start")
async def start_test(config: TestConfig):
    """启动测试 - 触发监控Workflow"""
    workflow_id = await workflow_manager.start_workflow(
        "test-monitoring",
        args={"device_ip": config.device_ip}
    )
    return {"workflow_id": workflow_id}

@app.post("/api/error/diagnose")
async def diagnose_error(error: ErrorEvent):
    """诊断错误 - 触发诊断Workflow"""
    workflow_id = await workflow_manager.start_workflow(
        "error-diagnosis",
        args={"error": error.dict()}
    )
    return {"workflow_id": workflow_id}

@app.post("/api/report/generate")
async def generate_report(session_id: str):
    """生成报告 - 触发报告生成Workflow"""
    workflow_id = await workflow_manager.start_workflow(
        "report-generation",
        args={"session_id": session_id}
    )
    return {"workflow_id": workflow_id}
```

### Workflow管理器

```python
# backend/workflows/manager.py
class WorkflowManager:
    """Workflow管理器 - 与Claude Code的Workflow工具集成"""
    
    async def start_workflow(self, workflow_name: str, args: dict):
        """
        启动Workflow
        
        通过调用Claude Code的Workflow API启动多代理协作
        """
        # 实际实现中，这里会调用Workflow工具
        pass
    
    async def get_workflow_status(self, workflow_id: str):
        """获取Workflow执行状态"""
        pass
    
    async def get_workflow_result(self, workflow_id: str):
        """获取Workflow执行结果"""
        pass
```

## 优势

### vs 传统单进程方式

**传统方式**：
- 顺序处理，慢
- 单一视角，可能遗漏问题
- 错误分析不够深入

**多Agent方式**：
- ✅ **并行处理**：日志分析、性能监控、错误诊断同时进行
- ✅ **多维度分析**：多个Agent从不同角度分析同一问题
- ✅ **深度诊断**：专门的错误诊断Workflow，多Agent协作找根因
- ✅ **高质量报告**：专业的报告生成Agent，结构化输出

### 具体优势

1. **速度提升**：并行处理，整体测试时间减少50%+
2. **准确性提升**：多Agent交叉验证，减少误判
3. **深度提升**：专项Agent深入分析，发现更多隐藏问题
4. **可扩展性**：轻松添加新的分析维度（新增Agent即可）

## 下一步

1. ✅ 确认多Agent架构方案
2. 实现核心Workflow脚本
3. 集成到前后端应用
4. 测试与优化

---

**这个多Agent架构是否符合你的设想？我们可以开始实现了！**
