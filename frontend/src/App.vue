<template>
  <div id="app" class="app-container">
    <el-container>
      <!-- 顶部标题栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <h1>🤖 AI辅助语音自动化测试框架</h1>
          <div class="header-info">
            <el-tag v-if="testStore.isRunning" type="success" effect="dark">
              <el-icon><VideoPlay /></el-icon> 测试运行中
            </el-tag>
            <el-tag v-else type="info">
              <el-icon><VideoPause /></el-icon> 就绪
            </el-tag>
            <span class="device-info">设备: {{ testStore.deviceIP }}</span>
          </div>
        </div>
      </el-header>

      <el-container>
        <!-- 主内容区 -->
        <el-main class="main-content">
          <!-- 测试控制面板 -->
          <TestControlPanel />

          <!-- 分栏布局 -->
          <el-row :gutter="20" class="content-row">
            <!-- 左侧：实时日志 -->
            <el-col :span="12">
              <LogPanel />
            </el-col>

            <!-- 右侧：性能监控 -->
            <el-col :span="12">
              <PerformancePanel />
            </el-col>
          </el-row>
        </el-main>
      </el-container>
    </el-container>

    <!-- 人工审核对话框 -->
    <ApprovalDialog />

    <!-- 错误诊断对话框 -->
    <ErrorDiagnosisDialog />

    <!-- 测试报告对话框 -->
    <ReportDialog />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useTestStore } from './stores/testStore'
import TestControlPanel from './components/TestControlPanel.vue'
import LogPanel from './components/LogPanel.vue'
import PerformancePanel from './components/PerformancePanel.vue'
import ApprovalDialog from './components/ApprovalDialog.vue'
import ErrorDiagnosisDialog from './components/ErrorDiagnosisDialog.vue'
import ReportDialog from './components/ReportDialog.vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'

const testStore = useTestStore()

onMounted(() => {
  // 初始化WebSocket连接
  testStore.initWebSocket()
})

onUnmounted(() => {
  // 断开WebSocket连接
  testStore.disconnectWebSocket()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  background: #f5f7fa;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.device-info {
  font-size: 14px;
  opacity: 0.9;
}

.main-content {
  padding: 20px;
}

.content-row {
  margin-top: 20px;
}
</style>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  width: 100%;
  height: 100vh;
}
</style>
