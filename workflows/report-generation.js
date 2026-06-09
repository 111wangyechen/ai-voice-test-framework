// workflows/report-generation.js
// 测试报告生成Workflow - 并行计算指标并生成报告

export const meta = {
  name: 'report-generation',
  description: '多Agent协作生成测试报告，并行计算各项指标',
  phases: [
    { title: 'Collect', detail: '收集测试数据' },
    { title: 'Calculate', detail: '并行计算各项指标' },
    { title: 'Generate', detail: '生成完整报告' },
    { title: 'Review', detail: 'AI审核报告质量' }
  ]
}

// 从args获取测试会话数据
const sessionId = args.sessionId
const testEvents = args.testEvents || []
const performanceData = args.performanceData || []
const testConfig = args.testConfig || {}

if (!sessionId) {
  log('❌ 错误：未提供sessionId参数')
  return { success: false, error: '缺少会话ID' }
}

log(`开始生成测试报告 - 会话ID: ${sessionId}`)
log(`测试事件数: ${testEvents.length}, 性能数据点: ${performanceData.length}`)

// 阶段1: 收集和整理测试数据
phase('Collect')

const dataOrganization = await agent(
  `整理测试数据，按类型分类：

测试事件 (${testEvents.length}条):
${JSON.stringify(testEvents.slice(0, 5), null, 2)}
...

测试配置:
${JSON.stringify(testConfig, null, 2)}

任务:
1. 将事件按类型分类（wakeup, recognition, fullduplex_exit, error等）
2. 统计各类事件数量
3. 识别关键事件
4. 提取测试的时间范围`,
  {
    label: 'organize-data',
    schema: {
      type: 'object',
      properties: {
        event_categories: {
          type: 'object',
          properties: {
            wakeup_attempts: { type: 'number' },
            successful_wakeups: { type: 'number' },
            recognition_events: { type: 'number' },
            fullduplex_exits: { type: 'number' },
            unexpected_exits: { type: 'number' },
            errors: { type: 'number' }
          }
        },
        time_range: {
          type: 'object',
          properties: {
            start: { type: 'string' },
            end: { type: 'string' },
            duration_seconds: { type: 'number' }
          }
        },
        critical_events: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              type: { type: 'string' },
              timestamp: { type: 'string' },
              description: { type: 'string' }
            }
          }
        }
      },
      required: ['event_categories', 'time_range']
    }
  }
)

log(`✓ 数据整理完成 - 唤醒尝试: ${dataOrganization.event_categories.wakeup_attempts}, 关键事件: ${dataOrganization.critical_events?.length || 0}`)

// 阶段2: 并行计算各项指标
phase('Calculate')
log('启动4个指标计算Agent并行工作...')

