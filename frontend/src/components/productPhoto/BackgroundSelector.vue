<template>
  <!-- 背景选择器组件 -->
  <div class="background-selector">
    <div class="selector-header">
      <h3 class="selector-title">背景设置</h3>
      <span class="selector-hint">选择或自定义背景场景</span>
    </div>

    <!-- 背景类型选择 -->
    <div class="type-tabs">
      <button
        v-for="tab in typeTabs"
        :key="tab.value"
        class="type-tab"
        :class="{ active: selectedType === tab.value }"
        @click="selectType(tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 预设背景 -->
    <div v-if="selectedType === 'preset'" class="preset-grid">
      <div
        v-for="preset in presets"
        :key="preset.value"
        class="preset-item"
        :class="{ selected: selectedPreset === preset.value }"
        @click="selectPreset(preset.value)"
      >
        <div class="preset-icon">{{ preset.icon }}</div>
        <span class="preset-label">{{ preset.label }}</span>
      </div>
    </div>

    <!-- 自定义背景上传 -->
    <div v-if="selectedType === 'custom'" class="custom-upload">
      <div
        v-if="customPreviewUrl"
        class="custom-preview"
      >
        <img :src="customPreviewUrl" alt="自定义背景预览" />
        <div class="preview-overlay">
          <button class="overlay-btn" @click="clearCustomImage" title="移除">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
          <label class="overlay-btn primary">
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              @change="handleCustomImageSelect"
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
      <label
        v-else
        class="upload-zone"
        :class="{ 'drag-over': isDragOver }"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @drop.prevent="handleDrop"
      >
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp"
          @change="handleCustomImageSelect"
          style="display: none;"
        />
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
        <span>点击或拖拽上传背景图</span>
      </label>
    </div>

    <!-- 背景描述输入 -->
    <div v-if="selectedType === 'description'" class="description-input">
      <textarea
        v-model="descriptionText"
        placeholder="描述你想要的背景场景，例如：阳光明媚的海边沙滩、现代简约的白色摄影棚..."
        rows="3"
        @input="handleDescriptionChange"
      ></textarea>
      <div class="description-hint">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        AI 将根据描述生成合适的背景
      </div>
    </div>

    <!-- 保持原背景提示 -->
    <div v-if="selectedType === 'original'" class="original-hint">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
        <path d="M9 12l2 2 4-4"></path>
      </svg>
      <span>将保留模特图的原始背景</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import type { BackgroundConfig } from '../../api/productPhoto'

/**
 * 背景选择器组件
 * 
 * 功能：
 * - 预设背景选择（街拍、室内、商场、户外、纯色）
 * - 自定义背景上传
 * - 背景描述输入
 * - 保持原背景
 * 
 * Requirements: 8.1, 8.2, 8.3, 8.4
 */

// Props
const props = withDefaults(defineProps<{
  modelValue?: BackgroundConfig
  disabled?: boolean
}>(), {
  disabled: false
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: BackgroundConfig | undefined): void
}>()

// 类型选项
const typeTabs = [
  { value: 'preset', label: '预设背景' },
  { value: 'custom', label: '自定义' },
  { value: 'description', label: '描述生成' },
  { value: 'original', label: '保持原背景' }
] as const

type BackgroundType = typeof typeTabs[number]['value']

// 预设背景选项
const presets = [
  { value: '街拍', label: '街拍', icon: '🏙️' },
  { value: '室内', label: '室内', icon: '🏠' },
  { value: '商场', label: '商场', icon: '🛍️' },
  { value: '户外', label: '户外', icon: '🌳' },
  { value: '纯色', label: '纯色', icon: '⬜' }
]

// 状态
const selectedType = ref<BackgroundType>('original')
const selectedPreset = ref<string | null>(null)
const customImageFile = ref<File | null>(null)
const customPreviewUrl = ref<string | null>(null)
const descriptionText = ref('')
const isDragOver = ref(false)

// 初始化状态
function initFromModelValue() {
  if (props.modelValue) {
    selectedType.value = props.modelValue.type as BackgroundType
    if (props.modelValue.type === 'preset' && props.modelValue.preset) {
      selectedPreset.value = props.modelValue.preset
    }
    if (props.modelValue.type === 'description' && props.modelValue.description) {
      descriptionText.value = props.modelValue.description
    }
  }
}

// 监听 modelValue 变化
watch(() => props.modelValue, initFromModelValue, { immediate: true })

// 选择类型
function selectType(type: BackgroundType) {
  if (props.disabled) return
  selectedType.value = type
  emitValue()
}

