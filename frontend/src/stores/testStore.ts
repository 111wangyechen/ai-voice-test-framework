import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// API基础URL
const API_BASE_URL = 'http://localhost:8000'
// WebSocket基础URL（与API同源，协议换成ws）
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws')

export interface TestConfig {
  deviceIP: string
  duration: number
  scenario: 'fullduplex' | 'wakeup' | 'recognition'
  aiMode: 'rule_based' | 'claude_api'  // 用户可选的AI模式
}

export interface LogEvent {
  timestamp: string
  type: string
  severity: 'info' | 'warning' | 'critical'
  description: string
  annotation: string
  color: string
  raw_log?: string
}

export interface PerformanceMetric {
  timestamp: number
  cpu_usage: number
  cpu_idle: number
  mem_available_mb: number
  processes: Record<string, { cpu: number; mem_mb: number }>
}

export const useTestStore = defineStore('test', () => {
  // 状态
  const isRunning = ref(false)
  const deviceIP = ref('10.7.187.15:5555')
  const testConfig = ref<TestConfig>({
    deviceIP: '10.7.187.15:5555',
    duration: 300,
    scenario: 'fullduplex',
    aiMode: 'rule_based'
  })

  const logEvents = ref<LogEvent[]>([])
  const performanceMetrics = ref<PerformanceMetric[]>([])

  // WebSocket（原生WebSocket，与后端FastAPI的 @app.websocket 端点匹配）
  let logSocket: WebSocket | null = null
  let perfSocket: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let manualClose = false

  // 审核相关
  const pendingApproval = ref<{
    show: boolean
    message: string
    type: string
    options?: string[]
  }>({
    show: false,
    message: '',
    type: ''
  })

  // 错误诊断
  const errorDiagnosis = ref<{
    show: boolean
    error: any
    diagnosis: any
  }>({
    show: false,
    error: null,
    diagnosis: null
  })

  // 测试报告
  const testReport = ref<{
    show: boolean
    markdown: string
    metrics: any
  }>({
    show: false,
    markdown: '',
    metrics: null
  })

  // WebSocket初始化
  const initWebSocket = () => {
    manualClose = false

    // 日志WebSocket - 连接后端 /ws/logs (原生WebSocket)
    const connectLogs = () => {
      logSocket = new WebSocket(`${WS_BASE_URL}/ws/logs`)

      logSocket.onmessage = (event) => {
        try {
          const data: LogEvent = JSON.parse(event.data)
          logEvents.value.push(data)
          // 保持最近1000条日志
          if (logEvents.value.length > 1000) {
            logEvents.value.shift()
          }
        } catch (e) {
          console.error('解析日志消息失败:', e)
        }
      }

      logSocket.onclose = () => {
        if (!manualClose) {
          // 5秒后自动重连
          reconnectTimer = setTimeout(connectLogs, 5000)
        }
      }

      logSocket.onerror = (err) => {
        console.error('日志WebSocket错误:', err)
      }
    }

    // 性能WebSocket - 连接后端 /ws/performance (原生WebSocket)
    const connectPerf = () => {
      perfSocket = new WebSocket(`${WS_BASE_URL}/ws/performance`)

      perfSocket.onmessage = (event) => {
        try {
          const data: PerformanceMetric = JSON.parse(event.data)
          performanceMetrics.value.push(data)
          // 保持最近100个数据点
          if (performanceMetrics.value.length > 100) {
            performanceMetrics.value.shift()
          }
        } catch (e) {
          console.error('解析性能消息失败:', e)
        }
      }

      perfSocket.onclose = () => {
        if (!manualClose) {
          setTimeout(connectPerf, 5000)
        }
      }

      perfSocket.onerror = (err) => {
        console.error('性能WebSocket错误:', err)
      }
    }

    connectLogs()
    connectPerf()
  }

  const disconnectWebSocket = () => {
    manualClose = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    logSocket?.close()
    perfSocket?.close()
    logSocket = null
    perfSocket = null
  }

  // API调用
  const startTest = async () => {
    try {
      isRunning.value = true
      logEvents.value = []
      performanceMetrics.value = []

      const response = await axios.post(`${API_BASE_URL}/api/test/start`, testConfig.value)
      console.log('测试已启动:', response.data)

      // TODO: 轮询workflow状态
      // const workflowId = response.data.workflow_id
      // pollWorkflowStatus(workflowId)

    } catch (error) {
      console.error('启动测试失败:', error)
      isRunning.value = false
    }
  }

  const stopTest = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/test/stop`)
      console.log('测试已停止')
    } catch (error) {
      console.error('停止测试失败:', error)
    } finally {
      // 无论后端是否成功，前端都回到就绪状态
      isRunning.value = false
    }
  }

  const diagnoseError = async (errorEvent: LogEvent) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/error/diagnose`, {
        error_event: errorEvent,
        device_ip: deviceIP.value
      })

      // 显示诊断结果
      errorDiagnosis.value = {
        show: true,
        error: errorEvent,
        diagnosis: response.data.diagnosis
      }

    } catch (error) {
      console.error('错误诊断失败:', error)
    }
  }

  const generateReport = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/report/generate`, {
        session_id: `test_${Date.now()}`,
        test_events: logEvents.value,
        performance_data: performanceMetrics.value,
        test_config: testConfig.value
      })

      // 显示报告
      testReport.value = {
        show: true,
        markdown: response.data.report?.markdown || '',
        metrics: response.data.report?.metrics
      }

    } catch (error) {
      console.error('生成报告失败:', error)
    }
  }

  // 人工审核响应
  const approveRequest = (approved: boolean, comments?: string) => {
    // TODO: 发送审核结果到后端
    console.log('审核结果:', approved, comments)
    pendingApproval.value.show = false
  }

  return {
    // 状态
    isRunning,
    deviceIP,
    testConfig,
    logEvents,
    performanceMetrics,
    pendingApproval,
    errorDiagnosis,
    testReport,

    // 方法
    initWebSocket,
    disconnectWebSocket,
    startTest,
    stopTest,
    diagnoseError,
    generateReport,
    approveRequest
  }
})
