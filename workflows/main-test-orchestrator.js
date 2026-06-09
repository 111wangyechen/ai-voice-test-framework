// workflows/main-test-orchestrator.js
// 主测试编排Workflow - 编排整个测试流程

export const meta = {
  name: 'main-test-orchestrator',
  description: '编排完整的语音测试流程：监控→分析→诊断→报告',
  phases: [
    { title: 'Setup', detail: '初始化设备和测试环境' },
    { title: 'Monitor', detail: '实时监控测试过程' },
    { title: 'Diagnose', detail: '诊断发现的错误（如有）' },
    { title: 'Report', detail: '生成测试报告' },
    { title: 'Review', detail: '等待人工审核' }
  ]
}

// 获取测试配置
const testConfig = args.testConfig || {}
const deviceIP = testConfig.deviceIP || '10.7.187.15:5555'
const monitorDuration = testConfig.duration || 300  // 默认5分钟
const scenario = testConfig.scenario || 'fullduplex'  // 测试场景

log(`======================================`)
log(`开始 ${scenario} 测试`)
log(`设备: ${deviceIP}`)
log(`监控时长: ${monitorDuration}秒`)
log(`======================================`)

// 阶段1: 初始化
phase('Setup')
log('初始化测试环境...')

// 请求人工确认音频准备就绪
const audioReady = await agent(
  `请通过前端界面通知用户：

  "请确认以下准备工作已完成：
  1. 测试音频文件已准备好
  2. 音响设备已连接并调试好音量
  3. 测试环境安静（混响 < 0.3）
  4. 准备开始播放测试音频"

  模拟等待用户确认（实际应用中通过WebSocket等待前端响应）。
  返回确认状态。`,
  {
    label: 'audio-ready-check',
    schema: {
      type: 'object',
      properties: {
        ready: { type: 'boolean' },
        message: { type: 'string' }
      },
      required: ['ready', 'message']
    }
  }
)

if (!audioReady || !audioReady.ready) {
  log('❌ 用户取消或未准备好，测试终止')
  return {
    success: false,
    stage: 'setup',
    error: '用户未确认音频准备就绪'
  }
}

log('✓ 用户确认音频就绪，开始测试')

// 阶段2: 启动监控Workflow
phase('Monitor')
log(`启动监控Workflow（${monitorDuration}秒）...`)

const monitoringResult = await workflow(
  { scriptPath: 'workflows/test-monitoring.js' },
  {
    deviceIP: deviceIP,
    duration: monitorDuration,
    testConfig: testConfig
  }
)

if (!monitoringResult.success) {
  log('❌ 监控Workflow执行失败')
  return {
    success: false,
    stage: 'monitor',
    error: monitoringResult.error
  }
}

log(`✓ 监控完成`)
log(`  - 总事件数: ${monitoringResult.summary.total_events}`)
log(`  - 关键事件: ${monitoringResult.summary.critical_events}`)
log(`  - 性能警告: ${monitoringResult.summary.performance_warnings}`)

// 检查是否需要告警
if (monitoringResult.alert) {
  log(`⚠️  检测到需要告警的问题`)
  log(`告警摘要: ${monitoringResult.alert_report.summary}`)

  // 如果建议暂停测试
  if (monitoringResult.alert_report.recommend_pause) {
    log('⚠️  建议暂停测试进行人工审核')

    // 请求人工决策
    const userDecision = await agent(
      `通知用户检测到重大问题，需要人工决策：

      告警报告:
      ${monitoringResult.alert_report.report_markdown}

      关键问题:
      ${JSON.stringify(monitoringResult.alert_report.critical_issues, null, 2)}

      请用户选择：
      1. 继续测试（忽略告警）
      2. 暂停测试，进行错误诊断
      3. 终止测试

      返回用户决策`,
      {
        label: 'user-decision',
        schema: {
          type: 'object',
          properties: {
            decision: { type: 'string', enum: ['continue', 'diagnose', 'abort'] },
            reason: { type: 'string' }
          },
          required: ['decision']
        }
      }
    )

    if (userDecision.decision === 'abort') {
      log('❌ 用户选择终止测试')
      return {
        success: false,
        stage: 'monitor',
        aborted_by_user: true,
        monitoring_result: monitoringResult
      }
    }

    if (userDecision.decision === 'diagnose') {
      log('开始错误诊断流程...')
      // 继续到诊断阶段
    }
  }
}

// 阶段3: 错误诊断（如果有关键错误）
phase('Diagnose')

const criticalErrors = monitoringResult.event_analysis?.filter(
  a => a && a.needs_alert
) || []

let diagnosisResults = []

