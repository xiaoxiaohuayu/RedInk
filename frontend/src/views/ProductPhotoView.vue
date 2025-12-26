<template>
  <div class="container">
    <!-- 输入阶段 -->
    <template v-if="store.stage === 'input'">
      <div class="page-header">
        <div>
          <h1 class="page-title">产品图生成</h1>
          <p class="page-subtitle">上传模特图和商品图，AI 自动合成专业产品展示图</p>
        </div>
      </div>

      <div class="content-layout">
        <!-- 左侧：图片上传区域 -->
        <div class="upload-section">
          <div class="card">
            <ModelImageUploader
              v-model="store.modelImage"
              :preview-url="store.modelImagePreview"
              @update:modelValue="handleModelImageChange"
              @update:previewUrl="handleModelPreviewChange"
              @templateSelected="handleTemplateSelected"
            />
          </div>

          <div class="card">
            <ProductImageUploader
              ref="productUploaderRef"
              :max-images="10"
              @update="handleProductImagesUpdate"
              @add="handleProductImagesAdd"
              @remove="handleProductImageRemove"
              @reorder="handleProductImagesReorder"
            />
          </div>
        </div>

        <!-- 右侧：配置区域 -->
        <div class="config-section">
          <!-- 供应商选择 -->
          <div class="card">
            <ProviderSelector
              :model-value="store.selectedProvider ?? undefined"
              :providers="store.providers"
              :loading="providersLoading"
              @update:model-value="(v: string) => store.setProvider(v)"
              @refresh="loadProviders"
              @providerChange="handleProviderChange"
            />
          </div>

          <!-- 风格选择 -->
          <div class="card">
            <StyleSelector v-model="store.config.style" />
          </div>

          <!-- 背景设置 -->
          <div class="card" v-if="store.supportsBackgroundChange">
            <BackgroundSelector v-model="store.config.background" />
          </div>

          <!-- 姿势设置 -->
          <div class="card" v-if="store.supportsPoseChange">
            <PoseSelector
              v-model="store.config.pose"
              :supported="store.supportsPoseChange"
            />
          </div>

          <!-- 商品位置 -->
          <div class="card">
            <PlacementSelector v-model="store.config.placement" />
          </div>

          <!-- 提示词输入 -->
          <div class="card">
            <div class="prompt-section">
              <h3 class="section-title-sm">补充描述</h3>
              <textarea
                v-model="store.config.prompt"
                placeholder="可选：补充描述你想要的效果，例如：阳光明媚、时尚街拍风格..."
                rows="3"
                class="prompt-input"
              ></textarea>
            </div>
          </div>

          <!-- 生成数量 -->
          <div class="card">
            <div class="variations-section">
              <h3 class="section-title-sm">生成数量</h3>
              <div class="variations-options">
                <button
                  v-for="n in 4"
                  :key="n"
                  class="variation-btn"
                  :class="{ active: store.config.variations === n }"
                  @click="store.config.variations = n"
                >
                  {{ n }} 张
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="action-bar">
        <button class="btn btn-secondary" @click="handleReset">
          重置
        </button>
        <button
          class="btn btn-primary"
          :disabled="!store.canGenerate"
          @click="handleStartGeneration"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
          开始生成
        </button>
      </div>
    </template>

    <!-- 生成中阶段 -->
    <template v-else-if="store.stage === 'generating'">
      <div class="page-header">
        <div>
          <h1 class="page-title">生成中...</h1>
          <p class="page-subtitle">{{ store.progress.message }}</p>
        </div>
      </div>

      <div class="card generating-card">
        <div class="progress-info">
          <span>生成进度</span>
          <span class="progress-percent">{{ progressPercent }}%</span>
        </div>
        <div class="progress-container">
          <div class="progress-bar" :style="{ width: progressPercent + '%' }"></div>
        </div>

        <div class="generating-preview">
          <div
            v-for="image in store.images"
            :key="image.index"
            class="preview-item"
            :class="image.status"
          >
            <div v-if="image.status === 'done' && image.url" class="preview-image">
              <img :src="store.getImageUrl(image.index)" :alt="`生成图 ${image.index + 1}`" />
            </div>
            <div v-else-if="image.status === 'generating'" class="preview-placeholder">
              <div class="spinner-primary"></div>
              <span>生成中...</span>
            </div>
            <div v-else-if="image.status === 'error'" class="preview-placeholder error">
              <div class="error-icon">!</div>
              <span>生成失败</span>
            </div>
            <div v-else class="preview-placeholder">
              <span>等待中</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 结果阶段 -->
    <template v-else-if="store.stage === 'result'">
      <div class="page-header">
        <div>
          <h1 class="page-title">生成完成</h1>
          <p class="page-subtitle">
            <span v-if="store.hasFailedImages">
              {{ store.failedImages.length }} 张图片生成失败，可点击重试
            </span>
            <span v-else>
              全部 {{ store.images.length }} 张图片生成完成
            </span>
          </p>
        </div>
        <div class="header-actions">
          <button
            v-if="store.hasFailedImages"
            class="btn btn-secondary"
            @click="handleRetryAllFailed"
            :disabled="isRetrying"
          >
            {{ isRetrying ? '重试中...' : '重试失败图片' }}
          </button>
          <button class="btn btn-secondary" @click="handleRegenerate">
            重新生成
          </button>
          <button class="btn btn-primary" @click="handleBackToInput">
            生成新图
          </button>
        </div>
      </div>

      <div v-if="store.error" class="error-msg">
        {{ store.error }}
      </div>

      <div class="result-grid">
        <div
          v-for="image in store.images"
          :key="image.index"
          class="result-card"
          :class="{ 'has-error': image.status === 'error' }"
        >
          <!-- 成功的图片 -->
          <div v-if="image.status === 'done' && image.url" class="result-image">
            <img
              :src="store.getImageUrl(image.index, false)"
              :alt="`生成图 ${image.index + 1}`"
              @click="openPreview(image.index)"
            />
            <div class="result-overlay">
              <button class="overlay-action" @click="handleDownload(image.index)" title="下载">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
              </button>
              <button class="overlay-action" @click="handleRetryImage(image.index)" title="重新生成">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 4v6h-6"></path>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- 重试中 -->
          <div v-else-if="image.status === 'retrying'" class="result-placeholder">
            <div class="spinner-primary"></div>
            <span>重试中...</span>
          </div>

          <!-- 失败的图片 -->
          <div v-else-if="image.status === 'error'" class="result-placeholder error">
            <div class="error-icon">!</div>
            <span>{{ image.error || '生成失败' }}</span>
            <button class="retry-btn" @click="handleRetryImage(image.index)">
              点击重试
            </button>
          </div>

          <!-- 底部信息 -->
          <div class="result-footer">
            <span class="result-index">图片 {{ image.index + 1 }}</span>
            <span class="result-status" :class="image.status">
              {{ getStatusText(image.status) }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- 图片预览模态框 -->
    <div v-if="previewIndex !== null" class="preview-modal" @click.self="closePreview">
      <div class="preview-content">
        <button class="preview-close" @click="closePreview">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        <img
          :src="store.getImageUrl(previewIndex, false)"
          :alt="`预览图 ${previewIndex + 1}`"
        />
        <div class="preview-actions">
          <button class="btn btn-secondary" @click="handleDownload(previewIndex)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            下载原图
          </button>
          <button class="btn btn-primary" @click="handleRetryImage(previewIndex); closePreview()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6"></path>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            重新生成
          </button>
        </div>
        <!-- 导航按钮 -->
        <button
          v-if="previewIndex > 0"
          class="preview-nav prev"
          @click="previewIndex--"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
        <button
          v-if="previewIndex < store.images.length - 1"
          class="preview-nav next"
          @click="previewIndex++"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProductPhotoStore, setupProductPhotoAutoSave } from '../stores/productPhoto'
