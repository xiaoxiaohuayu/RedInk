<template>
  <div class="image-editor" ref="containerRef">
    <!-- 画布容器 -->
    <div class="canvas-container" ref="canvasContainerRef">
      <!-- 底层图片 -->
      <canvas
        ref="imageCanvasRef"
        class="image-canvas"
      ></canvas>
      
      <!-- 蒙版层 -->
      <canvas
        ref="maskCanvasRef"
        class="mask-canvas"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
        @touchstart.prevent="handleTouchStart"
        @touchmove.prevent="handleTouchMove"
        @touchend.prevent="stopDrawing"
      ></canvas>
      
      <!-- 画笔预览 -->
      <div
        v-if="showBrushPreview"
        class="brush-preview"
        :style="brushPreviewStyle"
      ></div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载图片中...</span>
    </div>
    
    <!-- 错误状态 -->
    <div v-if="loadError" class="error-overlay">
      <span>图片加载失败</span>
      <button class="retry-btn" @click="loadImage">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

/**
 * 图片编辑器组件
 *
 * 功能：
 * - Canvas 画布显示图片
 * - 蒙版绘制（用于局部编辑）
 * - 画笔大小控制
 * - 清除蒙版
 *
 * Requirements: 12.3
 */

interface Props {
  imageUrl: string
  brushSize?: number
  brushColor?: string
  maskOpacity?: number
}

const props = withDefaults(defineProps<Props>(), {
  brushSize: 30,
  brushColor: 'rgba(255, 36, 66, 0.5)',
  maskOpacity: 0.5
})

const emit = defineEmits<{
  (e: 'mask-change', hasMask: boolean): void
}>()

// DOM 引用
const containerRef = ref<HTMLDivElement | null>(null)
const canvasContainerRef = ref<HTMLDivElement | null>(null)
const imageCanvasRef = ref<HTMLCanvasElement | null>(null)
const maskCanvasRef = ref<HTMLCanvasElement | null>(null)

// 状态
const loading = ref(false)
const loadError = ref(false)
const isDrawing = ref(false)
const hasMask = ref(false)
const showBrushPreview = ref(false)
const brushPosition = ref({ x: 0, y: 0 })

// 图片尺寸
const imageWidth = ref(0)
const imageHeight = ref(0)
const canvasScale = ref(1)

// 计算属性
const brushPreviewStyle = computed(() => ({
  width: `${props.brushSize}px`,
  height: `${props.brushSize}px`,
  left: `${brushPosition.value.x - props.brushSize / 2}px`,
  top: `${brushPosition.value.y - props.brushSize / 2}px`,
  borderColor: props.brushColor.replace(/[\d.]+\)$/, '1)')
}))

// 加载图片
async function loadImage() {
  if (!props.imageUrl || !imageCanvasRef.value) return

  loading.value = true
  loadError.value = false

  try {
    const img = new Image()
    img.crossOrigin = 'anonymous'

    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve()
      img.onerror = () => reject(new Error('图片加载失败'))
      img.src = props.imageUrl
    })

    // 设置画布尺寸
    await nextTick()
    setupCanvases(img)
  } catch (e) {
    console.error('加载图片失败:', e)
    loadError.value = true
  } finally {
    loading.value = false
  }
}

// 设置画布
function setupCanvases(img: HTMLImageElement) {
  const imageCanvas = imageCanvasRef.value
  const maskCanvas = maskCanvasRef.value
  const container = canvasContainerRef.value

  if (!imageCanvas || !maskCanvas || !container) return

  // 计算适合容器的尺寸
  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight || 600

  const imgRatio = img.width / img.height
  const containerRatio = containerWidth / containerHeight

  let displayWidth: number
  let displayHeight: number

  if (imgRatio > containerRatio) {
    // 图片更宽，以宽度为准
    displayWidth = containerWidth
    displayHeight = containerWidth / imgRatio
  } else {
    // 图片更高，以高度为准
    displayHeight = containerHeight
    displayWidth = containerHeight * imgRatio
  }

  // 保存原始尺寸和缩放比例
  imageWidth.value = img.width
  imageHeight.value = img.height
  canvasScale.value = img.width / displayWidth

  // 设置画布尺寸
  imageCanvas.width = displayWidth
  imageCanvas.height = displayHeight
  maskCanvas.width = displayWidth
  maskCanvas.height = displayHeight

  // 绘制图片
  const ctx = imageCanvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(img, 0, 0, displayWidth, displayHeight)
  }

  // 初始化蒙版画布
  const maskCtx = maskCanvas.getContext('2d')
  if (maskCtx) {
    maskCtx.clearRect(0, 0, displayWidth, displayHeight)
  }
}

