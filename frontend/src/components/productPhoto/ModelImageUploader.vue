<template>
  <!-- 模特图上传组件 -->
  <div class="model-uploader">
    <div class="uploader-header">
      <h3 class="uploader-title">模特图</h3>
      <span class="uploader-hint">支持 PNG、JPG、WEBP 格式</span>
    </div>

    <!-- 已上传图片预览 -->
    <div v-if="previewUrl" class="preview-container">
      <img :src="previewUrl" alt="模特图预览" class="preview-image" />
      <div class="preview-overlay">
        <button class="overlay-btn" @click="clearImage" title="移除图片">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
        <label class="overlay-btn primary">
          <input
            type="file"
            :accept="acceptedFormats"
            @change="handleFileSelect"
            style="display: none;"
          />
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </label>
      </div>
    </div>

    <!-- 上传区域 -->
    <div
      v-else
      class="upload-zone"
      :class="{ 'drag-over': isDragOver, 'has-error': error }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        :accept="acceptedFormats"
        @change="handleFileSelect"
        style="display: none;"
      />
      
      <div class="upload-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
      </div>
      <div class="upload-text">
        <span class="upload-main">拖拽图片到这里，或点击上传</span>
        <span class="upload-sub">支持 PNG、JPG、WEBP 格式</span>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      {{ error }}
    </div>

    <!-- 模板选择 -->
    <div v-if="showTemplates && templates.length > 0" class="template-section">
      <div class="template-header">
        <span class="template-title">或从模板选择</span>
        <button class="template-toggle" @click="isTemplateExpanded = !isTemplateExpanded">
          {{ isTemplateExpanded ? '收起' : '展开' }}
          <svg 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            stroke-width="2"
            :class="{ 'rotated': isTemplateExpanded }"
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
      </div>
      
      <div v-if="isTemplateExpanded" class="template-grid">
        <div
          v-for="template in templates"
          :key="template.id"
          class="template-item"
          :class="{ 'selected': selectedTemplateId === template.id }"
          @click="selectTemplate(template)"
        >
          <img :src="template.thumbnail_url" :alt="template.name" />
          <div class="template-name">{{ template.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTemplateStore } from '../../stores/template'
import type { Template } from '../../api/template'

/**
 * 模特图上传组件
 * 
 * 功能：
 * - 拖拽上传
 * - 点击选择文件
 * - 从已保存模板加载
 * - 图片预览和验证
 * 
 * Requirements: 1.1, 10.3
 */

// Props
const props = withDefaults(defineProps<{
  modelValue: File | null
  previewUrl: string | null
  showTemplates?: boolean
}>(), {
  showTemplates: true
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: File | null): void
  (e: 'update:previewUrl', value: string | null): void
  (e: 'templateSelected', template: Template): void
  (e: 'error', message: string): void
}>()

// 支持的图片格式
const ACCEPTED_FORMATS = ['image/png', 'image/jpeg', 'image/webp']
const acceptedFormats = ACCEPTED_FORMATS.join(',')

// 状态
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const error = ref<string | null>(null)
const isTemplateExpanded = ref(false)
const selectedTemplateId = ref<string | null>(null)
const localPreviewUrl = ref<string | null>(null)

// 模板 store
const templateStore = useTemplateStore()

// 计算属性
const templates = computed(() => templateStore.sortedTemplates)
const previewUrl = computed(() => props.previewUrl || localPreviewUrl.value)

// 方法
function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleDragOver() {
  isDragOver.value = true
}

function handleDragLeave() {
  isDragOver.value = false
}

function handleDrop(e: DragEvent) {
  isDragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    processFile(target.files[0])
  }
  // 清空 input 以允许重复选择同一文件
  target.value = ''
}