// 选择预设
function selectPreset(preset: string) {
  if (props.disabled) return
  selectedPreset.value = preset
  emitValue()
}

// 处理自定义图片选择
function handleCustomImageSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    processCustomImage(target.files[0])
  }
  target.value = ''
}

// 处理拖放
function handleDrop(e: DragEvent) {
  isDragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    processCustomImage(files[0])
  }
}

// 处理自定义图片
async function processCustomImage(file: File) {
  if (props.disabled) return
  
  // 验证格式
  const validTypes = ['image/png', 'image/jpeg', 'image/webp']
  if (!validTypes.includes(file.type)) {
    return
  }
  
  // 清除之前的预览
  if (customPreviewUrl.value) {
    URL.revokeObjectURL(customPreviewUrl.value)
  }
  
  customImageFile.value = file
  customPreviewUrl.value = URL.createObjectURL(file)
  emitValue()
}

// 清除自定义图片
function clearCustomImage() {
  if (customPreviewUrl.value) {
    URL.revokeObjectURL(customPreviewUrl.value)
  }
  customImageFile.value = null
  customPreviewUrl.value = null
  emitValue()
}

// 处理描述变化
function handleDescriptionChange() {
  emitValue()
}

// 发送值更新
async function emitValue() {
  let config: BackgroundConfig | undefined

  switch (selectedType.value) {
    case 'preset':
      if (selectedPreset.value) {
        config = {
          type: 'preset',
          preset: selectedPreset.value
        }
      }
      break
    case 'custom':
      if (customImageFile.value) {
        // 转换为 base64
        const base64 = await fileToBase64(customImageFile.value)
        config = {
          type: 'custom',
          customImage: base64
        }
      }
      break
    case 'description':
      if (descriptionText.value.trim()) {
        config = {
          type: 'description',
          description: descriptionText.value.trim()
        }
      }
      break
    case 'original':
      config = {
        type: 'original'
      }
      break
  }

  emit('update:modelValue', config)
}

// 文件转 base64
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// 清理
onUnmounted(() => {
  if (customPreviewUrl.value) {
    URL.revokeObjectURL(customPreviewUrl.value)
  }
})

// 暴露方法
defineExpose({
  clearCustomImage
})
</script>

<style scoped>
.background-selector {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.selector-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.selector-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main, #333);
  margin: 0;
}

.selector-hint {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

/* 类型选项卡 */
.type-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.type-tab {
  padding: 8px 16px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  background: var(--bg-card, #fff);
  color: var(--text-sub, #666);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-tab:hover {
  border-color: var(--border-hover, #e0e0e0);
  background: #fafafa;
}

.type-tab.active {
  border-color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
  color: var(--primary, #ff2442);
}

/* 预设背景网格 */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
}

.preset-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  border: 2px solid var(--border-color, #eee);
  border-radius: var(--radius-md, 12px);
  background: var(--bg-card, #fff);
  cursor: pointer;
  transition: all 0.2s;
}

.preset-item:hover {
  border-color: var(--border-hover, #e0e0e0);
  transform: translateY(-2px);
}

.preset-item.selected {
  border-color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.preset-icon {
  font-size: 24px;
}

.preset-label {
  font-size: 12px;
  color: var(--text-sub, #666);
}

.preset-item.selected .preset-label {
  color: var(--primary, #ff2442);
}

/* 自定义上传 */
.custom-upload {
  width: 100%;
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  border: 2px dashed var(--border-color, #eee);
  border-radius: var(--radius-md, 12px);
  background: var(--bg-card, #fff);
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-placeholder, #ccc);
}

.upload-zone:hover {
  border-color: var(--primary, #ff2442);
  color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.upload-zone.drag-over {
  border-color: var(--primary, #ff2442);
  background: var(--primary-light, #fff0f2);
}

.upload-zone span {
  font-size: 13px;
}

.custom-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
}

.custom-preview img {
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

.custom-preview:hover .preview-overlay {
  opacity: 1;
}

.overlay-btn {
  width: 44px;
  height: 44px;
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

/* 描述输入 */
.description-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.description-input textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
}

.description-input textarea:focus {
  outline: none;
  border-color: var(--primary, #ff2442);
}

.description-input textarea::placeholder {
  color: var(--text-placeholder, #ccc);
}

.description-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #999);
}

/* 保持原背景提示 */
.original-hint {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: var(--radius-sm, 8px);
  color: #166534;
}

.original-hint svg {
  flex-shrink: 0;
  color: #22c55e;
}

.original-hint span {
  font-size: 14px;
}
</style>
