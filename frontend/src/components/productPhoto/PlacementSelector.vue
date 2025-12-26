<template>
  <!-- 商品位置选择器组件 -->
  <div class="placement-selector">
    <div class="selector-header">
      <h3 class="selector-title">商品位置</h3>
      <span class="selector-hint">选择商品在模特身上的位置</span>
    </div>

    <!-- 位置选项 -->
    <div class="position-grid">
      <div
        v-for="position in positions"
        :key="position.value"
        class="position-item"
        :class="{ selected: selectedPosition === position.value }"
        @click="selectPosition(position.value)"
      >
        <div class="position-icon">{{ position.icon }}</div>
        <span class="position-label">{{ position.label }}</span>
      </div>
    </div>

    <!-- 自定义指令输入 -->
    <div class="custom-instruction">
      <div class="instruction-header">
        <span class="instruction-label">自定义位置指令</span>
        <span class="instruction-optional">（可选）</span>
      </div>
      <textarea
        v-model="customInstruction"
        placeholder="补充说明商品位置，例如：斜挎在左肩、放在膝盖上、双手捧着..."
        rows="2"
        @input="handleInstructionChange"
      ></textarea>
      <div class="instruction-hint">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        自定义指令会与选择的位置一起使用
      </div>
    </div>

    <!-- 自动位置说明 -->
    <div v-if="selectedPosition === 'auto'" class="auto-hint">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 16v-4"></path>
        <path d="M12 8h.01"></path>
      </svg>
      <span>AI 将根据商品类型自动选择最合适的位置</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { PlacementConfig } from '../../api/productPhoto'

/**
 * 商品位置选择器组件
 * 
 * 功能：
 * - 位置预设选择（左手、右手、肩上、胸前、腰间、自动）
 * - 自定义位置指令输入
 * 
 * Requirements: 9.1, 9.2, 9.3, 9.4
 */

// Props
const props = withDefaults(defineProps<{
  modelValue?: PlacementConfig
  disabled?: boolean
}>(), {
  disabled: false
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: PlacementConfig): void
}>()

// 位置选项
const positions = [
  { value: 'auto', label: '自动', icon: '🤖' },
  { value: 'left_hand', label: '左手', icon: '🤚' },
  { value: 'right_hand', label: '右手', icon: '✋' },
  { value: 'shoulder', label: '肩上', icon: '💪' },
  { value: 'chest', label: '胸前', icon: '👕' },
  { value: 'waist', label: '腰间', icon: '👖' }
] as const

type PositionValue = typeof positions[number]['value']

// 状态
const selectedPosition = ref<PositionValue>('auto')
const customInstruction = ref('')

// 初始化状态
function initFromModelValue() {
  if (props.modelValue) {
    selectedPosition.value = props.modelValue.position as PositionValue
    customInstruction.value = props.modelValue.customInstruction || ''
  } else {
    selectedPosition.value = 'auto'
    customInstruction.value = ''
  }
}

// 监听 modelValue 变化
watch(() => props.modelValue, initFromModelValue, { immediate: true })

// 选择位置
function selectPosition(position: PositionValue) {
  if (props.disabled) return
  selectedPosition.value = position
  emitValue()
}

// 处理自定义指令变化
function handleInstructionChange() {
  emitValue()
}

// 发送值更新
function emitValue() {
  const config: PlacementConfig = {
    position: selectedPosition.value
  }
  
  if (customInstruction.value.trim()) {
    config.customInstruction = customInstruction.value.trim()
  }
  
  emit('update:modelValue', config)
}

// 暴露方法
defineExpose({
  reset: () => {
    selectedPosition.value = 'auto'
    customInstruction.value = ''
    emitValue()
  }
})
</script>

<style scoped>
.placement-selector {
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

/* 位置网格 */
.position-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 10px;
}

.position-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 10px;
  border: 2px solid var(--border-color, #eee);
  border-radius: var(--radius-md, 12px);
  background: var(--bg-card, #fff);
  cursor: pointer;
  transition: all 0.2s;
}

.position-item:hover {
  border-color: var(--border-hover, #e0e0e0);
  transform: translateY(-2px);
}

.position-item.selected {
  border-color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.position-icon {
  font-size: 24px;
}

.position-label {
  font-size: 12px;
  color: var(--text-sub, #666);
}

.position-item.selected .position-label {
  color: var(--primary, #ff2442);
  font-weight: 500;
}

/* 自定义指令 */
.custom-instruction {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.instruction-header {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.instruction-label {
  font-size: 13px;
  color: var(--text-sub, #666);
}

.instruction-optional {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

.custom-instruction textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
}

.custom-instruction textarea:focus {
  outline: none;
  border-color: var(--primary, #ff2442);
}

.custom-instruction textarea::placeholder {
  color: var(--text-placeholder, #ccc);
}

.instruction-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #999);
}

/* 自动位置说明 */
.auto-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: var(--radius-sm, 8px);
  color: #1e40af;
}

.auto-hint svg {
  flex-shrink: 0;
  color: #3b82f6;
}

.auto-hint span {
  font-size: 13px;
}
</style>