import {
  ModelImageUploader,
  ProductImageUploader,
  BackgroundSelector,
  PoseSelector,
  StyleSelector,
  PlacementSelector,
  ProviderSelector
} from '../components/productPhoto'
import type { Template } from '../api/template'
import type { ProviderInfo } from '../api/productPhoto'

/**
 * 产品图生成主页面
 *
 * 功能：
 * - 集成所有上传和配置组件
 * - SSE 流式生成进度显示
 * - 结果预览和重新生成
 * - 下载功能
 *
 * Requirements: 1.5, 2.1, 2.2, 2.4, 3.1, 3.3, 6.1, 6.2, 6.3
 */

const store = useProductPhotoStore()

// 组件引用
const productUploaderRef = ref<InstanceType<typeof ProductImageUploader> | null>(null)

// 状态
const providersLoading = ref(false)
const isRetrying = ref(false)
const previewIndex = ref<number | null>(null)

// 计算属性
const progressPercent = computed(() => {
  if (store.progress.total === 0) return 0
  return Math.round((store.progress.current / store.progress.total) * 100)
})

// 状态文本映射
function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    pending: '等待中',
    generating: '生成中',
    done: '已完成',
    error: '失败',
    retrying: '重试中'
  }
  return texts[status] || '未知'
}

// 加载供应商列表
async function loadProviders() {
  providersLoading.value = true
  try {
    await store.loadProviders()
  } finally {
    providersLoading.value = false
  }
}

