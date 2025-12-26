<template>
  <div class="container">
    <!-- 加载中 -->
    <template v-if="loading">
      <div class="loading-container">
        <div class="spinner-primary"></div>
        <p>加载中...</p>
      </div>
    </template>

    <!-- 错误状态 -->
    <template v-else-if="error">
      <div class="error-container">
        <div class="error-icon">!</div>
        <h2>加载失败</h2>
        <p>{{ error }}</p>
        <button class="btn btn-secondary" @click="goBack">返回</button>
      </div>
    </template>

    <!-- 编辑界面 -->
    <template v-else>
      <div class="page-header">
        <div>
          <h1 class="page-title">图片编辑</h1>
          <p class="page-subtitle">使用 AI 对生成的图片进行二次编辑</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary" @click="handleCancel" :disabled="isProcessing">
            取消
          </button>
          <button class="btn btn-primary" @click="handleSave" :disabled="isProcessing || !hasChanges">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            保存
          </button>
        </div>
      </div>

      <div class="edit-layout">
        <!-- 左侧：图片编辑区域 -->
        <div class="edit-canvas-section">
          <div class="card edit-card">
            <ImageEditor
              ref="imageEditorRef"
              :image-url="currentImageUrl"
              :brush-size="brushSize"
              @mask-change="handleMaskChange"
            />
            
            <!-- 画笔工具栏 -->
            <div class="brush-toolbar">
              <div class="brush-size-control">
                <label>画笔大小</label>
                <input
                  type="range"
                  v-model.number="brushSize"
                  min="5"
                  max="100"
                  step="5"
                />
                <span class="brush-size-value">{{ brushSize }}px</span>
              </div>
              <button class="btn btn-secondary btn-sm" @click="clearMask" :disabled="!hasMask">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 6h18"></path>
                  <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                  <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                </svg>
                清除蒙版
              </button>
            </div>
          </div>
        </div>

        <!-- 右侧：编辑控制区域 -->
        <div class="edit-control-section">
          <!-- 编辑指令输入 -->
          <div class="card">
            <h3 class="section-title-sm">编辑指令</h3>
            <textarea
              v-model="instruction"
              placeholder="描述你想要的修改，例如：把包包往左移一点、调亮一些、去掉背景杂物..."
              rows="4"
              class="instruction-input"
              :disabled="isProcessing"
            ></textarea>
            <button
              class="btn btn-primary apply-btn"
              @click="handleApplyEdit"
              :disabled="!canApplyEdit || isProcessing"
            >
              <template v-if="isProcessing">
                <div class="spinner-sm"></div>
                处理中...
              </template>
              <template v-else>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
                应用编辑
              </template>
            </button>
            <p class="edit-tip">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
              提示：可以在图片上绘制蒙版来指定编辑区域
            </p>
          </div>

          <!-- 撤销/重做控制 -->
          <div class="card">
            <h3 class="section-title-sm">历史操作</h3>
            <div class="history-controls">
              <button
                class="btn btn-secondary history-btn"
                @click="handleUndo"
                :disabled="!canUndo || isProcessing"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 7v6h6"></path>
                  <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path>
                </svg>
                撤销
              </button>
              <button
                class="btn btn-secondary history-btn"
                @click="handleRedo"
                :disabled="!canRedo || isProcessing"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 7v6h-6"></path>
                  <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"></path>
                </svg>
                重做
              </button>
            </div>
            <div class="history-info">
              <span>历史记录: {{ historyIndex + 1 }} / {{ historyCount }}</span>
              <span class="history-limit">(最多 10 步)</span>
            </div>
          </div>

          <!-- 预设编辑指令 -->
          <div class="card">
            <h3 class="section-title-sm">快捷指令</h3>
            <div class="preset-instructions">
              <button
                v-for="preset in presetInstructions"
                :key="preset"
                class="preset-btn"
                @click="applyPreset(preset)"
                :disabled="isProcessing"
              >
                {{ preset }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ImageEditor } from '../components/productPhoto'
import {
  createEditSession,
  applyEditWithMaskCanvas,
  undoEdit,
  redoEdit,
  saveEdit,
  cancelEdit,
  getCurrentImageUrl,
  getSessionInfo,
  type EditSession
} from '../api/edit'

