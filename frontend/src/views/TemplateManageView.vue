<template>
  <div class="container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">模特模板</h1>
        <p class="page-subtitle">管理已保存的模特图模板，快速复用</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="handleRefresh" :disabled="store.loading">
          <svg v-if="!store.loading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"></path>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
          <div v-else class="spinner-small"></div>
          {{ store.loading ? '加载中...' : '刷新' }}
        </button>
        <label class="btn btn-primary upload-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          添加模板
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            @change="handleFileSelect"
            hidden
          />
        </label>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="toolbar-wrapper">
      <div class="template-stats">
        <span class="stats-item">
          共 <strong>{{ store.templateCount }}</strong> 个模板
        </span>
      </div>
      <div class="search-mini">
        <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索模板名称..."
        />
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="store.error" class="error-msg">
      {{ store.error }}
      <button class="error-close" @click="store.clearError">×</button>
    </div>

    <!-- 加载状态 -->
    <div v-if="store.loading && !store.loaded" class="loading-state">
      <div class="spinner"></div>
      <p>加载模板中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!store.hasTemplates" class="empty-state-large">
      <div class="empty-img">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
      </div>
      <h3>暂无模板</h3>
      <p class="empty-tips">点击上方"添加模板"按钮上传模特图</p>
    </div>

    <!-- 搜索无结果 -->
    <div v-else-if="filteredTemplates.length === 0" class="empty-state-large">
      <div class="empty-img">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </div>
      <h3>未找到匹配的模板</h3>
      <p class="empty-tips">尝试其他搜索关键词</p>
    </div>

    <!-- 模板网格 -->
    <div v-else class="template-grid">
      <TemplateCard
        v-for="template in filteredTemplates"
        :key="template.id"
        :template="template"
        :is-selected="store.selectedTemplateId === template.id"
        @select="handleSelectTemplate"
        @rename="handleRenameTemplate"
        @delete="handleDeleteTemplate"
      />
    </div>

    <!-- 添加模板对话框 -->
    <div v-if="showAddDialog" class="modal-overlay" @click.self="closeAddDialog">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加模板</h3>
          <button class="close-btn" @click="closeAddDialog">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <!-- 图片预览 -->
          <div class="preview-area">
            <img v-if="previewUrl" :src="previewUrl" alt="预览" />
          </div>
          <!-- 模板名称输入 -->
          <div class="form-group">
            <label class="form-label">模板名称</label>
            <input
              v-model="newTemplateName"
              type="text"
              class="form-input"
              placeholder="输入模板名称..."
              @keyup.enter="handleSaveNewTemplate"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeAddDialog">取消</button>
          <button
            class="btn btn-primary"
            :disabled="!newTemplateName.trim() || saving"
            @click="handleSaveNewTemplate"
          >
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteDialog" class="modal-overlay" @click.self="closeDeleteDialog">
      <div class="modal-content modal-sm">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="close-btn" @click="closeDeleteDialog">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>确定要删除模板 "{{ deleteTargetName }}" 吗？此操作不可恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeDeleteDialog">取消</button>
          <button
            class="btn btn-danger"
            :disabled="deleting"
            @click="confirmDelete"
          >
            {{ deleting ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 模特模板管理页面
 *
 * 功能：
 * - 显示模板网格
 * - 保存、重命名、删除模板
 * - 搜索模板
 *
 * Requirements: 10.1, 10.2, 10.4, 10.5
 */

import { ref, computed, onMounted } from 'vue'
import { useTemplateStore } from '../stores/template'
import { TemplateCard } from '../components/template'
import type { Template } from '../api/template'

const store = useTemplateStore()

// 搜索
const searchQuery = ref('')

// 添加模板对话框
const showAddDialog = ref(false)
const newTemplateName = ref('')
const selectedFile = ref<File | null>(null)
const previewUrl = ref<string | null>(null)
const saving = ref(false)

// 删除确认对话框
const showDeleteDialog = ref(false)
const deleteTargetId = ref<string | null>(null)
const deleteTargetName = ref('')
const deleting = ref(false)

// 计算属性
const filteredTemplates = computed(() => {
  if (!searchQuery.value.trim()) {
    return store.sortedTemplates
  }
  return store.searchTemplates(searchQuery.value)
})

// 方法
async function handleRefresh() {
  await store.refreshTemplates()
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 验证文件类型
  const validTypes = ['image/png', 'image/jpeg', 'image/webp']
  if (!validTypes.includes(file.type)) {
    alert('请选择 PNG、JPG 或 WEBP 格式的图片')
    return
  }

  selectedFile.value = file
  newTemplateName.value = file.name.replace(/\.[^/.]+$/, '') // 默认使用文件名

  // 创建预览
  const reader = new FileReader()
  reader.onload = (e) => {
    previewUrl.value = e.target?.result as string
  }
  reader.readAsDataURL(file)

  showAddDialog.value = true

  // 重置 input
  input.value = ''
}

function closeAddDialog() {
  showAddDialog.value = false
  selectedFile.value = null
  previewUrl.value = null
  newTemplateName.value = ''
}

async function handleSaveNewTemplate() {
  if (!selectedFile.value || !newTemplateName.value.trim()) return

  saving.value = true
  try {
    const templateId = await store.saveNewTemplate(
      newTemplateName.value.trim(),
      selectedFile.value
    )
    if (templateId) {
      closeAddDialog()
    }
  } finally {
    saving.value = false
  }
}

function handleSelectTemplate(template: Template) {
  if (store.selectedTemplateId === template.id) {
    store.clearSelection()
  } else {
    store.selectTemplate(template.id)
  }
}

async function handleRenameTemplate(templateId: string, newName: string) {
  await store.updateExistingTemplate(templateId, { name: newName })
}

function handleDeleteTemplate(templateId: string) {
  const template = store.getTemplateById(templateId)
  if (!template) return

  deleteTargetId.value = templateId
  deleteTargetName.value = template.name
  showDeleteDialog.value = true
}

function closeDeleteDialog() {
  showDeleteDialog.value = false
  deleteTargetId.value = null
  deleteTargetName.value = ''
}

async function confirmDelete() {
  if (!deleteTargetId.value) return

  deleting.value = true
  try {
    const success = await store.removeTemplate(deleteTargetId.value)
    if (success) {
      closeDeleteDialog()
    }
  } finally {
    deleting.value = false
  }
}

// 生命周期
onMounted(async () => {
  if (!store.loaded) {
    await store.loadTemplates()
  }
})
</script>

<style scoped>
/* 头部操作 */
.header-actions {
  display: flex;
  gap: 12px;
}

.upload-btn {
  cursor: pointer;
}

/* 工具栏 */
.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.template-stats {
  font-size: 14px;
  color: var(--text-sub, #666);
}

.stats-item strong {
  color: var(--text-main, #333);
  font-weight: 600;
}

.search-mini {
  position: relative;
  width: 240px;
}

.search-mini input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border-radius: 100px;
  border: 1px solid var(--border-color, #eee);
  font-size: 14px;
  background: white;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-mini input:focus {
  border-color: var(--primary, #ff2442);
  outline: none;
  box-shadow: 0 0 0 3px var(--primary-light, rgba(255, 36, 66, 0.1));
}

.search-mini .icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #ccc;
}

/* 错误提示 */
.error-msg {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.error-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #ff4d4f;
  padding: 0 8px;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--text-sub, #666);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color, #eee);
  border-top-color: var(--primary, #ff2442);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

.spinner-small {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-color, #eee);
  border-top-color: var(--primary, #ff2442);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state-large {
  text-align: center;
  padding: 80px 0;
  color: var(--text-sub, #666);
}

.empty-img {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state-large h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main, #333);
  margin-bottom: 8px;
}

.empty-tips {
  font-size: 14px;
  color: var(--text-placeholder, #999);
}

/* 模板网格 */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 24px;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: var(--radius-lg, 16px);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-content.modal-sm {
  max-width: 400px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main, #333);
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-sub, #666);
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f5f5f5;
  color: var(--text-main, #333);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #eee);
}

/* 预览区域 */
.preview-area {
  width: 100%;
  aspect-ratio: 3/4;
  background: #f5f5f5;
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
  margin-bottom: 20px;
}

.preview-area img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 表单 */
.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-main, #333);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary, #ff2442);
}

/* 危险按钮 */
.btn-danger {
  background: #ff4d4f;
  color: white;
  border: none;
}

.btn-danger:hover:not(:disabled) {
  background: #ff7875;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