// 处理模特图变化
function handleModelImageChange(file: File | null) {
  store.setModelImage(file)
}

function handleModelPreviewChange(url: string | null) {
  store.modelImagePreview = url
}

function handleTemplateSelected(template: Template) {
  console.log('选择了模板:', template.name)
}

// 处理商品图变化
function handleProductImagesUpdate(files: File[]) {
  store.productImages = files
}

function handleProductImagesAdd(files: File[]) {
  store.addProductImages(files)
}

function handleProductImageRemove(index: number) {
  store.removeProductImage(index)
}

function handleProductImagesReorder(fromIndex: number, toIndex: number) {
  store.reorderProductImages(fromIndex, toIndex)
}

// 处理供应商变化
function handleProviderChange(provider: ProviderInfo) {
  store.setProvider(provider.name)
}

// 开始生成
async function handleStartGeneration() {
  if (!store.canGenerate) return
  await store.startGeneration()
}

// 重试单张图片
async function handleRetryImage(index: number) {
  isRetrying.value = true
  try {
    await store.retryFailedImage(index)
  } finally {
    isRetrying.value = false
  }
}

// 重试所有失败的图片
async function handleRetryAllFailed() {
  isRetrying.value = true
  try {
    await store.retryAllFailed()
  } finally {
    isRetrying.value = false
  }
}

// 重新生成（保留配置）
function handleRegenerate() {
  store.regenerate()
}

// 返回输入阶段
function handleBackToInput() {
  store.reset()
  productUploaderRef.value?.clearAll()
}

// 重置
function handleReset() {
  store.reset()
  productUploaderRef.value?.clearAll()
}

