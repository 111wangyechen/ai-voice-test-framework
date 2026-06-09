// workflows/log-file-analysis.js
// 分析本地日志文件的Workflow - 不需要实时设备连接

export const meta = {
  name: 'log-file-analysis',
  description: '分析本地日志文件，识别语音事件和问题',
  phases: [
    { title: 'Load', detail: '加载日志文件' },
    { title: 'Analyze', detail: '多维度分析日志' },
    { title: 'Diagnose', detail: '诊断发现的问题' },
    { title: 'Report', detail: '生成分析报告' }
  ]
}

// 从args获取日志文件路径
const logFilePath = args.logFilePath || 'D:/huiwei/log/cannotwake.log'
const logFileName = logFilePath.split('/').pop()

log(`======================================`)
log(`开始分析日志文件: ${logFileName}`)
log(`======================================`)

// 阶段1: 加载日志文件
phase('Load')
log('读取日志文件...')

const logContent = await agent(
  `读取日志文件 ${logFilePath} 的内容。

  使用Bash工具执行命令读取文件内容。

  返回：
  - 文件大小
  - 总行数
  - 时间范围（第一条和最后一条日志的时间）
  - 前100行内容样本（用于初步分析）`,
  {
    label: 'load-log-file',
    schema: {
      type: 'object',
      properties: {
        file_size_mb: { type: 'number' },
        total_lines: { type: 'number' },
        time_range: {
          type: 'object',
          properties: {
            start: { type: 'string' },
            end: { type: 'string' }
          }
        },
        sample_lines: {
          type: 'array',
          items: { type: 'string' }
        },
        success: { type: 'boolean' }
      },
      required: ['file_size_mb', 'total_lines', 'success']
    }
  }
)

if (!logContent.success) {
  log('❌ 日志文件读取失败')
  return { success: false, error: '无法读取日志文件' }
}

log(`✓ 日志文件已加载`)
log(`  - 文件大小: ${logContent.file_size_mb.toFixed(2)} MB`)
log(`  - 总行数: ${logContent.total_lines}`)
log(`  - 时间范围: ${logContent.time_range?.start} ~ ${logContent.time_range?.end}`)

// 阶段2: 多维度并行分析
phase('Analyze')
log('启动4个分析Agent并行工作...')

const analyses = await parallel([
  // 分析1: 唤醒事件分析
  () => agent(
    `分析日志文件 ${logFilePath} 中的唤醒事件。

    搜索关键词：wakeup, 唤醒, isWakeupEncrypt, WakeUp

    使用grep命令提取相关日志行，然后分析：
    1. 唤醒尝试次数
    2. 成功唤醒次数
    3. 失败唤醒次数
    4. 失败原因分析
    5. 唤醒时间分布

    文件名是: ${logFileName}
    这是一个"无法唤醒"问题的日志，重点分析为什么唤醒失败。`,
    {
      label: 'wakeup-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          total_attempts: { type: 'number' },
          successful_wakeups: { type: 'number' },
          failed_wakeups: { type: 'number' },
          failure_reasons: {
            type: 'array',
            items: { type: 'string' }
          },
          key_findings: {
            type: 'array',
            items: { type: 'string' }
          },
          sample_failed_logs: {
            type: 'array',
            items: { type: 'string' }
          }
        },
        required: ['total_attempts', 'key_findings']
      }
    }
  ),

  // 分析2: 系统异常分析
  () => agent(
    `分析日志文件 ${logFilePath} 中的系统异常。

    搜索关键词：Error, Exception, Crash, ANR, FATAL, died

    识别：
    1. 所有错误类型
    2. 错误发生频率
    3. 是否有进程崩溃
    4. 是否有ANR（应用无响应）
    5. 错误与唤醒失败的关联性`,
    {
      label: 'error-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          total_errors: { type: 'number' },
          error_types: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                type: { type: 'string' },
                count: { type: 'number' },
                severity: { type: 'string' }
              }
            }
          },
          critical_errors: {
            type: 'array',
            items: { type: 'string' }
          },
          related_to_wakeup_failure: { type: 'boolean' },
          analysis: { type: 'string' }
        },
        required: ['total_errors', 'analysis']
      }
    }
  ),

  // 分析3: 音频相关分析
  () => agent(
    `分析日志文件 ${logFilePath} 中的音频系统状态。

    搜索关键词：audio, AudioFlinger, media.swcodec, CSK, 音频

    检查：
    1. 音频系统是否正常运行
    2. 是否有音频设备错误
    3. CSK（语音芯片）状态
    4. 音频编解码器状态
    5. 可能影响唤醒的音频问题`,
    {
      label: 'audio-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          audio_system_status: { type: 'string' },
          csk_status: { type: 'string' },
          audio_issues: {
            type: 'array',
            items: { type: 'string' }
          },
          affects_wakeup: { type: 'boolean' },
          recommendations: {
            type: 'array',
            items: { type: 'string' }
          }
        },
        required: ['audio_system_status', 'affects_wakeup']
      }
    }
  ),

  // 分析4: 时间线分析
  () => agent(
    `分析日志文件 ${logFilePath} 的事件时间线。

    重建从测试开始到唤醒失败的完整时间线：
    1. 识别测试开始时间
    2. 识别唤醒尝试的时间点
    3. 识别系统关键事件
    4. 识别是否有时序问题（超时、竞态等）
    5. 找出唤醒失败的触发点`,
    {
      label: 'timeline-analysis',
      phase: 'Analyze',
      schema: {
        type: 'object',
        properties: {
          timeline: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                timestamp: { type: 'string' },
                event: { type: 'string' },
                significance: { type: 'string' }
              }
            }
          },
          trigger_point: { type: 'string' },
          timing_issues: {
            type: 'array',
            items: { type: 'string' }
          }
        },
        required: ['timeline', 'trigger_point']
      }
    }
  )
])

