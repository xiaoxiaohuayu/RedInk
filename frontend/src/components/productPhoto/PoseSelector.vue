<template>
  <!-- 姿势选择器组件 -->
  <div class="pose-selector">
    <div class="selector-header">
      <h3 class="selector-title">姿势设置</h3>
      <span class="selector-hint">选择模特姿势或自定义描述</span>
    </div>

    <!-- 姿势类型选择 -->
    <div class="type-tabs">
      <button
        class="type-tab"
        :class="{ active: poseType === 'preset' }"
        @click="selectType('preset')"
      >
        预设姿势
      </button>
      <button
        class="type-tab"
        :class="{ active: poseType === 'custom' }"
        @click="selectType('custom')"
      >
        自定义描述
      </button>
      <button
        class="type-tab"
        :class="{ active: poseType === 'original' }"
        @click="selectType('original')"
      >
        保持原姿势
      </button>
    </div>

    <!-- 预设姿势 -->
    <div v-if="poseType === 'preset'" class="preset-grid">
      <div
        v-for="preset in presets"
        :key="preset.value"
        class="preset-item"
        :class="{ selected: selectedPreset === preset.value }"
        @click="selectPreset(preset.value)"
      >
        <div class="preset-icon">{{ preset.icon }}</div>
        <span class="preset-label">{{ preset.label }}</span>
        <span class="preset-desc">{{ preset.description }}</span>
      </div>
    </div>

    <!-- 自定义描述 -->
    <div v-if="poseType === 'custom'" class="custom-input">
      <textarea
        v-model="customDescription"
        placeholder="描述你想要的姿势，例如：双手叉腰、单手托腮、回头微笑..."
        rows="3"
        @input="handleCustomChange"
      ></textarea>
      <div class="input-hint">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        AI 将根据描述调整模特姿势
      </div>
    </div>

    <!-- 保持原姿势提示 -->
    <div v-if="poseType === 'original'" class="original-hint">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
        <path d="M9 12l2 2 4-4"></path>
      </svg>
      <span>将保留模特图的原始姿势</span>
    </div>

    <!-- 功能不支持提示 -->
    <div v-if="!supported" class="unsupported-hint">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>当前供应商不支持姿势调整</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

/**
 * 姿势选择器组件
 * 
 * 功能：
 * - 预设姿势选择（站立、坐姿、行走、侧身、回眸）
 * - 自定义姿势描述
 * - 保持原姿势
 * 
 * Requirements: 11.1, 11.2
 */

// Props
const props = withDefaults(defineProps<{
  modelValue?: string
  supported?: boolean
  disabled?: boolean
}>(), {
  supported: true,
  disabled: false
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: string | undefined): void
}>()

// 预设姿势选项
const presets = [
  { value: '站立', label: '站立', icon: '🧍', description: '自然站立姿势' },
  { value: '坐姿', label: '坐姿', icon: '🪑', description: '优雅坐姿' },
  { value: '行走', label: '行走', icon: '🚶', description: '自然行走状态' },
  { value: '侧身', label: '侧身', icon: '👤', description: '侧面展示' },
  { value: '回眸', label: '回眸', icon: '💫', description: '回头看的姿势' }
]

// 状态
type PoseType = 'preset' | 'custom' | 'original'
const poseType = ref<PoseType>('original')
const selectedPreset = ref<string | null>(null)
const customDescription = ref('')

// 初始化状态
function initFromModelValue() {
  if (!props.modelValue) {
    poseType.value = 'original'
    selectedPreset.value = null
    customDescription.value = ''
    return
  }

  // 检查是否是预设值
  const isPreset = presets.some(p => p.value === props.modelValue)
  if (isPreset) {
    poseType.value = 'preset'
    selectedPreset.value = props.modelValue!
    customDescription.value = ''
  } else {
    poseType.value = 'custom'
    selectedPreset.value = null
    customDescription.value = props.modelValue!
  }
}

// 监听 modelValue 变化
watch(() => props.modelValue, initFromModelValue, { immediate: true })

// 选择类型
function selectType(type: PoseType) {
  if (props.disabled || !props.supported) return
  poseType.value = type
  
  if (type === 'original') {
    emit('update:modelValue', undefined)
  } else if (type === 'preset' && selectedPreset.value) {
    emit('update:modelValue', selectedPreset.value)
  } else if (type === 'custom' && customDescription.value.trim()) {
    emit('update:modelValue', customDescription.value.trim())
  }
}

// 选择预设
function selectPreset(preset: string) {
  if (props.disabled || !props.supported) return
  selectedPreset.value = preset
  emit('update:modelValue', preset)
}

// 处理自定义描述变化
function handleCustomChange() {
  if (props.disabled || !props.supported) return
  const value = customDescription.value.trim()
  emit('update:modelValue', value || undefined)
}

// 暴露方法
defineExpose({
  reset: () => {
    poseType.value = 'original'
    selectedPreset.value = null
    customDescription.value = ''
    emit('update:modelValue', undefined)
  }
})
</script>

<style scoped>
.pose-selector {
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

/* 预设姿势网格 */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

.preset-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
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
  font-size: 28px;
}

.preset-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-main, #333);
}

.preset-item.selected .preset-label {
  color: var(--primary, #ff2442);
}

.preset-desc {
  font-size: 11px;
  color: var(--text-secondary, #999);
  text-align: center;
}

/* 自定义输入 */
.custom-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.custom-input textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
}

.custom-input textarea:focus {
  outline: none;
  border-color: var(--primary, #ff2442);
}

.custom-input textarea::placeholder {
  color: var(--text-placeholder, #ccc);
}

.input-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #999);
}

/* 保持原姿势提示 */
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

/* 不支持提示 */
.unsupported-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-sm, 8px);
  color: #92400e;
  font-size: 13px;
}

.unsupported-hint svg {
  flex-shrink: 0;
  color: #f59e0b;
}
</style>
