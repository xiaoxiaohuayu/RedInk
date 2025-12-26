<template>
  <!-- 商品图上传组件 -->
  <div class="product-uploader">
    <div class="uploader-header">
      <h3 class="uploader-title">商品图</h3>
      <span class="uploader-hint">支持多张图片，可拖拽排序</span>
    </div>

    <!-- 图片列表 -->
    <div class="image-list">
      <!-- 已上传的图片 -->
      <div
        v-for="(image, index) in images"
        :key="image.id"
        class="image-item"
        :class="{ 'dragging': dragIndex === index, 'drag-over': dropIndex === index }"
        draggable="true"
        @dragstart="handleDragStart(index, $event)"
        @dragend="handleDragEnd"
        @dragover.prevent="handleItemDragOver(index)"
        @dragleave="handleItemDragLeave"
        @drop.prevent="handleItemDrop(index)"
      >
        <img :src="image.preview" :alt="`商品图 ${index + 1}`" />
        <div class="image-overlay">
          <span class="image-index">{{ index + 1 }}</span>
          <button class="remove-btn" @click="removeImage(index)" title="移除">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="product-type-badge" v-if="image.productType">
          {{ productTypeLabels[image.productType] || image.productType }}
        </div>
      </div>

      <!-- 添加按钮 -->
      <div
        class="add-button"
        :class="{ 'drag-over': isZoneDragOver }"
        @click="triggerFileInput"
        @dragover.prevent="handleZoneDragOver"
        @dragleave.prevent="handleZoneDragLeave"
        @drop.prevent="handleZoneDrop"
      >
        <input
          ref="fileInputRef"
          type="file"
          :accept="acceptedFormats"
          multiple
          @change="handleFileSelect"
          style="display: none;"
        />
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        <span>添加商品图</span>
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

    <!-- 商品类型提示 -->
    <div class="product-types-hint">
      <span class="hint-label">支持的商品类型：</span>
      <div class="type-tags">
        <span class="type-tag">衣服</span>
        <span class="type-tag">鞋子</span>
        <span class="type-tag">配饰</span>
        <span class="type-tag">包包</span>
        <span class="type-tag">手表</span>
        <span class="type-tag">玩具</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'

/**
 * 商品图上传组件
 * 
 * 功能：
 * - 多图上传
 * - 拖拽排序
 * - 图片预览
 * - 移除图片
 * 
 * Requirements: 1.1, 7.1-7.6
 */

// 商品图类型
interface ProductImage {
  id: string
  file: File
  preview: string
  productType?: string
}

// Props
const props = withDefaults(defineProps<{
  maxImages?: number
}>(), {
  maxImages: 10
})

// Emits
const emit = defineEmits<{
  (e: 'update', files: File[]): void
  (e: 'add', files: File[]): void
  (e: 'remove', index: number): void
  (e: 'reorder', fromIndex: number, toIndex: number): void
  (e: 'error', message: string): void
}>()

// 支持的图片格式
const ACCEPTED_FORMATS = ['image/png', 'image/jpeg', 'image/webp']
const acceptedFormats = ACCEPTED_FORMATS.join(',')

// 商品类型标签
const productTypeLabels: Record<string, string> = {
  clothing: '衣服',
  footwear: '鞋子',
  accessory: '配饰',
  bag: '包包',
  watch: '手表',
  toy: '玩具'
}

// 状态
const fileInputRef = ref<HTMLInputElement | null>(null)
const images = ref<ProductImage[]>([])
const error = ref<string | null>(null)
const isZoneDragOver = ref(false)

// 拖拽排序状态
const dragIndex = ref<number | null>(null)
const dropIndex = ref<number | null>(null)

// 计算属性
const files = computed(() => images.value.map(img => img.file))

// 生成唯一 ID
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// 方法
function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    processFiles(Array.from(target.files))
  }
  // 清空 input 以允许重复选择同一文件
  target.value = ''
}

function handleZoneDragOver() {
  isZoneDragOver.value = true
}

function handleZoneDragLeave() {
  isZoneDragOver.value = false
}

function handleZoneDrop(e: DragEvent) {
  isZoneDragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    processFiles(Array.from(files))
  }
}