if (criticalErrors.length > 0) {
  log(`开始诊断 ${criticalErrors.length} 个关键错误...`)

  // 使用pipeline对每个错误进行诊断（流水线处理，不等待全部完成）
  diagnosisResults = await pipeline(
    criticalErrors,
    // Stage 1: 找到对应的原始错误事件
    error => {
      const originalEvent = monitoringResult.log_events.find(
        e => e.description === error.root_cause
      )
      return originalEvent || { type: 'unknown', description: error.root_cause }
    },
    // Stage 2: 调用错误诊断Workflow
    (errorEvent, originalError, index) => {
      log(`诊断错误 ${index + 1}/${criticalErrors.length}: ${errorEvent.description}`)
      return workflow(
        { scriptPath: 'workflows/error-diagnosis.js' },
        {
          errorEvent: errorEvent,
          deviceIP: deviceIP
        }
      )
    }
  )

  const successfulDiagnoses = diagnosisResults.filter(Boolean)
  log(`✓ 完成 ${successfulDiagnoses.length}/${criticalErrors.length} 个错误诊断`)

  // 输出每个诊断的根因
  successfulDiagnoses.forEach((diag, i) => {
    if (diag.success && diag.final_diagnosis) {
      log(`  ${i + 1}. ${diag.final_diagnosis.root_cause.description} (置信度: ${Math.round(diag.final_diagnosis.root_cause.confidence * 100)}%)`)
    }
  })
} else {
  log('✓ 未检测到需要诊断的关键错误')
}

// 阶段4: 生成测试报告
phase('Report')
log('开始生成测试报告...')

const reportResult = await workflow(
  { scriptPath: 'workflows/report-generation.js' },
  {
    sessionId: args.sessionId || `test_${Date.now()}`,
    testEvents: monitoringResult.log_events,
    performanceData: monitoringResult.performance_data?.metrics || [],
    testConfig: testConfig
  }
)

if (!reportResult.success) {
  log('❌ 报告生成失败')
  return {
    success: false,
    stage: 'report',
    error: reportResult.error,
    monitoring_result: monitoringResult,
    diagnosis_results: diagnosisResults
  }
}

log(`✓ 报告生成完成`)
log(`  - 状态: ${reportResult.report.overall_status}`)
log(`  - 唤醒率: ${reportResult.metrics.wakeup.wakeup_rate_percentage}`)
log(`  - 识别率: ${reportResult.metrics.recognition.recognition_rate_percentage}`)
log(`  - 稳定性: ${reportResult.metrics.fullduplex.stability_percentage}`)

// 阶段5: 人工审核
phase('Review')
log('等待人工审核报告...')

const humanReview = await agent(
  `通知用户测试完成，请审核报告：

  ## 测试报告

  ${reportResult.report.markdown}

  ## 质量评分
  - AI质量评分: ${reportResult.quality_review.quality_score}/100
  - AI审核通过: ${reportResult.quality_review.approved ? '是' : '否'}

  ${reportResult.quality_review.issues_found?.length > 0 ? `
  ## 发现的问题
  ${reportResult.quality_review.issues_found.join('\n')}
  ` : ''}

  请用户审核并决定：
  1. 接受报告
  2. 要求重新生成报告
  3. 标记需要关注的问题

  返回用户审核结果`,
  {
    label: 'human-review',
    schema: {
      type: 'object',
      properties: {
        approved: { type: 'boolean' },
        comments: { type: 'string' },
        issues_flagged: {
          type: 'array',
          items: { type: 'string' }
        }
      },
      required: ['approved']
    }
  }
)

log(`${humanReview.approved ? '✓' : '⚠️'} 用户${humanReview.approved ? '接受' : '拒绝'}报告`)
if (humanReview.comments) {
  log(`用户评论: ${humanReview.comments}`)
}

// 返回最终结果
log(`======================================`)
log(`测试流程完成`)
log(`状态: ${reportResult.report.overall_status}`)
log(`======================================`)

return {
  success: true,
  test_scenario: scenario,
  device_ip: deviceIP,
  duration_seconds: monitorDuration,
  stages: {
    setup: { completed: true },
    monitor: {
      completed: true,
      alert: monitoringResult.alert,
      summary: monitoringResult.summary
    },
    diagnose: {
      completed: true,
      errors_diagnosed: diagnosisResults.filter(Boolean).length,
      diagnoses: diagnosisResults
    },
    report: {
      completed: true,
      status: reportResult.report.overall_status,
      metrics: reportResult.metrics
    },
    review: {
      completed: true,
      approved: humanReview.approved
    }
  },
  final_report: reportResult.report.markdown,
  human_review: humanReview
}