function processFile(file: File) {
  error.value = null
  
  // 验证文件格式
  if (!ACCEPTED_FORMATS.includes(file.type)) {
    error.value = '不支持的图片格式，请上传 PNG、JPG 或 WEBP 格式的图片'
    emit('error', error.value)
    return
  }
  
  // 验证文件大小（最大 10MB）
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    error.value = '图片文件过大，请上传小于 10MB 的图片'
    emit('error', error.value)
    return
  }
  
  // 清除之前的预览
  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value)
  }
  
  // 创建预览
  localPreviewUrl.value = URL.createObjectURL(file)
  selectedTemplateId.value = null
  
  emit('update:modelValue', file)
  emit('update:previewUrl', localPreviewUrl.value)
}

function clearImage() {
  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value)
    localPreviewUrl.value = null
  }
  selectedTemplateId.value = null
  error.value = null
  
  emit('update:modelValue', null)
  emit('update:previewUrl', null)
}

async function selectTemplate(template: Template) {
  error.value = null
  selectedTemplateId.value = template.id
  
  // 清除之前的本地预览
  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value)
    localPreviewUrl.value = null
  }
  
  // 使用模板的图片 URL
  emit('update:previewUrl', templateStore.getImageUrl(template.id))
  emit('templateSelected', template)
}

// 生命周期
onMounted(async () => {
  if (props.showTemplates && !templateStore.loaded) {
    await templateStore.loadTemplates()
  }
})

onUnmounted(() => {
  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value)
  }
})

// 暴露方法
defineExpose({
  clearImage,
  triggerFileInput
})
</script>

<style scoped>
.model-uploader {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.uploader-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.uploader-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main, #333);
  margin: 0;
}

.uploader-hint {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

/* 上传区域 */
.upload-zone {
  aspect-ratio: 3/4;
  max-height: 400px;
  border: 2px dashed var(--border-color, #eee);
  border-radius: var(--radius-lg, 16px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-card, #fff);
}

.upload-zone:hover {
  border-color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.upload-zone.drag-over {
  border-color: var(--primary, #ff2442);
  background: var(--primary-light, #fff0f2);
  transform: scale(1.02);
}

.upload-zone.has-error {
  border-color: #ff4d4f;
}

.upload-icon {
  color: var(--text-placeholder, #ccc);
  transition: color 0.2s;
}

.upload-zone:hover .upload-icon {
  color: var(--primary, #ff2442);
}

.upload-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.upload-main {
  font-size: 14px;
  color: var(--text-sub, #666);
}

.upload-sub {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

/* 预览容器 */
.preview-container {
  position: relative;
  aspect-ratio: 3/4;
  max-height: 400px;
  border-radius: var(--radius-lg, 16px);
  overflow: hidden;
  background: #f5f5f5;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.preview-container:hover .preview-overlay {
  opacity: 1;
}

.overlay-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.overlay-btn:hover {
  background: white;
  color: var(--text-main, #333);
  transform: scale(1.1);
}

.overlay-btn.primary {
  background: var(--primary, #ff2442);
  border-color: var(--primary, #ff2442);
}

.overlay-btn.primary:hover {
  background: var(--primary-hover, #ff4d6a);
  color: white;
}

/* 错误提示 */
.error-message {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: var(--radius-sm, 8px);
  color: #ff4d4f;
  font-size: 13px;
}

/* 模板选择 */
.template-section {
  margin-top: 8px;
}

.template-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.template-title {
  font-size: 13px;
  color: var(--text-sub, #666);
}

.template-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--primary, #ff2442);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm, 8px);
  transition: background 0.2s;
}

.template-toggle:hover {
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.template-toggle svg {
  transition: transform 0.2s;
}

.template-toggle svg.rotated {
  transform: rotate(180deg);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
}

.template-item {
  cursor: pointer;
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: var(--border-hover, #e0e0e0);
  transform: translateY(-2px);
}

.template-item.selected {
  border-color: var(--primary, #ff2442);
}

.template-item img {
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
}

.template-name {
  padding: 6px 8px;
  font-size: 11px;
  color: var(--text-sub, #666);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
  background: #fafafa;
}
</style>