function processFiles(fileList: File[]) {
  error.value = null
  
  // 检查数量限制
  const remainingSlots = props.maxImages - images.value.length
  if (remainingSlots <= 0) {
    error.value = `最多只能上传 ${props.maxImages} 张商品图`
    emit('error', error.value)
    return
  }
  
  const filesToAdd = fileList.slice(0, remainingSlots)
  const validFiles: File[] = []
  
  for (const file of filesToAdd) {
    // 验证文件格式
    if (!ACCEPTED_FORMATS.includes(file.type)) {
      error.value = `不支持的图片格式：${file.name}，请上传 PNG、JPG 或 WEBP 格式的图片`
      emit('error', error.value)
      continue
    }
    
    // 验证文件大小（最大 10MB）
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      error.value = `图片文件过大：${file.name}，请上传小于 10MB 的图片`
      emit('error', error.value)
      continue
    }
    
    validFiles.push(file)
  }
  
  if (validFiles.length === 0) return
  
  // 创建预览并添加到列表
  const newImages: ProductImage[] = validFiles.map(file => ({
    id: generateId(),
    file,
    preview: URL.createObjectURL(file)
  }))
  
  images.value.push(...newImages)
  
  emit('add', validFiles)
  emit('update', files.value)
  
  // 提示超出数量
  if (fileList.length > remainingSlots) {
    error.value = `已达到最大数量限制，仅添加了 ${remainingSlots} 张图片`
    emit('error', error.value)
  }
}

function removeImage(index: number) {
  const image = images.value[index]
  if (image) {
    URL.revokeObjectURL(image.preview)
    images.value.splice(index, 1)
    emit('remove', index)
    emit('update', files.value)
  }
  error.value = null
}

function clearAll() {
  images.value.forEach(img => URL.revokeObjectURL(img.preview))
  images.value = []
  error.value = null
  emit('update', [])
}

// 拖拽排序
function handleDragStart(index: number, e: DragEvent) {
  dragIndex.value = index
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', index.toString())
  }
}

function handleDragEnd() {
  dragIndex.value = null
  dropIndex.value = null
}

function handleItemDragOver(index: number) {
  if (dragIndex.value !== null && dragIndex.value !== index) {
    dropIndex.value = index
  }
}

function handleItemDragLeave() {
  dropIndex.value = null
}

function handleItemDrop(toIndex: number) {
  if (dragIndex.value !== null && dragIndex.value !== toIndex) {
    const fromIndex = dragIndex.value
    
    // 重新排序
    const [movedImage] = images.value.splice(fromIndex, 1)
    images.value.splice(toIndex, 0, movedImage)
    
    emit('reorder', fromIndex, toIndex)
    emit('update', files.value)
  }
  
  dragIndex.value = null
  dropIndex.value = null
}

// 生命周期
onUnmounted(() => {
  images.value.forEach(img => URL.revokeObjectURL(img.preview))
})

// 暴露方法和状态
defineExpose({
  clearAll,
  triggerFileInput,
  images,
  files
})
</script>

<style scoped>
.product-uploader {
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

/* 图片列表 */
.image-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

/* 图片项 */
.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
  cursor: grab;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md, 0 8px 24px rgba(0, 0, 0, 0.06));
}

.image-item.dragging {
  opacity: 0.5;
  cursor: grabbing;
}

.image-item.drag-over {
  border-color: var(--primary, #ff2442);
  transform: scale(1.05);
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.4) 0%, transparent 40%, transparent 60%, rgba(0,0,0,0.4) 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-index {
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn {
  align-self: flex-end;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 77, 79, 0.9);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #ff4d4f;
  transform: scale(1.1);
}

.product-type-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 4px;
  font-size: 10px;
}

/* 添加按钮 */
.add-button {
  aspect-ratio: 1;
  border: 2px dashed var(--border-color, #eee);
  border-radius: var(--radius-md, 12px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-placeholder, #ccc);
  min-height: 100px;
}

.add-button:hover {
  border-color: var(--primary, #ff2442);
  color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
}

.add-button.drag-over {
  border-color: var(--primary, #ff2442);
  background: var(--primary-light, #fff0f2);
  transform: scale(1.02);
}

.add-button span {
  font-size: 12px;
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

/* 商品类型提示 */
.product-types-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 12px;
  background: #fafafa;
  border-radius: var(--radius-sm, 8px);
}

.hint-label {
  font-size: 12px;
  color: var(--text-sub, #666);
}

.type-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.type-tag {
  padding: 2px 8px;
  background: white;
  border: 1px solid var(--border-color, #eee);
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-sub, #666);
}
</style>
