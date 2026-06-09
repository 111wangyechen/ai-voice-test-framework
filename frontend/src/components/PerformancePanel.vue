<template>
  <el-card class="perf-panel" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>📊 性能监控</span>
      </div>
    </template>

    <!-- CPU图表 -->
    <div class="chart-section">
      <h4>CPU使用率</h4>
      <div ref="cpuChartRef" class="chart-container"></div>
    </div>

    <!-- 内存图表 -->
    <div class="chart-section">
      <h4>内存使用情况</h4>
      <div ref="memChartRef" class="chart-container"></div>
    </div>

    <!-- 关键进程表格 -->
    <div class="table-section">
      <h4>关键进程资源占用</h4>
      <el-table :data="latestProcesses" size="small" stripe>
        <el-table-column prop="name" label="进程名" width="200" />
        <el-table-column prop="cpu" label="CPU (%)" width="100">
          <template #default="scope">
            <el-tag
              :type="getCpuTagType(scope.row.cpu)"
              size="small"
            >
              {{ scope.row.cpu.toFixed(1) }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mem_mb" label="内存 (MB)" width="100">
          <template #default="scope">
            {{ scope.row.mem_mb.toFixed(0) }} MB
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()

const cpuChartRef = ref<HTMLElement>()
const memChartRef = ref<HTMLElement>()

let cpuChart: echarts.ECharts | null = null
let memChart: echarts.ECharts | null = null

// 最新的进程数据
const latestProcesses = computed(() => {
  const latest = testStore.performanceMetrics[testStore.performanceMetrics.length - 1]
  if (!latest || !latest.processes) return []

  return Object.entries(latest.processes).map(([name, data]) => ({
    name,
    cpu: data.cpu,
    mem_mb: data.mem_mb
  }))
})

const getCpuTagType = (cpu: number) => {
  if (cpu > 300) return 'danger'
  if (cpu > 200) return 'warning'
  return 'success'
}

// 初始化图表
onMounted(() => {
  if (cpuChartRef.value) {
    cpuChart = echarts.init(cpuChartRef.value)
    cpuChart.setOption({
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: []
      },
      yAxis: {
        type: 'value',
        name: 'CPU使用率 (%)',
        max: 400
      },
      series: [{
        name: 'CPU使用率',
        type: 'line',
        smooth: true,
        data: [],
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        }
      }]
    })
  }

  if (memChartRef.value) {
    memChart = echarts.init(memChartRef.value)
    memChart.setOption({
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: []
      },
      yAxis: {
        type: 'value',
        name: '可用内存 (MB)'
      },
      series: [{
        name: '可用内存',
        type: 'line',
        smooth: true,
        data: [],
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.5)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
          ])
        }
      }]
    })
  }

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

// 更新图表数据
watch(() => testStore.performanceMetrics, (metrics) => {
  if (metrics.length === 0) return

  const timestamps = metrics.map(m => new Date(m.timestamp * 1000).toLocaleTimeString())
  const cpuData = metrics.map(m => m.cpu_usage)
  const memData = metrics.map(m => m.mem_available_mb)

  if (cpuChart) {
    cpuChart.setOption({
      xAxis: { data: timestamps },
      series: [{ data: cpuData }]
    })
  }

  if (memChart) {
    memChart.setOption({
      xAxis: { data: timestamps },
      series: [{ data: memData }]
    })
  }
}, { deep: true })

const handleResize = () => {
  cpuChart?.resize()
  memChart?.resize()
}
</script>

<style scoped>
.perf-panel {
  height: 600px;
  overflow-y: auto;
}

.card-header {
  font-weight: 600;
}

.chart-section {
  margin-bottom: 24px;
}

.chart-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
}

.chart-container {
  width: 100%;
  height: 200px;
}

.table-section {
  margin-top: 24px;
}

.table-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
}
</style>
