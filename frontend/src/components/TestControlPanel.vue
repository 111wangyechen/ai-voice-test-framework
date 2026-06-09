<template>
  <el-card class="control-panel" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>🎛️ 测试控制</span>
      </div>
    </template>

    <el-form :model="testStore.testConfig" label-width="120px">
      <el-form-item label="设备IP">
        <el-input
          v-model="testStore.testConfig.deviceIP"
          placeholder="10.7.187.15:5555"
          :disabled="testStore.isRunning"
        />
      </el-form-item>

      <el-form-item label="测试场景">
        <el-select
          v-model="testStore.testConfig.scenario"
          placeholder="请选择测试场景"
          :disabled="testStore.isRunning"
        >
          <el-option label="全双工语音交互测试" value="fullduplex" />
          <el-option label="唤醒率测试" value="wakeup" />
          <el-option label="语音识别率测试" value="recognition" />
        </el-select>
      </el-form-item>

      <el-form-item label="监控时长">
        <el-input-number
          v-model="testStore.testConfig.duration"
          :min="60"
          :max="3600"
          :step="60"
          :disabled="testStore.isRunning"
        />
        <span style="margin-left: 8px; color: #909399;">秒</span>
      </el-form-item>

      <el-form-item label="AI分析模式">
        <el-radio-group
          v-model="testStore.testConfig.aiMode"
          :disabled="testStore.isRunning"
        >
          <el-radio value="rule_based">
            <el-tooltip content="基于规则匹配，速度快，成本低" placement="top">
              <span>规则匹配模式</span>
            </el-tooltip>
          </el-radio>
          <el-radio value="claude_api">
            <el-tooltip content="使用Claude API进行智能分析，更准确但有API成本" placement="top">
              <span>Claude AI模式</span>
            </el-tooltip>
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item>
        <el-button
          v-if="!testStore.isRunning"
          type="primary"
          size="large"
          @click="handleStartTest"
          :loading="starting"
        >
          <el-icon><VideoPlay /></el-icon>
          开始测试
        </el-button>
        <el-button
          v-else
          type="danger"
          size="large"
          @click="handleStopTest"
        >
          <el-icon><VideoPause /></el-icon>
          停止测试
        </el-button>

        <el-button
          size="large"
          @click="handleGenerateReport"
          :disabled="testStore.isRunning || testStore.logEvents.length === 0"
        >
          <el-icon><Document /></el-icon>
          生成报告
        </el-button>
      </el-form-item>
    </el-form>

    <el-divider />

    <div class="stats-section">
      <el-statistic title="总事件数" :value="testStore.logEvents.length" />
      <el-statistic title="关键事件" :value="criticalEventCount" />
      <el-statistic title="性能采样" :value="testStore.performanceMetrics.length" />
      <el-statistic title="运行时长" :value="runningDuration" suffix="秒" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, VideoPause, Document } from '@element-plus/icons-vue'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()
const starting = ref(false)

const criticalEventCount = computed(() => {
  return testStore.logEvents.filter(e => e.severity === 'critical').length
})

const runningDuration = computed(() => {
  // TODO: 计算实际运行时长
  return testStore.isRunning ? 0 : 0
})

const handleStartTest = async () => {
  try {
    await ElMessageBox.confirm(
      '请确认以下准备工作已完成：\n\n1. 测试音频文件已准备好\n2. 音响设备已连接并调试好音量\n3. 测试环境安静（混响 < 0.3）\n4. 准备开始播放测试音频',
      '准备开始测试',
      {
        confirmButtonText: '已准备好，开始测试',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    starting.value = true
    await testStore.startTest()
    ElMessage.success('测试已启动！请开始播放音频。')

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('启动测试失败：' + error)
    }
  } finally {
    starting.value = false
  }
}

const handleStopTest = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要停止当前测试吗？',
      '停止测试',
      {
        confirmButtonText: '确定停止',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    testStore.stopTest()
    ElMessage.info('测试已停止')

  } catch (error) {
    // 用户取消
  }
}

const handleGenerateReport = async () => {
  try {
    ElMessage.info('正在生成报告...')
    await testStore.generateReport()
  } catch (error) {
    ElMessage.error('生成报告失败：' + error)
  }
}
</script>

<style scoped>
.control-panel {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.stats-section {
  display: flex;
  justify-content: space-around;
  gap: 20px;
}
</style>