// 下载图片
async function handleDownload(index: number) {
  const imageUrl = store.getImageUrl(index, false)
  if (!imageUrl) return

  try {
    const response = await fetch(imageUrl)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `product-photo-${store.taskId}-${index + 1}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('下载失败:', e)
  }
}

// 预览相关
function openPreview(index: number) {
  previewIndex.value = index
}

function closePreview() {
  previewIndex.value = null
}

// 生命周期
onMounted(async () => {
  // 设置自动保存
  setupProductPhotoAutoSave()
  // 加载供应商列表
  await loadProviders()
})
</script>


<style scoped>
/* 内容布局 */
.content-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

@media (max-width: 1024px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
}

.upload-section,
.config-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 小标题 */
.section-title-sm {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main, #333);
  margin: 0 0 12px 0;
}

/* 提示词输入 */
.prompt-section {
  display: flex;
  flex-direction: column;
}

.prompt-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
  font-family: inherit;
}

.prompt-input:focus {
  outline: none;
  border-color: var(--primary, #ff2442);
}

.prompt-input::placeholder {
  color: var(--text-placeholder, #ccc);
}

/* 生成数量选择 */
.variations-section {
  display: flex;
  flex-direction: column;
}

.variations-options {
  display: flex;
  gap: 10px;
}

.variation-btn {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  background: var(--bg-card, #fff);
  color: var(--text-sub, #666);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.variation-btn:hover {
  border-color: var(--border-hover, #e0e0e0);
}

.variation-btn.active {
  border-color: var(--primary, #ff2442);
  background: var(--primary-fade, rgba(255, 36, 66, 0.08));
  color: var(--primary, #ff2442);
}

/* 底部操作栏 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px 0;
  border-top: 1px solid var(--border-color, #eee);
  margin-top: 24px;
}

/* 头部操作按钮 */
.header-actions {
  display: flex;
  gap: 12px;
}

/* 生成中卡片 */
.generating-card {
  text-align: center;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
}

.progress-percent {
  color: var(--primary, #ff2442);
}

.generating-preview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 32px;
}

.preview-item {
  aspect-ratio: 3/4;
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
  border: 2px solid var(--border-color, #eee);
}

.preview-item.done {
  border-color: #22c55e;
}

.preview-item.generating {
  border-color: var(--primary, #ff2442);
}

.preview-item.error {
  border-color: #ff4d4f;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #f9f9f9;
  color: var(--text-secondary, #999);
  font-size: 14px;
}

.preview-placeholder.error {
  background: #fff5f5;
  color: #ff4d4f;
}

.spinner-primary {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color, #eee);
  border-top-color: var(--primary, #ff2442);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ff4d4f;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

/* 结果网格 */
.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.result-card {
  background: var(--bg-card, #fff);
  border-radius: var(--radius-lg, 16px);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s;
}

.result-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-4px);
}

.result-card.has-error {
  border: 2px solid #ffccc7;
}

.result-image {
  position: relative;
  aspect-ratio: 3/4;
  cursor: pointer;
}

.result-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  opacity: 0;
  transition: opacity 0.2s;
}

.result-image:hover .result-overlay {
  opacity: 1;
}

.overlay-action {
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

.overlay-action:hover {
  background: white;
  color: var(--text-main, #333);
  transform: scale(1.1);
}

.result-placeholder {
  aspect-ratio: 3/4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #f9f9f9;
  color: var(--text-secondary, #999);
  font-size: 14px;
}

.result-placeholder.error {
  background: #fff5f5;
  color: #ff4d4f;
}

.retry-btn {
  margin-top: 8px;
  padding: 8px 20px;
  background: var(--primary, #ff2442);
  color: white;
  border: none;
  border-radius: var(--radius-sm, 8px);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.retry-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}

.result-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color, #eee);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-index {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-main, #333);
}

.result-status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
}

.result-status.done {
  background: #e6f7ed;
  color: #52c41a;
}

.result-status.generating,
.result-status.retrying {
  background: #e6f4ff;
  color: #1890ff;
}

.result-status.error {
  background: #fff1f0;
  color: #ff4d4f;
}

.result-status.pending {
  background: #f5f5f5;
  color: #999;
}

/* 预览模态框 */
.preview-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.preview-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-content img {
  max-width: 100%;
  max-height: calc(90vh - 80px);
  object-fit: contain;
  border-radius: var(--radius-md, 12px);
}

.preview-close {
  position: absolute;
  top: -40px;
  right: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.preview-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.preview-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.preview-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.preview-nav:hover {
  background: rgba(255, 255, 255, 0.3);
}

.preview-nav.prev {
  left: -60px;
}

.preview-nav.next {
  right: -60px;
}
</style>
