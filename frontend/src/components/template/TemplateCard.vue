<template>
  <div class="template-card" :class="{ selected: isSelected }">
    <!-- 缩略图 -->
    <div class="template-thumbnail" @click="handleSelect">
      <img
        :src="thumbnailUrl"
        :alt="template.name"
        @error="handleImageError"
      />
      <div class="template-overlay">
        <button class="overlay-btn" @click.stop="handleSelect" title="选择">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </button>
      </div>
      <!-- 选中标记 -->
      <div v-if="isSelected" class="selected-badge">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      </div>
    </div>

    <!-- 信息区域 -->
    <div class="template-info">
      <div class="template-name-row">
        <span v-if="!isEditing" class="template-name" :title="template.name">
          {{ template.name }}
        </span>
        <input
          v-else
          ref="nameInputRef"
          v-model="editName"
          class="name-input"
          @blur="handleSaveName"
          @keyup.enter="handleSaveName"
          @keyup.escape="handleCancelEdit"
        />
      </div>
      <span class="template-date">{{ formattedDate }}</span>
    </div>

    <!-- 操作按钮 -->
    <div class="template-actions">
      <button class="action-btn" @click="handleRename" title="重命名">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        </svg>
      </button>
      <button class="action-btn danger" @click="handleDelete" title="删除">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 模特模板卡片组件
 *
 * 功能：
 * - 显示模板缩略图
 * - 显示模板名称和创建时间
 * - 支持选择、重命名、删除操作
 *
 * Requirements: 10.2
 */

import { ref, computed, nextTick } from 'vue'
import type { Template } from '../../api/template'
import { getTemplateThumbnailUrl } from '../../api/template'

// Props
const props = defineProps<{
  template: Template
  isSelected?: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'select', template: Template): void
  (e: 'rename', templateId: string, newName: string): void
  (e: 'delete', templateId: string): void
}>()

// 状态
const isEditing = ref(false)
const editName = ref('')
const nameInputRef = ref<HTMLInputElement | null>(null)

// 计算属性
const thumbnailUrl = computed(() => {
  return getTemplateThumbnailUrl(props.template.id)
})

const formattedDate = computed(() => {
  const date = new Date(props.template.created_at)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
})

// 方法
function handleSelect() {
  emit('select', props.template)
}

function handleRename() {
  editName.value = props.template.name
  isEditing.value = true
  nextTick(() => {
    nameInputRef.value?.focus()
    nameInputRef.value?.select()
  })
}

function handleSaveName() {
  if (!isEditing.value) return

  const newName = editName.value.trim()
  if (newName && newName !== props.template.name) {
    emit('rename', props.template.id, newName)
  }
  isEditing.value = false
}

function handleCancelEdit() {
  isEditing.value = false
  editName.value = props.template.name
}

function handleDelete() {
  emit('delete', props.template.id)
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"%3E%3Crect fill="%23f0f0f0" width="100" height="100"/%3E%3Ctext fill="%23999" font-size="12" x="50" y="50" text-anchor="middle" dy=".3em"%3E无图片%3C/text%3E%3C/svg%3E'
}
</script>

<style scoped>
.template-card {
  background: var(--bg-card, #fff);
  border-radius: var(--radius-lg, 16px);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s;
  border: 2px solid transparent;
}

.template-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-4px);
}

.template-card.selected {
  border-color: var(--primary, #ff2442);
}

/* 缩略图区域 */
.template-thumbnail {
  position: relative;
  aspect-ratio: 3/4;
  cursor: pointer;
  overflow: hidden;
  background: #f5f5f5;
}

.template-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.template-card:hover .template-thumbnail img {
  transform: scale(1.05);
}

.template-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.template-thumbnail:hover .template-overlay {
  opacity: 1;
}

.overlay-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.8);
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
  color: var(--primary, #ff2442);
  transform: scale(1.1);
}

.selected-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary, #ff2442);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 信息区域 */
.template-info {
  padding: 16px;
  border-bottom: 1px solid var(--border-color, #eee);
}

.template-name-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.template-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main, #333);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.name-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--primary, #ff2442);
  border-radius: 4px;
  font-size: 15px;
  font-weight: 600;
  outline: none;
}

.template-date {
  font-size: 12px;
  color: var(--text-secondary, #999);
}

/* 操作按钮 */
.template-actions {
  display: flex;
  padding: 12px 16px;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  background: var(--bg-card, #fff);
  color: var(--text-sub, #666);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: var(--primary, #ff2442);
  color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.action-btn.danger:hover {
  border-color: #ff4d4f;
  color: #ff4d4f;
  background: #fff1f0;
}
</style>