/**
 * 产品图编辑页面
 *
 * 功能：
 * - 加载生成的图片进行编辑
 * - 编辑指令输入
 * - 撤销/重做控制
 * - 保存/取消按钮
 *
 * Requirements: 12.1, 12.2, 12.4, 12.5, 12.6
 */

const route = useRoute()
const router = useRouter()

// 组件引用
const imageEditorRef = ref<InstanceType<typeof ImageEditor> | null>(null)

// 状态
const loading = ref(true)
const error = ref<string | null>(null)
const isProcessing = ref(false)
const sessionId = ref<string | null>(null)
const session = ref<EditSession | null>(null)

// 编辑状态
const instruction = ref('')
const brushSize = ref(30)
const hasMask = ref(false)
const hasChanges = ref(false)

// 预设编辑指令
const presetInstructions = [
  '调亮一些',
  '调暗一些',
  '增加对比度',
  '去掉背景杂物',
  '模糊背景',
  '锐化图片',
  '调整色调更暖',
  '调整色调更冷'
]

// 计算属性
const taskId = computed(() => route.params.taskId as string)
const imageIndex = computed(() => parseInt(route.params.imageIndex as string) || 0)

const currentImageUrl = computed(() => {
  if (!sessionId.value) return ''
  return getCurrentImageUrl(sessionId.value) + `?t=${Date.now()}`
})

const canUndo = computed(() => session.value?.can_undo ?? false)
const canRedo = computed(() => session.value?.can_redo ?? false)
const historyIndex = computed(() => session.value?.history_index ?? 0)
const historyCount = computed(() => session.value?.history_count ?? 1)

const canApplyEdit = computed(() => {
  return instruction.value.trim().length > 0
})

// 初始化编辑会话
async function initSession() {
  loading.value = true
  error.value = null

  try {
    const result = await createEditSession({
      taskId: taskId.value,
      imageIndex: imageIndex.value
    })

    if (!result.success || !result.session_id) {
      throw new Error(result.error || '创建编辑会话失败')
    }

    sessionId.value = result.session_id
    session.value = result.session || null

    // 获取完整会话信息
    await refreshSession()
  } catch (e) {
    console.error('初始化编辑会话失败:', e)
    error.value = e instanceof Error ? e.message : '初始化失败'
  } finally {
    loading.value = false
  }
}

// 刷新会话信息
async function refreshSession() {
  if (!sessionId.value) return

  try {
    const result = await getSessionInfo(sessionId.value)
    if (result.success && result.session) {
      session.value = result.session
    }
  } catch (e) {
    console.error('刷新会话信息失败:', e)
  }
}

// 应用编辑
async function handleApplyEdit() {
  if (!sessionId.value || !canApplyEdit.value) return

  isProcessing.value = true

  try {
    // 获取蒙版 canvas
    const maskCanvas = imageEditorRef.value?.getMaskCanvas()

    const result = await applyEditWithMaskCanvas(
      sessionId.value,
      instruction.value,
      hasMask.value && maskCanvas ? maskCanvas : undefined
    )

    if (!result.success) {
      throw new Error(result.error || '编辑失败')
    }

    // 更新会话信息
    if (result.session) {
      session.value = result.session
    }

    // 清空指令和蒙版
    instruction.value = ''
    clearMask()
    hasChanges.value = true

    // 强制刷新图片
    await refreshSession()
  } catch (e) {
    console.error('应用编辑失败:', e)
    alert(e instanceof Error ? e.message : '编辑失败')
  } finally {
    isProcessing.value = false
  }
}

// 撤销
async function handleUndo() {
  if (!sessionId.value || !canUndo.value) return

  isProcessing.value = true

  try {
    const result = await undoEdit(sessionId.value)

    if (!result.success) {
      throw new Error(result.error || '撤销失败')
    }

    if (result.session) {
      session.value = result.session
    }

    await refreshSession()
  } catch (e) {
    console.error('撤销失败:', e)
    alert(e instanceof Error ? e.message : '撤销失败')
  } finally {
    isProcessing.value = false
  }
}