// 获取画布坐标
function getCanvasCoordinates(event: MouseEvent | Touch): { x: number; y: number } {
  const canvas = maskCanvasRef.value
  if (!canvas) return { x: 0, y: 0 }

  const rect = canvas.getBoundingClientRect()
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }
}

// 开始绘制
function startDrawing(event: MouseEvent) {
  isDrawing.value = true
  const coords = getCanvasCoordinates(event)
  drawPoint(coords.x, coords.y)
}

// 绘制
function draw(event: MouseEvent) {
  const coords = getCanvasCoordinates(event)
  brushPosition.value = coords
  showBrushPreview.value = true

  if (!isDrawing.value) return
  drawPoint(coords.x, coords.y)
}

// 停止绘制
function stopDrawing() {
  isDrawing.value = false
  showBrushPreview.value = false
}

// 绘制点
function drawPoint(x: number, y: number) {
  const canvas = maskCanvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.globalCompositeOperation = 'source-over'
  ctx.fillStyle = props.brushColor
  ctx.beginPath()
  ctx.arc(x, y, props.brushSize / 2, 0, Math.PI * 2)
  ctx.fill()

  // 标记有蒙版
  if (!hasMask.value) {
    hasMask.value = true
    emit('mask-change', true)
  }
}

// 触摸事件处理
function handleTouchStart(event: TouchEvent) {
  if (event.touches.length === 1) {
    isDrawing.value = true
    const coords = getCanvasCoordinates(event.touches[0])
    drawPoint(coords.x, coords.y)
  }
}

function handleTouchMove(event: TouchEvent) {
  if (event.touches.length === 1 && isDrawing.value) {
    const coords = getCanvasCoordinates(event.touches[0])
    drawPoint(coords.x, coords.y)
  }
}

// 清除蒙版
function clearMask() {
  const canvas = maskCanvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  hasMask.value = false
  emit('mask-change', false)
}

// 获取蒙版 Canvas（用于导出）
function getMaskCanvas(): HTMLCanvasElement | null {
  if (!hasMask.value) return null

  const maskCanvas = maskCanvasRef.value
  if (!maskCanvas) return null

  // 创建原始尺寸的蒙版
  const exportCanvas = document.createElement('canvas')
  exportCanvas.width = imageWidth.value
  exportCanvas.height = imageHeight.value

  const ctx = exportCanvas.getContext('2d')
  if (!ctx) return null

  // 缩放绘制蒙版到原始尺寸
  ctx.drawImage(
    maskCanvas,
    0, 0, maskCanvas.width, maskCanvas.height,
    0, 0, imageWidth.value, imageHeight.value
  )

  return exportCanvas
}

// 获取蒙版数据 URL
function getMaskDataUrl(): string | null {
  const canvas = getMaskCanvas()
  if (!canvas) return null
  return canvas.toDataURL('image/png')
}

// 监听图片 URL 变化
watch(() => props.imageUrl, () => {
  if (props.imageUrl) {
    loadImage()
  }
})

// 监听容器大小变化
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (props.imageUrl) {
    loadImage()
  }

  // 监听容器大小变化
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      if (props.imageUrl) {
        loadImage()
      }
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

// 暴露方法
defineExpose({
  clearMask,
  getMaskCanvas,
  getMaskDataUrl,
  hasMask: () => hasMask.value
})
</script>

<style scoped>
.image-editor {
  position: relative;
  width: 100%;
  min-height: 400px;
  background: #f5f5f5;
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
}

.canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-canvas,
.mask-canvas {
  position: absolute;
  max-width: 100%;
  max-height: 100%;
}

.image-canvas {
  z-index: 1;
}

.mask-canvas {
  z-index: 2;
  cursor: crosshair;
}

.brush-preview {
  position: absolute;
  z-index: 3;
  border: 2px solid;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0.8;
}

/* 加载状态 */
.loading-overlay,
.error-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.9);
}

.spinner {
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

.error-overlay {
  color: #ff4d4f;
}

.retry-btn {
  padding: 8px 16px;
  background: var(--primary, #ff2442);
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.retry-btn:hover {
  opacity: 0.9;
}
</style>
