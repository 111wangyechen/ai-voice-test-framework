// workflows/error-diagnosis.js
// 错误诊断Workflow - 多维度并行分析错误根因

export const meta = {
  name: 'error-diagnosis',
  description: '多Agent协作诊断错误根因，提供解决方案',
  phases: [
    { title: 'Extract', detail: '提取错误上下文' },
    { title: 'Analyze', detail: '多维度并行分析' },
    { title: 'Synthesize', detail: '综合诊断结论' }
  ]
}

// 从args获取错误事件
const errorEvent = args.errorEvent
const deviceIP = args.deviceIP || '10.7.187.15:5555'

if (!errorEvent) {
  log('❌ 错误：未提供errorEvent参数')
  return { success: false, error: '缺少错误事件数据' }
}

log(`开始诊断错误: ${errorEvent.type} - ${errorEvent.description}`)

// 阶段1: 提取错误上下文
phase('Extract')

const errorContext = await agent(
  `提取错误的完整上下文信息：

错误事件:
- 类型: ${errorEvent.type}
- 时间: ${errorEvent.timestamp}
- 描述: ${errorEvent.description}
- 原始日志: ${errorEvent.raw_log || '无'}

任务:
1. 从设备 ${deviceIP} 获取错误发生前后10秒的完整日志
   使用命令: adb -s ${deviceIP} logcat -d -t 500
2. 获取当前设备状态（内存、CPU、进程列表）
3. 提取相关的关键信息（进程状态、异常堆栈等）

返回结构化的错误上下文`,
  {
    label: 'extract-context',
    schema: {
      type: 'object',
      properties: {
        before_logs: {
          type: 'array',
          items: { type: 'string' },
          description: '错误发生前的日志'
        },
        after_logs: {
          type: 'array',
          items: { type: 'string' },
          description: '错误发生后的日志'
        },
        device_state: {
          type: 'object',
          properties: {
            memory_mb: { type: 'number' },
            cpu_usage: { type: 'number' },
            key_processes: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  name: { type: 'string' },
                  pid: { type: 'number' },
                  status: { type: 'string' }
                }
              }
            }
          }
        },
        stack_traces: {
          type: 'array',
          items: { type: 'string' },
          description: '异常堆栈信息'
        }
      },
      required: ['before_logs', 'after_logs', 'device_state']
    }
  }
)

log(`✓ 上下文提取完成 - 前置日志: ${errorContext.before_logs.length}, 后置日志: ${errorContext.after_logs.length}`)

// 阶段2: 多维度并行分析
phase('Analyze')
log('启动4个分析Agent并行工作...')

// 4个独立的分析维度，完全并行
const analyses = await parallel([
  // 维度1: 代码逻辑分析
  () => agent(
    `从代码逻辑角度分析这个错误：

错误类型: ${errorEvent.type}
错误描述: ${errorEvent.description}

日志上下文:
${errorContext.before_logs.slice(-10).join('\n')}
[错误发生点]
${errorContext.after_logs.slice(0, 10).join('\n')}

分析要点:
1. 这是什么类型的错误？（逻辑错误、状态机错误、时序错误等）
2. 代码执行流程哪里出了问题？
3. 是否违反了某个前置条件？
4. 可能的代码缺陷在哪里？`,
    {
      label: 'logic-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          error_category: { type: 'string' },
          execution_flow_issue: { type: 'string' },
          precondition_violation: { type: 'string' },
          suspected_code_location: { type: 'string' },
          confidence: { type: 'number', minimum: 0, maximum: 1 }
        },
        required: ['error_category', 'execution_flow_issue', 'confidence']
      }
    }
  ),

  // 维度2: 系统资源分析
  () => agent(
    `从系统资源角度分析这个错误：

设备状态:
- 可用内存: ${errorContext.device_state.memory_mb} MB
- CPU使用率: ${errorContext.device_state.cpu_usage}%
- 关键进程: ${JSON.stringify(errorContext.device_state.key_processes, null, 2)}

错误堆栈: ${errorContext.stack_traces.join('\n') || '无'}

分析要点:
1. 是否存在资源不足（内存、CPU、文件描述符）？
2. 是否有进程异常（死锁、卡死、OOM）？
3. 系统负载是否过高导致该错误？
4. 资源竞争或泄漏的迹象？`,
    {
      label: 'resource-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          resource_shortage: { type: 'boolean' },
          resource_type: { type: 'string' },
          process_anomaly: { type: 'string' },
          system_overload: { type: 'boolean' },
          root_cause_likelihood: { type: 'number', minimum: 0, maximum: 1 }
        },
        required: ['resource_shortage', 'system_overload', 'root_cause_likelihood']
      }
    }
  ),

  // 维度3: 时序关系分析
  () => agent(
    `从时序关系角度分析这个错误：

时间线（按时间顺序）:
${errorContext.before_logs.slice(-5).concat(errorContext.after_logs.slice(0, 5)).join('\n')}

分析要点:
1. 事件发生的时序链条是什么？
2. 是否存在竞态条件（race condition）？
3. 是否有超时或延迟导致的问题？
4. 前序事件中哪个是触发点？`,
    {
      label: 'timing-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          event_sequence: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                event: { type: 'string' },
                timestamp: { type: 'string' }
              }
            }
          },
          race_condition: { type: 'boolean' },
          timeout_issue: { type: 'boolean' },
          trigger_event: { type: 'string' },
          causality_confidence: { type: 'number', minimum: 0, maximum: 1 }
        },
        required: ['event_sequence', 'race_condition', 'causality_confidence']
      }
    }
  ),

  // 维度4: 历史案例分析
  () => agent(
    `从历史案例角度分析这个错误：

当前错误:
- 类型: ${errorEvent.type}
- 特征: ${errorEvent.description}
- 关键日志: ${errorEvent.raw_log}

任务:
1. 这是否是已知的常见问题？
2. 是否与之前报告的问题相似？
3. 历史案例中的解决方案是什么？
4. 是否是回归问题（之前修复过但又出现）？`,
    {
      label: 'history-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          known_issue: { type: 'boolean' },
          similar_cases: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                description: { type: 'string' },
                solution: { type: 'string' }
              }
            }
          },
          regression: { type: 'boolean' },
          historical_fix_applicable: { type: 'boolean' }
        },
        required: ['known_issue', 'regression', 'historical_fix_applicable']
      }
    }
  )
])

