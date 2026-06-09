<template>
  <el-card class="log-panel" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>📋 实时日志</span>
        <div class="header-actions">
          <el-input
            v-model="searchText"
            placeholder="搜索日志..."
            size="small"
            clearable
            style="width: 200px; margin-right: 10px;"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button size="small" @click="clearLogs">清空</el-button>
          <el-button size="small" @click="exportLogs">导出</el-button>
        </div>
      </div>
    </template>

    <!-- 日志过滤器 -->
    <div class="filter-bar">
      <el-radio-group v-model="selectedSeverity" size="small">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="info">Info</el-radio-button>
        <el-radio-button value="warning">Warning</el-radio-button>
        <el-radio-button value="critical">Critical</el-radio-button>
      </el-radio-group>

      <el-checkbox-group v-model="selectedTypes" size="small" style="margin-left: 20px;">
        <el-checkbox value="wakeup">唤醒</el-checkbox>
        <el-checkbox value="recognition">识别</el-checkbox>
        <el-checkbox value="fullduplex_exit">全双工退出</el-checkbox>
        <el-checkbox value="error">错误</el-checkbox>
      </el-checkbox-group>
    </div>

    <!-- 日志列表 -->
    <div class="log-container" ref="logContainerRef">
      <div
        v-for="(event, index) in filteredLogs"
        :key="index"
        class="log-item"
        :class="getSeverityClass(event.severity)"
        @click="handleLogClick(event)"
      >
        <div class="log-header">
          <el-tag
            :type="getTagType(event.severity)"
            size="small"
            effect="dark"
          >
            {{ event.severity.toUpperCase() }}
          </el-tag>
          <el-tag
            size="small"
            :style="{ backgroundColor: event.color, border: 'none', color: 'white' }"
          >
            {{ event.type }}
          </el-tag>
          <span class="log-time">{{ event.timestamp }}</span>
        </div>
        <div class="log-content">
          <span class="log-annotation">{{ event.annotation }}</span>
          <span class="log-description">{{ event.description }}</span>
        </div>
        <div v-if="event.raw_log" class="log-raw">
          <el-text type="info" size="small">{{ event.raw_log }}</el-text>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="filteredLogs.length === 0"
        description="暂无日志数据"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()

const searchText = ref('')
const selectedSeverity = ref('all')
const selectedTypes = ref<string[]>([])
const logContainerRef = ref<HTMLElement>()

// 过滤日志
const filteredLogs = computed(() => {
  let logs = testStore.logEvents

  // 按严重程度过滤
  if (selectedSeverity.value !== 'all') {
    logs = logs.filter(e => e.severity === selectedSeverity.value)
  }

  // 按类型过滤
  if (selectedTypes.value.length > 0) {
    logs = logs.filter(e => selectedTypes.value.includes(e.type))
  }

  // 搜索过滤
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    logs = logs.filter(e =>
      e.description.toLowerCase().includes(search) ||
      e.annotation.toLowerCase().includes(search) ||
      e.raw_log?.toLowerCase().includes(search)
    )
  }

  return logs
})

// 自动滚动到底部
watch(() => testStore.logEvents.length, () => {
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
})

const getSeverityClass = (severity: string) => {
  return `severity-${severity}`
}

const getTagType = (severity: string) => {
  const typeMap: Record<string, any> = {
    info: 'info',
    warning: 'warning',
    critical: 'danger'
  }
  return typeMap[severity] || 'info'
}

const handleLogClick = (event: any) => {
  if (event.severity === 'critical') {
    // 点击关键事件，触发错误诊断
    testStore.diagnoseError(event)
  }
}

const clearLogs = () => {
  testStore.logEvents = []
  ElMessage.success('日志已清空')
}

const exportLogs = () => {
  // TODO: 实现日志导出
  const logs = JSON.stringify(testStore.logEvents, null, 2)
  const blob = new Blob([logs], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `test-logs-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('日志已导出')
}
</script>

<style scoped>
.log-panel {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 4px;
}

.log-item {
  background: white;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  border-left: 3px solid #dcdfe6;
  cursor: pointer;
  transition: all 0.3s;
}

.log-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateX(2px);
}

.log-item.severity-info {
  border-left-color: #409eff;
}

.log-item.severity-warning {
  border-left-color: #e6a23c;
}

.log-item.severity-critical {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.log-time {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-annotation {
  font-weight: 600;
  color: #303133;
}

.log-description {
  font-size: 13px;
  color: #606266;
}

.log-raw {
  margin-top: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  overflow-x: auto;
}
</style>