const metricsResults = await parallel([
  // 指标1: 唤醒率分析
  () => agent(
    `计算唤醒率指标：

数据:
- 唤醒尝试次数: ${dataOrganization.event_categories.wakeup_attempts}
- 成功唤醒次数: ${dataOrganization.event_categories.successful_wakeups}

相关事件:
${JSON.stringify(testEvents.filter(e => e.type === 'wakeup' || e.type === 'wakeup_attempt').slice(0, 10), null, 2)}

计算:
1. 唤醒率 = 成功次数 / 尝试次数
2. 分析唤醒失败的原因（如果有）
3. 唤醒延迟统计（如果有时延数据）
4. 与基准值对比（基准: 95%）
5. 给出评价（优秀/良好/需改进）`,
    {
      label: 'wakeup-metrics',
      phase: 'Calculate',
      schema: {
        type: 'object',
        properties: {
          wakeup_rate: { type: 'number', minimum: 0, maximum: 1 },
          wakeup_rate_percentage: { type: 'string' },
          total_attempts: { type: 'number' },
          successful_count: { type: 'number' },
          failed_count: { type: 'number' },
          failure_reasons: {
            type: 'array',
            items: { type: 'string' }
          },
          avg_delay_ms: { type: 'number' },
          benchmark_comparison: {
            type: 'object',
            properties: {
              benchmark: { type: 'number' },
              delta: { type: 'number' },
              meets_requirement: { type: 'boolean' }
            }
          },
          rating: { type: 'string', enum: ['excellent', 'good', 'fair', 'poor'] },
          summary: { type: 'string' }
        },
        required: ['wakeup_rate', 'total_attempts', 'successful_count', 'rating', 'summary']
      }
    }
  ),

  // 指标2: 识别率分析
  () => agent(
    `计算识别准确率指标：

数据:
- 识别事件数: ${dataOrganization.event_categories.recognition_events}

识别事件详情:
${JSON.stringify(testEvents.filter(e => e.type === 'recognition'), null, 2)}

计算:
1. 识别率 = 正确识别数 / 总识别数
2. 常见识别错误分析
3. 识别延迟统计
4. 与基准值对比（基准: 90%）
5. 给出评价`,
    {
      label: 'recognition-metrics',
      phase: 'Calculate',
      schema: {
        type: 'object',
        properties: {
          recognition_rate: { type: 'number', minimum: 0, maximum: 1 },
          recognition_rate_percentage: { type: 'string' },
          total_recognitions: { type: 'number' },
          correct_count: { type: 'number' },
          error_count: { type: 'number' },
          common_errors: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                expected: { type: 'string' },
                actual: { type: 'string' },
                frequency: { type: 'number' }
              }
            }
          },
          avg_delay_ms: { type: 'number' },
          benchmark_comparison: {
            type: 'object',
            properties: {
              benchmark: { type: 'number' },
              delta: { type: 'number' },
              meets_requirement: { type: 'boolean' }
            }
          },
          rating: { type: 'string', enum: ['excellent', 'good', 'fair', 'poor'] },
          summary: { type: 'string' }
        },
        required: ['recognition_rate', 'total_recognitions', 'rating', 'summary']
      }
    }
  ),

  // 指标3: 全双工稳定性分析
  () => agent(
    `计算全双工稳定性指标：

数据:
- 全双工退出次数: ${dataOrganization.event_categories.fullduplex_exits}
- 非预期退出次数: ${dataOrganization.event_categories.unexpected_exits}

退出事件详情:
${JSON.stringify(testEvents.filter(e => e.type === 'fullduplex_exit'), null, 2)}

计算:
1. 稳定性 = 1 - (非预期退出 / 总对话轮次)
2. 分析非预期退出的原因
3. 退出时机分析（是否在关键时刻）
4. 与基准值对比（基准: 95%）
5. 给出评价和改进建议`,
    {
      label: 'fullduplex-metrics',
      phase: 'Calculate',
      schema: {
        type: 'object',
        properties: {
          stability_rate: { type: 'number', minimum: 0, maximum: 1 },
          stability_percentage: { type: 'string' },
          total_exits: { type: 'number' },
          unexpected_exits: { type: 'number' },
          expected_exits: { type: 'number' },
          exit_causes: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                cause: { type: 'string' },
                count: { type: 'number' }
              }
            }
          },
          benchmark_comparison: {
            type: 'object',
            properties: {
              benchmark: { type: 'number' },
              delta: { type: 'number' },
              meets_requirement: { type: 'boolean' }
            }
          },
          rating: { type: 'string', enum: ['excellent', 'good', 'fair', 'poor'] },
          recommendations: {
            type: 'array',
            items: { type: 'string' }
          },
          summary: { type: 'string' }
        },
        required: ['stability_rate', 'total_exits', 'unexpected_exits', 'rating', 'summary']
      }
    }
  ),

  // 指标4: 性能分析
  () => agent(
    `分析性能指标：

性能数据点数: ${performanceData.length}

样本数据:
${JSON.stringify(performanceData.slice(0, 5), null, 2)}

分析:
1. CPU使用率趋势（平均值、峰值、是否稳定）
2. 内存使用趋势（是否有泄漏迹象）
3. 关键进程资源占用（com.cmcc.jarvis, media.swcodec等）
4. 性能瓶颈识别
5. 性能评级和优化建议`,
    {
      label: 'performance-metrics',
      phase: 'Calculate',
      schema: {
        type: 'object',
        properties: {
          cpu_stats: {
            type: 'object',
            properties: {
              average: { type: 'number' },
              peak: { type: 'number' },
              min_idle: { type: 'number' },
              stable: { type: 'boolean' }
            }
          },
          memory_stats: {
            type: 'object',
            properties: {
              average_available_mb: { type: 'number' },
              min_available_mb: { type: 'number' },
              leak_suspected: { type: 'boolean' }
            }
          },
          process_analysis: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                process_name: { type: 'string' },
                avg_cpu: { type: 'number' },
                peak_cpu: { type: 'number' },
                avg_mem_mb: { type: 'number' },
                status: { type: 'string', enum: ['normal', 'high', 'critical'] }
              }
            }
          },
          bottlenecks: {
            type: 'array',
            items: { type: 'string' }
          },
          rating: { type: 'string', enum: ['excellent', 'good', 'fair', 'poor'] },
          optimization_suggestions: {
            type: 'array',
            items: { type: 'string' }
          },
          summary: { type: 'string' }
        },
        required: ['cpu_stats', 'memory_stats', 'rating', 'summary']
      }
    }
  )
])