// 过滤失败的分析
const validAnalyses = analyses.filter(Boolean)
log(`✓ 完成 ${validAnalyses.length}/4 个维度的分析`)

// 阶段3: 综合诊断
phase('Synthesize')

const finalDiagnosis = await agent(
  `综合4个维度的分析，给出最终诊断结论：

## 各维度分析结果

### 1. 代码逻辑分析
${JSON.stringify(validAnalyses[0], null, 2)}

### 2. 系统资源分析
${JSON.stringify(validAnalyses[1], null, 2)}

### 3. 时序关系分析
${JSON.stringify(validAnalyses[2], null, 2)}

### 4. 历史案例分析
${JSON.stringify(validAnalyses[3], null, 2)}

## 任务
基于以上4个维度的独立分析，综合判断：
1. **根本原因** - 最可能的根因是什么？（给出置信度）
2. **次要原因** - 还有哪些可能的贡献因素？
3. **解决方案** - 具体的修复建议（优先级排序）
4. **预防措施** - 如何避免再次发生？
5. **紧急程度** - 是否需要立即处理？

注意：不同维度的分析可能得出不同结论，你需要权衡各方证据，给出最合理的综合判断。`,
  {
    label: 'synthesize-diagnosis',
    schema: {
      type: 'object',
      properties: {
        root_cause: {
          type: 'object',
          properties: {
            description: { type: 'string' },
            confidence: { type: 'number', minimum: 0, maximum: 1 },
            supporting_evidence: {
              type: 'array',
              items: { type: 'string' }
            }
          },
          required: ['description', 'confidence']
        },
        contributing_factors: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              factor: { type: 'string' },
              impact: { type: 'string', enum: ['high', 'medium', 'low'] }
            }
          }
        },
        solutions: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              solution: { type: 'string' },
              priority: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
              estimated_effort: { type: 'string' },
              implementation_steps: {
                type: 'array',
                items: { type: 'string' }
              }
            }
          }
        },
        prevention_measures: {
          type: 'array',
          items: { type: 'string' }
        },
        urgency: {
          type: 'string',
          enum: ['immediate', 'urgent', 'normal', 'low']
        },
        requires_human_review: { type: 'boolean' }
      },
      required: ['root_cause', 'solutions', 'urgency']
    }
  }
)

log(`✓ 诊断完成 - 根因: ${finalDiagnosis.root_cause.description} (置信度: ${Math.round(finalDiagnosis.root_cause.confidence * 100)}%)`)

// 生成诊断报告（Markdown格式）
const reportMarkdown = await agent(
  `生成错误诊断报告（Markdown格式）：

错误事件: ${errorEvent.description}
诊断结论: ${JSON.stringify(finalDiagnosis, null, 2)}

生成一份清晰、专业的诊断报告，包含：
1. 错误摘要
2. 根本原因分析
3. 解决方案（按优先级）
4. 预防措施
5. 附录：各维度详细分析`,
  {
    label: 'generate-report',
    schema: {
      type: 'object',
      properties: {
        markdown_report: { type: 'string' }
      },
      required: ['markdown_report']
    }
  }
)

log('✓ 错误诊断完成')

// 返回完整诊断结果
return {
  success: true,
  error_event: errorEvent,
  context: errorContext,
  dimensional_analyses: {
    logic: validAnalyses[0],
    resource: validAnalyses[1],
    timing: validAnalyses[2],
    history: validAnalyses[3]
  },
  final_diagnosis: finalDiagnosis,
  report_markdown: reportMarkdown.markdown_report
}
