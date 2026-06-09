<template>
  <el-dialog
    v-model="testStore.pendingApproval.show"
    title="⚠️ 需要人工审核"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <el-alert
      type="warning"
      :closable="false"
      show-icon
    >
      <template #title>
        <strong>{{ testStore.pendingApproval.type }}</strong>
      </template>
    </el-alert>

    <div class="approval-content">
      <p>{{ testStore.pendingApproval.message }}</p>

      <div v-if="testStore.pendingApproval.options" class="options-section">
        <el-radio-group v-model="selectedOption">
          <el-radio
            v-for="option in testStore.pendingApproval.options"
            :key="option"
            :value="option"
            border
          >
            {{ option }}
          </el-radio>
        </el-radio-group>
      </div>

      <el-input
        v-model="comments"
        type="textarea"
        :rows="3"
        placeholder="可选：添加审核意见..."
        style="margin-top: 16px;"
      />
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleReject">
          <el-icon><Close /></el-icon>
          拒绝
        </el-button>
        <el-button type="primary" @click="handleApprove">
          <el-icon><Check /></el-icon>
          通过
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Close } from '@element-plus/icons-vue'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()

const selectedOption = ref('')
const comments = ref('')

const handleApprove = () => {
  testStore.approveRequest(true, comments.value)
  ElMessage.success('已通过审核')
  resetDialog()
}

const handleReject = () => {
  testStore.approveRequest(false, comments.value)
  ElMessage.info('已拒绝')
  resetDialog()
}

const resetDialog = () => {
  selectedOption.value = ''
  comments.value = ''
}
</script>

<style scoped>
.approval-content {
  padding: 20px 0;
}

.approval-content p {
  margin-bottom: 16px;
  line-height: 1.6;
  color: #606266;
}

.options-section {
  margin: 16px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