// 重做
async function handleRedo() {
  if (!sessionId.value || !canRedo.value) return

  isProcessing.value = true

  try {
    const result = await redoEdit(sessionId.value)

    if (!result.success) {
      throw new Error(result.error || '重做失败')
    }

    if (result.session) {
      session.value = result.session
    }

    await refreshSession()
  } catch (e) {
    console.error('重做失败:', e)
    alert(e instanceof Error ? e.message : '重做失败')
  } finally {
    isProcessing.value = false
  }
}

// 保存编辑
async function handleSave() {
  if (!sessionId.value) return

  isProcessing.value = true

  try {
    const result = await saveEdit(sessionId.value)

    if (!result.success) {
      throw new Error(result.error || '保存失败')
    }

    // 保存成功，返回上一页
    alert('保存成功')
    goBack()
  } catch (e) {
    console.error('保存失败:', e)
    alert(e instanceof Error ? e.message : '保存失败')
  } finally {
    isProcessing.value = false
  }
}

// 取消编辑
async function handleCancel() {
  if (hasChanges.value) {
    const confirmed = confirm('确定要取消编辑吗？所有未保存的更改将丢失。')
    if (!confirmed) return
  }

  if (sessionId.value) {
    try {
      await cancelEdit(sessionId.value)
    } catch (e) {
      console.error('取消编辑失败:', e)
    }
  }

  goBack()
}

// 返回上一页
function goBack() {
  router.back()
}

// 处理蒙版变化
function handleMaskChange(hasMaskValue: boolean) {
  hasMask.value = hasMaskValue
}

// 清除蒙版
function clearMask() {
  imageEditorRef.value?.clearMask()
  hasMask.value = false
}

// 应用预设指令
function applyPreset(preset: string) {
  instruction.value = preset
}

// 生命周期
onMounted(() => {
  initSession()
})

onUnmounted(() => {
  // 如果有未保存的会话，清理它
  if (sessionId.value && !hasChanges.value) {
    cancelEdit(sessionId.value).catch(() => {})
  }
})
</script>

<style scoped>
/* 加载和错误状态 */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
  color: var(--text-secondary, #999);
}

.error-container {
  color: #ff4d4f;
}

.error-container h2 {
  color: var(--text-main, #333);
  margin: 0;
}

.error-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #ff4d4f;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
}

.spinner-primary {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color, #eee);
  border-top-color: var(--primary, #ff2442);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 头部操作 */
.header-actions {
  display: flex;
  gap: 12px;
}

/* 编辑布局 */
.edit-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

@media (max-width: 1024px) {
  .edit-layout {
    grid-template-columns: 1fr;
  }
}

/* 编辑画布区域 */
.edit-canvas-section {
  display: flex;
  flex-direction: column;
}

.edit-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 画笔工具栏 */
.brush-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, #eee);
}

.brush-size-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brush-size-control label {
  font-size: 14px;
  color: var(--text-sub, #666);
  font-weight: 500;
}

.brush-size-control input[type="range"] {
  width: 120px;
  accent-color: var(--primary, #ff2442);
}

.brush-size-value {
  font-size: 13px;
  color: var(--text-secondary, #999);
  min-width: 50px;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
}

/* 编辑控制区域 */
.edit-control-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title-sm {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main, #333);
  margin: 0 0 12px 0;
}

/* 编辑指令输入 */
.instruction-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color, #eee);
  border-radius: var(--radius-sm, 8px);
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
  font-family: inherit;
  margin-bottom: 12px;
}

.instruction-input:focus {
  outline: none;
  border-color: var(--primary, #ff2442);
}

.instruction-input::placeholder {
  color: var(--text-placeholder, #ccc);
}

.instruction-input:disabled {
  background: #f9f9f9;
  cursor: not-allowed;
}

.apply-btn {
  width: 100%;
  margin-bottom: 12px;
}

.edit-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary, #999);
  margin: 0;
}

/* 历史控制 */
.history-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.history-btn {
  flex: 1;
}

.history-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-secondary, #999);
}

.history-limit {
  color: var(--text-placeholder, #ccc);
}

/* 预设指令 */
.preset-instructions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-btn {
  padding: 8px 14px;
  background: #f5f5f5;
  border: 1px solid transparent;
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-sub, #666);
  cursor: pointer;
  transition: all 0.2s;
}

.preset-btn:hover:not(:disabled) {
  background: white;
  border-color: var(--primary, #ff2442);
  color: var(--primary, #ff2442);
}

.preset-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 小型加载动画 */
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
