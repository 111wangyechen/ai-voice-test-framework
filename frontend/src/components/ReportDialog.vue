<template>
  <el-dialog
    v-model="testStore.testReport.show"
    title="📊 测试报告"
    width="1000px"
    :fullscreen="isFullscreen"
  >
    <template #header>
      <div class="dialog-header">
        <span>📊 测试报告</span>
        <div>
          <el-button
            :icon="isFullscreen ? 'FullScreen' : 'FullScreenExit'"
            circle
            @click="isFullscreen = !isFullscreen"
          />
        </div>
      </div>
    </template>

    <div v-if="metrics" class="report-container">
      <!-- 总体评分 -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <strong>总体评分</strong>
        </template>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="唤醒率" :value="metrics.wakeup.wakeup_rate_percentage" />
            <el-rate
              :model-value="getRatingStars(metrics.wakeup.rating)"
              disabled
              show-score
              :text-color="getRatingColor(metrics.wakeup.rating)"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic title="识别率" :value="metrics.recognition.recognition_rate_percentage" />
            <el-rate
              :model-value="getRatingStars(metrics.recognition.rating)"
              disabled
              show-score
              :text-color="getRatingColor(metrics.recognition.rating)"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic title="全双工稳定性" :value="metrics.fullduplex.stability_percentage" />
            <el-rate
              :model-value="getRatingStars(metrics.fullduplex.rating)"
              disabled
              show-score
              :text-color="getRatingColor(metrics.fullduplex.rating)"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic title="性能评分" :value="metrics.performance.rating" />
            <el-rate
              :model-value="getRatingStars(metrics.performance.rating)"
              disabled
              show-score
              :text-color="getRatingColor(metrics.performance.rating)"
            />
          </el-col>
        </el-row>
      </el-card>

      <!-- 详细指标 -->
      <el-tabs>
        <el-tab-pane label="唤醒性能" name="wakeup">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="唤醒率">
              {{ metrics.wakeup.wakeup_rate_percentage }}
            </el-descriptions-item>
            <el-descriptions-item label="评级">
              <el-tag :type="getRatingTagType(metrics.wakeup.rating)">
                {{ metrics.wakeup.rating }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="尝试次数">
              {{ metrics.wakeup.total_attempts }}
            </el-descriptions-item>
            <el-descriptions-item label="成功次数">
              {{ metrics.wakeup.successful_count }}
            </el-descriptions-item>
            <el-descriptions-item label="失败次数">
              {{ metrics.wakeup.failed_count }}
            </el-descriptions-item>
            <el-descriptions-item label="平均延迟">
              {{ metrics.wakeup.avg_delay_ms }}ms
            </el-descriptions-item>
            <el-descriptions-item label="摘要" :span="2">
              {{ metrics.wakeup.summary }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="metrics.wakeup.failure_reasons?.length" class="failure-reasons">
            <h4>失败原因分析：</h4>
            <ul>
              <li v-for="(reason, i) in metrics.wakeup.failure_reasons" :key="i">
                {{ reason }}
              </li>
            </ul>
          </div>
        </el-tab-pane>

        <el-tab-pane label="识别准确性" name="recognition">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="识别率">
              {{ metrics.recognition.recognition_rate_percentage }}
            </el-descriptions-item>
            <el-descriptions-item label="评级">
              <el-tag :type="getRatingTagType(metrics.recognition.rating)">
                {{ metrics.recognition.rating }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总识别数">
              {{ metrics.recognition.total_recognitions }}
            </el-descriptions-item>
            <el-descriptions-item label="正确数">
              {{ metrics.recognition.correct_count }}
            </el-descriptions-item>
            <el-descriptions-item label="错误数">
              {{ metrics.recognition.error_count }}
            </el-descriptions-item>
            <el-descriptions-item label="平均延迟">
              {{ metrics.recognition.avg_delay_ms }}ms
            </el-descriptions-item>
            <el-descriptions-item label="摘要" :span="2">
              {{ metrics.recognition.summary }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="metrics.recognition.common_errors?.length" class="common-errors">
            <h4>常见识别错误：</h4>
            <el-table :data="metrics.recognition.common_errors" size="small">
              <el-table-column prop="expected" label="预期" />
              <el-table-column prop="actual" label="实际" />
              <el-table-column prop="frequency" label="频次" width="80" />
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="全双工稳定性" name="fullduplex">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="稳定性">
              {{ metrics.fullduplex.stability_percentage }}
            </el-descriptions-item>
            <el-descriptions-item label="评级">
              <el-tag :type="getRatingTagType(metrics.fullduplex.rating)">
                {{ metrics.fullduplex.rating }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总退出次数">
              {{ metrics.fullduplex.total_exits }}
            </el-descriptions-item>
            <el-descriptions-item label="非预期退出">
              <el-tag type="danger">{{ metrics.fullduplex.unexpected_exits }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="正常退出">
              {{ metrics.fullduplex.expected_exits }}
            </el-descriptions-item>
            <el-descriptions-item label="摘要" :span="2">
              {{ metrics.fullduplex.summary }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="metrics.fullduplex.recommendations?.length" class="recommendations">
            <h4>改进建议：</h4>
            <ul>
              <li v-for="(rec, i) in metrics.fullduplex.recommendations" :key="i">
                {{ rec }}
              </li>
            </ul>
          </div>
        </el-tab-pane>

        <el-tab-pane label="性能分析" name="performance">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="CPU平均使用率">
              {{ metrics.performance.cpu_stats.average.toFixed(1) }}%
            </el-descriptions-item>
            <el-descriptions-item label="CPU峰值">
              {{ metrics.performance.cpu_stats.peak.toFixed(1) }}%
            </el-descriptions-item>
            <el-descriptions-item label="内存平均可用">
              {{ metrics.performance.memory_stats.average_available_mb.toFixed(0) }} MB
            </el-descriptions-item>
            <el-descriptions-item label="内存最低可用">
              {{ metrics.performance.memory_stats.min_available_mb.toFixed(0) }} MB
            </el-descriptions-item>
            <el-descriptions-item label="内存泄漏疑似">
              <el-tag :type="metrics.performance.memory_stats.leak_suspected ? 'warning' : 'success'">
                {{ metrics.performance.memory_stats.leak_suspected ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="摘要" :span="2">
              {{ metrics.performance.summary }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="metrics.performance.optimization_suggestions?.length" class="suggestions">
            <h4>优化建议：</h4>
            <ul>
              <li v-for="(sug, i) in metrics.performance.optimization_suggestions" :key="i">
                {{ sug }}
              </li>
            </ul>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- Markdown完整报告 -->
      <el-card shadow="never" class="section-card" style="margin-top: 20px;">
        <template #header>
          <strong>完整报告（Markdown）</strong>
        </template>
        <div class="markdown-content" v-html="renderedMarkdown"></div>
      </el-card>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="exportMarkdown">
          <el-icon><Download /></el-icon>
          导出Markdown
        </el-button>
        <el-button @click="exportPDF">
          <el-icon><Document /></el-icon>
          导出PDF
        </el-button>
        <el-button type="primary" @click="testStore.testReport.show = false">
          关闭
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document } from '@element-plus/icons-vue'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()
const isFullscreen = ref(false)

const metrics = computed(() => testStore.testReport.metrics)

const renderedMarkdown = computed(() => {
  // TODO: 使用markdown渲染库
  const markdown = testStore.testReport.markdown || ''
  return markdown.replace(/\n/g, '<br>')
})

const getRatingStars = (rating: string) => {
  const map: Record<string, number> = {
    excellent: 5,
    good: 4,
    fair: 3,
    poor: 2
  }
  return map[rating] || 3
}

const getRatingColor = (rating: string) => {
  const map: Record<string, string> = {
    excellent: '#67C23A',
    good: '#409EFF',
    fair: '#E6A23C',
    poor: '#F56C6C'
  }
  return map[rating] || '#909399'
}

const getRatingTagType = (rating: string) => {
  const map: Record<string, any> = {
    excellent: 'success',
    good: 'primary',
    fair: 'warning',
    poor: 'danger'
  }
  return map[rating] || 'info'
}

const exportMarkdown = () => {
  const markdown = testStore.testReport.markdown || ''
  const blob = new Blob([markdown], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `test-report-${Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出为Markdown')
}

const exportPDF = () => {
  // TODO: 实现PDF导出
  ElMessage.info('PDF导出功能开发中...')
}
</script>

<style scoped>
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-container {
  max-height: 70vh;
  overflow-y: auto;
}

.section-card {
  margin-bottom: 16px;
}

.failure-reasons, .common-errors, .recommendations, .suggestions {
  margin-top: 16px;
}

.failure-reasons h4, .recommendations h4, .suggestions h4 {
  margin: 0 0 8px 0;
}

.failure-reasons ul, .recommendations ul, .suggestions ul {
  margin: 0;
  padding-left: 24px;
}

.failure-reasons li, .recommendations li, .suggestions li {
  margin-bottom: 4px;
  line-height: 1.6;
}

.markdown-content {
  line-height: 1.8;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