const validAnalyses = analyses.filter(Boolean)
log(`✓ 完成 ${validAnalyses.length}/4 个维度的分析`)

const wakeupAnalysis = validAnalyses[0]
const errorAnalysis = validAnalyses[1]
const audioAnalysis = validAnalyses[2]
const timelineAnalysis = validAnalyses[3]

// 阶段3: 综合诊断
phase('Diagnose')
log('综合所有分析，诊断根本原因...')

const diagnosis = await agent(
  `基于4个维度的分析结果，综合诊断"无法唤醒"问题的根本原因：

## 1. 唤醒事件分析
${JSON.stringify(wakeupAnalysis, null, 2)}

## 2. 系统异常分析
${JSON.stringify(errorAnalysis, null, 2)}

## 3. 音频系统分析
${JSON.stringify(audioAnalysis, null, 2)}

## 4. 时间线分析
${JSON.stringify(timelineAnalysis, null, 2)}

---

请综合以上4个维度的独立分析，回答：

1. **根本原因是什么？** （给出置信度）
2. **为什么无法唤醒？** （技术层面的详细解释）
3. **是否是已知问题？** （是否在其他日志中也出现过）
4. **如何解决？** （具体的解决方案，按优先级排序）
5. **如何预防？** （避免再次发生的措施）`,
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
            technical_explanation: { type: 'string' }
          },
          required: ['description', 'confidence', 'technical_explanation']
        },
        solutions: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              solution: { type: 'string' },
              priority: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
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
        known_issue: { type: 'boolean' }
      },
      required: ['root_cause', 'solutions', 'prevention_measures']
    }
  }
)

log(`✓ 诊断完成`)
log(`根因: ${diagnosis.root_cause.description}`)
log(`置信度: ${Math.round(diagnosis.root_cause.confidence * 100)}%`)

// 阶段4: 生成报告
phase('Report')
log('生成分析报告...')

const report = await agent(
  `生成"无法唤醒问题"分析报告（Markdown格式）：

文件: ${logFileName}
时间范围: ${logContent.time_range?.start} ~ ${logContent.time_range?.end}

诊断结果: ${JSON.stringify(diagnosis, null, 2)}

生成完整的Markdown报告，包括：
# 日志分析报告 - 无法唤醒问题

## 1. 概览
- 文件信息
- 测试时间
- 问题摘要

## 2. 根本原因分析
- 根因描述
- 置信度
- 技术解释

## 3. 详细分析
### 3.1 唤醒事件分析
### 3.2 系统异常分析
### 3.3 音频系统分析
### 3.4 时间线分析

## 4. 解决方案（按优先级）

## 5. 预防措施

## 6. 附录
- 关键日志片段
- 数据统计`,
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

log('✓ 报告生成完成')

log(`======================================`)
log(`分析完成！`)
log(`======================================`)

// 返回完整结果
return {
  success: true,
  log_file: logFileName,
  log_info: logContent,
  analyses: {
    wakeup: wakeupAnalysis,
    errors: errorAnalysis,
    audio: audioAnalysis,
    timeline: timelineAnalysis
  },
  diagnosis: diagnosis,
  report_markdown: report.markdown_report
}
