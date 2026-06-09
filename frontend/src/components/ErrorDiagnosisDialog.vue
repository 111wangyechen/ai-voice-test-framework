<template>
  <el-dialog
    v-model="testStore.errorDiagnosis.show"
    title="🔍 错误诊断报告"
    width="900px"
    :fullscreen="isFullscreen"
  >
    <template #header>
      <div class="dialog-header">
        <span>🔍 错误诊断报告</span>
        <el-button
          :icon="isFullscreen ? 'FullScreen' : 'FullScreenExit'"
          circle
          @click="isFullscreen = !isFullscreen"
        />
      </div>
    </template>

    <div v-if="diagnosis" class="diagnosis-container">
      <!-- 错误概览 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <strong>错误概览</strong>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="错误类型">
            <el-tag>{{ error?.type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityTagType(error?.severity)">
              {{ error?.severity }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="时间">
            {{ error?.timestamp }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ error?.description }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 根本原因 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <strong>🎯 根本原因</strong>
        </template>
        <el-alert
          :type="diagnosis.root_cause.confidence > 0.7 ? 'success' : 'warning'"
          :closable="false"
        >
          <template #title>
            <strong>{{ diagnosis.root_cause.description }}</strong>
          </template>
          <div style="margin-top: 8px;">
            置信度: {{ Math.round(diagnosis.root_cause.confidence * 100) }}%
          </div>
        </el-alert>

        <div v-if="diagnosis.root_cause.supporting_evidence" class="evidence-list">
          <h4>支持证据：</h4>
          <ul>
            <li v-for="(evidence, i) in diagnosis.root_cause.supporting_evidence" :key="i">
              {{ evidence }}
            </li>
          </ul>
        </div>
      </el-card>

      <!-- 多维度分析 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <strong>📊 多维度分析</strong>
        </template>
        <el-collapse>
          <el-collapse-item title="代码逻辑分析" name="logic">
            <pre class="analysis-content">{{ JSON.stringify(diagnosis.dimensional_analyses?.logic, null, 2) }}</pre>
          </el-collapse-item>
          <el-collapse-item title="系统资源分析" name="resource">
            <pre class="analysis-content">{{ JSON.stringify(diagnosis.dimensional_analyses?.resource, null, 2) }}</pre>
          </el-collapse-item>
          <el-collapse-item title="时序关系分析" name="timing">
            <pre class="analysis-content">{{ JSON.stringify(diagnosis.dimensional_analyses?.timing, null, 2) }}</pre>
          </el-collapse-item>
          <el-collapse-item title="历史案例分析" name="history">
            <pre class="analysis-content">{{ JSON.stringify(diagnosis.dimensional_analyses?.history, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 解决方案 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <strong>💡 解决方案</strong>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="(solution, i) in diagnosis.solutions"
            :key="i"
            :type="getPriorityType(solution.priority)"
            :timestamp="solution.priority"
          >
            <el-card>
              <h4>{{ solution.solution }}</h4>
              <p>预估工作量: {{ solution.estimated_effort }}</p>
              <div v-if="solution.implementation_steps" class="steps-list">
                <strong>实施步骤：</strong>
                <ol>
                  <li v-for="(step, j) in solution.implementation_steps" :key="j">
                    {{ step }}
                  </li>
                </ol>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 预防措施 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <strong>🛡️ 预防措施</strong>
        </template>
        <ul class="prevention-list">
          <li v-for="(measure, i) in diagnosis.prevention_measures" :key="i">
            {{ measure }}
          </li>
        </ul>
      </el-card>

      <!-- 完整报告 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <strong>📝 完整诊断报告</strong>
        </template>
        <div class="markdown-content" v-html="renderedMarkdown"></div>
      </el-card>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="exportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
        <el-button type="primary" @click="testStore.errorDiagnosis.show = false">
          关闭
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()
const isFullscreen = ref(false)

const error = computed(() => testStore.errorDiagnosis.error)
const diagnosis = computed(() => testStore.errorDiagnosis.diagnosis?.final_diagnosis)

const renderedMarkdown = computed(() => {
  // TODO: 使用markdown渲染库（如marked）
  const markdown = testStore.errorDiagnosis.diagnosis?.report_markdown || ''
  return markdown.replace(/\n/g, '<br>')
})

const getSeverityTagType = (severity: string) => {
  const map: Record<string, any> = {
    info: 'info',
    warning: 'warning',
    critical: 'danger'
  }
  return map[severity] || 'info'
}

const getPriorityType = (priority: string) => {
  const map: Record<string, any> = {
    critical: 'danger',
    high: 'warning',
    medium: 'primary',
    low: 'info'
  }
  return map[priority] || 'primary'
}

const exportReport = () => {
  const report = JSON.stringify(testStore.errorDiagnosis.diagnosis, null, 2)
  const blob = new Blob([report], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `error-diagnosis-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('诊断报告已导出')
}
</script>

<style scoped>
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.diagnosis-container {
  max-height: 70vh;
  overflow-y: auto;
}

.section-card {
  margin-bottom: 16px;
}

.evidence-list, .prevention-list, .steps-list {
  margin-top: 12px;
}

.evidence-list h4 {
  margin: 0 0 8px 0;
}

.evidence-list ul, .prevention-list, .steps-list ol {
  margin: 0;
  padding-left: 24px;
}

.evidence-list li, .prevention-list li, .steps-list li {
  margin-bottom: 4px;
  line-height: 1.6;
}

.analysis-content {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}

.markdown-content {
  line-height: 1.8;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
