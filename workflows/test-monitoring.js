// workflows/test-monitoring.js
// 实时测试监控Workflow - 并行监控日志和性能

export const meta = {
  name: 'test-monitoring',
  description: '实时监控测试过程，并行分析日志和性能指标',
  phases: [
    { title: 'Initialize', detail: '初始化设备连接和数据收集' },
    { title: 'Monitor', detail: '并行监控日志流和性能指标' },
    { title: 'Analyze', detail: '实时分析事件' },
    { title: 'Alert', detail: '检测重大错误并告警' }
  ]
}

// 从args获取设备IP和测试配置
const deviceIP = args.deviceIP || '10.7.187.15:5555'
const testConfig = args.testConfig || {}

// 阶段1: 初始化
phase('Initialize')
log(`开始监控设备: ${deviceIP}`)

// 检查设备连接
const deviceStatus = await agent(
  `检查ADB设备 ${deviceIP} 是否已连接，如果未连接则连接它`,
  {
    label: 'device-init',
    schema: {
      type: 'object',
      properties: {
        connected: { type: 'boolean' },
        message: { type: 'string' }
      },
      required: ['connected', 'message']
    }
  }
)

if (!deviceStatus.connected) {
  log(`❌ 设备连接失败: ${deviceStatus.message}`)
  return { success: false, error: '设备未连接' }
}

log(`✓ 设备已连接`)

// 阶段2: 并行监控
phase('Monitor')
log('启动并行监控任务...')

// 定义监控时长（秒）
const monitorDuration = args.duration || 60

// 并行启动两个持续监控的Agent
const monitoringTasks = await parallel([
  // 任务1: 日志监控Agent
  () => agent(
    `持续监控设备 ${deviceIP} 的logcat日志 ${monitorDuration} 秒，
    识别以下事件：
    1. 唤醒事件 (WakeUp, 唤醒成功)
    2. 语音识别事件 (ASR, recognition, 识别结果)
    3. 全双工退出事件 (exit_interactive, FullDuplexOp)
    4. 错误事件 (Exception, Error, Crash, ANR)

    使用 adb -s ${deviceIP} logcat -v time 命令采集日志。

    返回识别到的所有事件列表，包括：
    - 时间戳
    - 事件类型
    - 事件详情
    - 严重程度 (info/warning/critical)
    - 原始日志行`,
    {
      label: 'log-monitor',
      phase: 'Monitor',
      schema: {
        type: 'object',
        properties: {
          events: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                timestamp: { type: 'string' },
                type: { type: 'string', enum: ['wakeup', 'recognition', 'fullduplex_exit', 'error', 'other'] },
                severity: { type: 'string', enum: ['info', 'warning', 'critical'] },
                description: { type: 'string' },
                details: { type: 'object' },
                raw_log: { type: 'string' }
              },
              required: ['timestamp', 'type', 'severity', 'description']
            }
          },
          summary: { type: 'string' }
        },
        required: ['events', 'summary']
      }
    }
  ),

  // 任务2: 性能监控Agent
  () => agent(
    `持续监控设备 ${deviceIP} 的性能指标 ${monitorDuration} 秒，
    每2秒采样一次，监控：
    1. CPU使用率 (通过 top 命令)
    2. 内存使用情况 (通过 cat /proc/meminfo)
    3. 关键进程资源占用：
       - com.cmcc.jarvis
       - media.swcodec
       - audioserver

    检测性能异常：
    - CPU idle < 10% (持续高负载)
    - 可用内存 < 200MB (内存不足)
    - media.swcodec CPU > 350% (音频编解码过载)

    返回：
    - 性能指标时序数据
    - 检测到的性能警告
    - 性能趋势分析`,
    {
      label: 'perf-monitor',
      phase: 'Monitor',
      schema: {
        type: 'object',
        properties: {
          metrics: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                timestamp: { type: 'number' },
                cpu_usage: { type: 'number' },
                cpu_idle: { type: 'number' },
                mem_available_mb: { type: 'number' },
                processes: {
                  type: 'object',
                  additionalProperties: {
                    type: 'object',
                    properties: {
                      cpu: { type: 'number' },
                      mem_mb: { type: 'number' }
                    }
                  }
                }
              },
              required: ['timestamp', 'cpu_usage', 'mem_available_mb']
            }
          },
          warnings: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                type: { type: 'string' },
                severity: { type: 'string' },
                message: { type: 'string' },
                timestamp: { type: 'number' }
              },
              required: ['type', 'message']
            }
          },
          trend_analysis: { type: 'string' }
        },
        required: ['metrics', 'warnings', 'trend_analysis']
      }
    }
  )
])

