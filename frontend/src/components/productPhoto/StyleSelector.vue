<template>
  <!-- 风格选择器组件 -->
  <div class="style-selector">
    <div class="selector-header">
      <h3 class="selector-title">风格设置</h3>
      <span class="selector-hint">选择图片整体风格</span>
    </div>

    <!-- 风格选项 -->
    <div class="style-grid">
      <div
        v-for="style in styles"
        :key="style.value"
        class="style-item"
        :class="{ selected: selectedStyle === style.value }"
        @click="selectStyle(style.value)"
      >
        <div class="style-preview" :style="{ background: style.gradient }">
          <span class="style-icon">{{ style.icon }}</span>
        </div>
        <div class="style-info">
          <span class="style-label">{{ style.label }}</span>
          <span class="style-desc">{{ style.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

/**
 * 风格选择器组件
 * 
 * 功能：
 * - 风格预设选择（简约、时尚、复古、街头、高端）
 * 
 * Requirements: 2.3
 */

// Props
const props = withDefaults(defineProps<{
  modelValue?: string
  disabled?: boolean
}>(), {
  modelValue: '自然',
  disabled: false
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

// 风格选项
const styles = [
  { 
    value: '自然', 
    label: '自然', 
    icon: '🌿',
    description: '真实自然的效果',
    gradient: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)'
  },
  { 
    value: '简约', 
    label: '简约', 
    icon: '⬜',
    description: '干净简洁的风格',
    gradient: 'linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%)'
  },
  { 
    value: '时尚', 
    label: '时尚', 
    icon: '✨',
    description: '潮流时尚感',
    gradient: 'linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%)'
  },
  { 
    value: '复古', 
    label: '复古', 
    icon: '📷',
    description: '怀旧复古风',
    gradient: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)'
  },
  { 
    value: '街头', 
    label: '街头', 
    icon: '🏙️',
    description: '街头潮流风',
    gradient: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)'
  },
  { 
    value: '高端', 
    label: '高端', 
    icon: '💎',
    description: '奢华高端感',
    gradient: 'linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%)'
  }
]

// 状态
const selectedStyle = ref(props.modelValue)

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  selectedStyle.value = newVal
}, { immediate: true })

// 选择风格
function selectStyle(style: string) {
  if (props.disabled) return
  selectedStyle.value = style
  emit('update:modelValue', style)
}

// 暴露方法
defineExpose({
  reset: () => {
    selectedStyle.value = '自然'
    emit('update:modelValue', '自然')
  }
})
</script>

<style scoped>
.style-selector {
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

/* 风格网格 */
.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.style-item {
  display: flex;
  flex-direction: column;
  border: 2px solid var(--border-color, #eee);
  border-radius: var(--radius-md, 12px);
  background: var(--bg-card, #fff);
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
}

.style-item:hover {
  border-color: var(--border-hover, #e0e0e0);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm, 0 2px 8px rgba(0, 0, 0, 0.04));
}

.style-item.selected {
  border-color: var(--primary, #ff2442);
}

.style-preview {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.style-icon {
  font-size: 24px;
}

.style-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  background: var(--bg-card, #fff);
}

.style-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-main, #333);
}

.style-item.selected .style-label {
  color: var(--primary, #ff2442);
}

.style-desc {
  font-size: 11px;
  color: var(--text-secondary, #999);
}
</style>