// 过滤失败的计算
const validMetrics = metricsResults.filter(Boolean)
log(`✓ 完成 ${validMetrics.length}/4 个指标计算`)

const wakeupMetrics = validMetrics[0]
const recognitionMetrics = validMetrics[1]
const fullduplexMetrics = validMetrics[2]
const performanceMetrics = validMetrics[3]

// 阶段3: 生成完整报告
phase('Generate')

const fullReport = await agent(
  `生成完整的测试报告（Markdown格式）：

## 测试会话信息
- 会话ID: ${sessionId}
- 测试时间: ${dataOrganization.time_range.start} ~ ${dataOrganization.time_range.end}
- 测试时长: ${Math.round(dataOrganization.time_range.duration_seconds / 60)} 分钟
- 测试配置: ${JSON.stringify(testConfig, null, 2)}

## 指标汇总
### 1. 唤醒率
${JSON.stringify(wakeupMetrics, null, 2)}

### 2. 识别准确率
${JSON.stringify(recognitionMetrics, null, 2)}

### 3. 全双工稳定性
${JSON.stringify(fullduplexMetrics, null, 2)}

### 4. 性能分析
${JSON.stringify(performanceMetrics, null, 2)}

## 关键事件
${JSON.stringify(dataOrganization.critical_events, null, 2)}

---

请生成一份专业、清晰、结构化的测试报告，包含：

# AI辅助语音测试报告

## 1. 测试概览
- 测试信息摘要
- 总体评价（通过/不通过）
- 核心指标一览表

## 2. 详细指标分析
### 2.1 唤醒性能
- 唤醒率及评价
- 失败原因分析
- 改进建议

### 2.2 识别准确性
- 识别率及评价
- 常见错误分析
- 改进建议

### 2.3 全双工稳定性
- 稳定性评分
- 非预期退出分析
- 改进建议

### 2.4 系统性能
- CPU/内存表现
- 性能瓶颈
- 优化建议

## 3. 关键问题
列出测试中发现的关键问题（如果有）

## 4. 总体结论
- 测试结论（通过/不通过）
- 综合评价
- 下一步行动建议

## 5. 附录
- 详细数据
- 测试日志链接`,
  {
    label: 'generate-report',
    schema: {
      type: 'object',
      properties: {
        report_markdown: { type: 'string' },
        overall_status: { type: 'string', enum: ['PASS', 'FAIL', 'WARNING'] },
        pass_criteria_met: { type: 'boolean' },
        summary: { type: 'string' }
      },
      required: ['report_markdown', 'overall_status', 'pass_criteria_met', 'summary']
    }
  }
)

log(`✓ 报告生成完成 - 状态: ${fullReport.overall_status}`)

// 阶段4: AI审核报告质量
phase('Review')

const reportReview = await agent(
  `审核生成的测试报告质量：

报告内容:
${fullReport.report_markdown}

审核要点:
1. 报告结构是否完整？
2. 数据分析是否准确？
3. 结论是否有充分支撑？
4. 是否遗漏重要信息？
5. 语言是否专业清晰？
6. 改进建议是否具体可行？

给出审核结果和改进建议`,
  {
    label: 'review-report',
    schema: {
      type: 'object',
      properties: {
        quality_score: { type: 'number', minimum: 0, maximum: 100 },
        completeness: { type: 'boolean' },
        accuracy: { type: 'boolean' },
        clarity: { type: 'boolean' },
        issues_found: {
          type: 'array',
          items: { type: 'string' }
        },
        improvement_suggestions: {
          type: 'array',
          items: { type: 'string' }
        },
        approved: { type: 'boolean' }
      },
      required: ['quality_score', 'completeness', 'accuracy', 'approved']
    }
  }
)

log(`✓ 报告审核完成 - 质量评分: ${reportReview.quality_score}/100, 通过审核: ${reportReview.approved}`)

// 如果审核未通过，记录问题
if (!reportReview.approved) {
  log(`⚠️  报告质量问题: ${reportReview.issues_found.join(', ')}`)
}

// 返回完整结果
return {
  success: true,
  session_id: sessionId,
  test_duration_seconds: dataOrganization.time_range.duration_seconds,
  metrics: {
    wakeup: wakeupMetrics,
    recognition: recognitionMetrics,
    fullduplex: fullduplexMetrics,
    performance: performanceMetrics
  },
  report: {
    markdown: fullReport.report_markdown,
    overall_status: fullReport.overall_status,
    pass_criteria_met: fullReport.pass_criteria_met,
    summary: fullReport.summary
  },
  quality_review: reportReview,
  critical_events: dataOrganization.critical_events
}
