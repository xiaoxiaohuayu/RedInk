<template>
  <!-- 供应商选择器组件 -->
  <div class="provider-selector">
    <div class="selector-header">
      <h3 class="selector-title">AI 供应商</h3>
      <span class="selector-hint">选择图片生成服务</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载供应商列表...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="providers.length === 0" class="empty-state">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>暂无可用的供应商</span>
      <button class="retry-btn" @click="$emit('refresh')">重新加载</button>
    </div>

    <!-- 供应商列表 -->
    <div v-else class="provider-list">
      <div
        v-for="provider in providers"
        :key="provider.name"
        class="provider-item"
        :class="{ selected: selectedProvider === provider.name }"
        @click="selectProvider(provider.name)"
      >
        <div class="provider-main">
          <div class="provider-info">
            <span class="provider-name">{{ provider.displayName }}</span>
            <span class="provider-id">{{ provider.name }}</span>
          </div>
          <div class="provider-check" v-if="selectedProvider === provider.name">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>
        </div>
        
        <!-- 功能支持标签 -->
        <div class="feature-tags">
          <span 
            class="feature-tag" 
            :class="{ supported: provider.features.backgroundChange }"
            :title="provider.features.backgroundChange ? '支持换背景' : '不支持换背景'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
            换背景
          </span>
          <span 
            class="feature-tag" 
            :class="{ supported: provider.features.poseChange }"
            :title="provider.features.poseChange ? '支持换姿势' : '不支持换姿势'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
            </svg>
            换姿势
          </span>
          <span 
            class="feature-tag" 
            :class="{ supported: provider.features.multiProduct }"
            :title="provider.features.multiProduct ? '支持多商品' : '不支持多商品'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            多商品
          </span>
          <span 
            class="feature-tag" 
            :class="{ supported: provider.features.inpainting }"
            :title="provider.features.inpainting ? '支持局部编辑' : '不支持局部编辑'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 19l7-7 3 3-7 7-3-3z"></path>
              <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path>
              <path d="M2 2l7.586 7.586"></path>
            </svg>
            局部编辑
          </span>
        </div>
      </div>
    </div>

    <!-- 功能说明 -->
    <div class="feature-legend">
      <span class="legend-title">功能说明：</span>
      <div class="legend-items">
        <span class="legend-item supported">
          <span class="legend-dot"></span>
          支持
        </span>
        <span class="legend-item">
          <span class="legend-dot"></span>
          不支持
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ProviderInfo } from '../../api/productPhoto'

/**
 * 供应商选择器组件
 * 
 * 功能：
 * - 显示可用供应商列表
 * - 显示各供应商支持的功能
 * - 选择供应商
 * 
 * Requirements: 5.1
 */

// Props
const props = withDefaults(defineProps<{
  modelValue?: string
  providers: ProviderInfo[]
  loading?: boolean
  disabled?: boolean
}>(), {
  providers: () => [],
  loading: false,
  disabled: false
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'refresh'): void
  (e: 'providerChange', provider: ProviderInfo): void
}>()

// 状态
const selectedProvider = ref<string | null>(props.modelValue || null)

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  selectedProvider.value = newVal || null
}, { immediate: true })

// 监听 providers 变化，自动选择第一个
watch(() => props.providers, (newProviders) => {
  if (newProviders.length > 0 && !selectedProvider.value) {
    selectProvider(newProviders[0].name)
  }
}, { immediate: true })

// 选择供应商
function selectProvider(name: string) {
  if (props.disabled) return
  selectedProvider.value = name
  emit('update:modelValue', name)
  
  const provider = props.providers.find(p => p.name === name)
  if (provider) {
    emit('providerChange', provider)
  }
}

// 获取当前选中的供应商信息
function getCurrentProvider(): ProviderInfo | undefined {
  return props.providers.find(p => p.name === selectedProvider.value)
}

// 暴露方法
defineExpose({
  getCurrentProvider,
  selectedProvider
})
</script>

<style scoped>
.provider-selector {
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

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  color: var(--text-secondary, #999);
  font-size: 14px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color, #eee);
  border-top-color: var(--primary, #ff2442);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px;
  color: var(--text-secondary, #999);
}

.empty-state svg {
  color: var(--text-placeholder, #ccc);
}

.retry-btn {
  padding: 8px 16px;
  border: 1px solid var(--primary, #ff2442);
  border-radius: var(--radius-sm, 8px);
  background: transparent;
  color: var(--primary, #ff2442);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

/* 供应商列表 */
.provider-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.provider-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 2px solid var(--border-color, #eee);
  border-radius: var(--radius-md, 12px);
  background: var(--bg-card, #fff);
  cursor: pointer;
  transition: all 0.2s;
}

.provider-item:hover {
  border-color: var(--border-hover, #e0e0e0);
}

.provider-item.selected {
  border-color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.provider-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.provider-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.provider-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-main, #333);
}

.provider-item.selected .provider-name {
  color: var(--primary, #ff2442);
}

.provider-id {
  font-size: 11px;
  color: var(--text-secondary, #999);
  font-family: monospace;
}

.provider-check {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary, #ff2442);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 功能标签 */
.feature-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.feature-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  background: #f5f5f5;
  color: var(--text-secondary, #999);
  transition: all 0.2s;
}

.feature-tag.supported {
  background: #ecfdf5;
  color: #059669;
}

.feature-tag svg {
  flex-shrink: 0;
}

/* 功能说明 */
.feature-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: var(--radius-sm, 8px);
}

.legend-title {
  font-size: 12px;
  color: var(--text-sub, #666);
}

.legend-items {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #999);
}

.legend-item.supported {
  color: #059669;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e5e5e5;
}

.legend-item.supported .legend-dot {
  background: #10b981;
}
</style>