const logEvents = monitoringTasks[0]
const perfData = monitoringTasks[1]

log(`✓ 监控完成 - 日志事件: ${logEvents.events.length}, 性能警告: ${perfData.warnings.length}`)

// 阶段3: 分析事件
phase('Analyze')
log('开始多维度分析...')

// 对每个关键事件进行深度分析（使用pipeline，无需barrier）
const criticalEvents = logEvents.events.filter(e => e.severity === 'critical')

const eventAnalysis = await pipeline(
  criticalEvents,
  // Stage 1: 分析每个关键事件
  event => agent(
    `深度分析这个关键事件：
    类型: ${event.type}
    描述: ${event.description}
    原始日志: ${event.raw_log}

    分析：
    1. 事件发生的根本原因
    2. 是否为已知问题
    3. 对测试的影响程度
    4. 是否需要立即告警`,
    {
      label: `analyze-${event.type}`,
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          root_cause: { type: 'string' },
          known_issue: { type: 'boolean' },
          impact_level: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
          needs_alert: { type: 'boolean' },
          recommendation: { type: 'string' }
        },
        required: ['root_cause', 'impact_level', 'needs_alert']
      }
    }
  ),

  // Stage 2: 关联性能数据分析
  (analysis, originalEvent) => {
    // 查找事件发生时的性能数据
    const eventTime = new Date(originalEvent.timestamp).getTime() / 1000
    const relatedMetrics = perfData.metrics.filter(
      m => Math.abs(m.timestamp - eventTime) < 5  // 前后5秒内的性能数据
    )

    return agent(
      `综合分析事件与性能数据的关联：

      事件: ${originalEvent.description}
      根因分析: ${analysis.root_cause}

      相关性能数据（事件前后5秒）:
      ${JSON.stringify(relatedMetrics, null, 2)}

      分析：
      1. 性能数据是否支持根因分析？
      2. 是否存在性能瓶颈导致该事件？
      3. 综合诊断结论`,
      {
        label: `correlate-${originalEvent.type}`,
        phase: 'Analyze',
        schema: {
          type: 'object',
          properties: {
            performance_related: { type: 'boolean' },
            bottleneck: { type: 'string' },
            final_diagnosis: { type: 'string' }
          },
          required: ['performance_related', 'final_diagnosis']
        }
      }
    )
  }
).then(results => results.filter(Boolean))  // 过滤掉失败的分析

log(`✓ 事件分析完成 - 分析了 ${eventAnalysis.length} 个关键事件`)

// 阶段4: 告警检测
phase('Alert')

// 检查是否需要发出告警
const needsAlert = eventAnalysis.filter(a => a && a.needs_alert)

if (needsAlert.length > 0 || perfData.warnings.length > 0) {
  log(`⚠️  检测到 ${needsAlert.length} 个关键事件需要告警`)

  // 生成综合告警报告
  const alertReport = await agent(
    `生成告警报告（Markdown格式）：

    ## 关键事件告警
    ${JSON.stringify(needsAlert, null, 2)}

    ## 性能警告
    ${JSON.stringify(perfData.warnings, null, 2)}

    生成一份简洁清晰的告警报告，包括：
    1. 告警摘要（2-3句话）
    2. 关键问题列表
    3. 建议的处理措施
    4. 是否建议暂停测试`,
    {
      label: 'alert-report',
      schema: {
        type: 'object',
        properties: {
          summary: { type: 'string' },
          critical_issues: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                issue: { type: 'string' },
                severity: { type: 'string' },
                action: { type: 'string' }
              },
              required: ['issue', 'severity', 'action']
            }
          },
          recommend_pause: { type: 'boolean' },
          report_markdown: { type: 'string' }
        },
        required: ['summary', 'critical_issues', 'recommend_pause', 'report_markdown']
      }
    }
  )

  log(`⚠️  ${alertReport.summary}`)

  return {
    success: true,
    alert: true,
    alert_report: alertReport,
    log_events: logEvents.events,
    performance_data: perfData,
    event_analysis: eventAnalysis
  }
}

log('✓ 监控周期完成，未检测到需要告警的问题')

// 返回监控结果
return {
  success: true,
  alert: false,
  log_events: logEvents.events,
  performance_data: perfData,
  event_analysis: eventAnalysis,
  summary: {
    total_events: logEvents.events.length,
    critical_events: criticalEvents.length,
    performance_warnings: perfData.warnings.length,
    trend: perfData.trend_analysis
  }
}
