/**
 * 产品图生成状态管理
 *
 * 管理功能：
 * - 生成状态和进度
 * - 任务管理
 * - 生成结果
 * - 供应商信息
 *
 * Requirements: 1.5, 6.1, 6.2
 */

import { defineStore } from 'pinia'
import { watch } from 'vue'
import {
  generateProductPhoto,
  retryGeneration,
  getTaskStatus,
  getProviders,
  getProductPhotoImageUrl,
  type GenerateProductPhotoRequest,
  type ProviderInfo,
  type BackgroundConfig,
  type PlacementConfig
} from '../api/productPhoto'

// ==================== 类型定义 ====================

export interface GeneratedProductImage {
  index: number
  url: string
  status: 'pending' | 'generating' | 'done' | 'error' | 'retrying'
  error?: string
}

export interface ProductPhotoConfig {
  prompt: string
  aspectRatio: string
  style: string
  background?: BackgroundConfig
  placement?: PlacementConfig
  pose?: string
  variations: number
  provider?: string
}

export interface ProductPhotoState {
  // 当前阶段
  stage: 'input' | 'generating' | 'result'

  // 模特图
  modelImage: File | null
  modelImagePreview: string | null

  // 商品图列表
  productImages: File[]
  productImagePreviews: string[]

  // 生成配置
  config: ProductPhotoConfig

  // 生成进度
  progress: {
    current: number
    total: number
    status: 'idle' | 'generating' | 'done' | 'error'
    message: string
  }

  // 生成结果
  images: GeneratedProductImage[]

  // 任务 ID
  taskId: string | null

  // 供应商列表
  providers: ProviderInfo[]

  // 当前选中的供应商
  selectedProvider: string | null

  // 错误信息
  error: string | null
}

const STORAGE_KEY = 'product-photo-state'

// ==================== 辅助函数 ====================

/**
 * 从 localStorage 加载状态
 */
function loadState(): Partial<ProductPhotoState> {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('加载产品图状态失败:', e)
  }
  return {}
}

/**
 * 保存状态到 localStorage
 */
function saveState(state: ProductPhotoState) {
  try {
    // 只保存可序列化的数据，不保存 File 对象
    const toSave = {
      stage: state.stage,
      config: state.config,
      progress: state.progress,
      images: state.images,
      taskId: state.taskId,
      selectedProvider: state.selectedProvider
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
  } catch (e) {
    console.error('保存产品图状态失败:', e)
  }
}

/**
 * 创建默认配置
 */
function createDefaultConfig(): ProductPhotoConfig {
  return {
    prompt: '',
    aspectRatio: '3:4',
    style: '自然',
    variations: 1
  }
}

// ==================== Store 定义 ====================

export const useProductPhotoStore = defineStore('productPhoto', {
  state: (): ProductPhotoState => {
    const saved = loadState()
    return {
      stage: saved.stage || 'input',
      modelImage: null,
      modelImagePreview: null,
      productImages: [],
      productImagePreviews: [],
      config: saved.config || createDefaultConfig(),
      progress: saved.progress || {
        current: 0,
        total: 0,
        status: 'idle',
        message: ''
      },
      images: saved.images || [],
      taskId: saved.taskId || null,
      providers: [],
      selectedProvider: saved.selectedProvider || null,
      error: null
    }
  },

  getters: {
    /**
     * 是否可以开始生成
     */
    canGenerate(): boolean {
      return this.modelImage !== null && this.productImages.length > 0
    },

    /**
     * 是否正在生成
     */
    isGenerating(): boolean {
      return this.progress.status === 'generating'
    },

    /**
     * 获取失败的图片
     */
    failedImages(): GeneratedProductImage[] {
      return this.images.filter(img => img.status === 'error')
    },

    /**
     * 是否有失败的图片
     */
    hasFailedImages(): boolean {
      return this.images.some(img => img.status === 'error')
    },

    /**
     * 获取成功的图片
     */
    completedImages(): GeneratedProductImage[] {
      return this.images.filter(img => img.status === 'done')
    },

    /**
     * 当前供应商信息
     */
    currentProvider(): ProviderInfo | undefined {
      if (!this.selectedProvider) return undefined
      return this.providers.find(p => p.name === this.selectedProvider)
    },

    /**
     * 当前供应商是否支持换背景
     */
    supportsBackgroundChange(): boolean {
      return this.currentProvider?.features.backgroundChange ?? false
    },

    /**
     * 当前供应商是否支持换姿势
     */
    supportsPoseChange(): boolean {
      return this.currentProvider?.features.poseChange ?? false
    },

    /**
     * 当前供应商是否支持多商品
     */
    supportsMultiProduct(): boolean {
      return this.currentProvider?.features.multiProduct ?? false
    }
  },

  actions: {
    // ==================== 图片管理 ====================

    /**
     * 设置模特图
     */
    setModelImage(file: File | null) {
      this.modelImage = file
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          this.modelImagePreview = e.target?.result as string
        }
        reader.readAsDataURL(file)
      } else {
        this.modelImagePreview = null
      }
    },

    /**
     * 添加商品图
     */
    addProductImage(file: File) {
      this.productImages.push(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        this.productImagePreviews.push(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    },

    /**
     * 添加多张商品图
     */
    addProductImages(files: File[]) {
      files.forEach(file => this.addProductImage(file))
    },

    /**
     * 移除商品图
     */
    removeProductImage(index: number) {
      this.productImages.splice(index, 1)
      this.productImagePreviews.splice(index, 1)
    },

    /**
     * 清空商品图
     */
    clearProductImages() {
      this.productImages = []
      this.productImagePreviews = []
    },

    /**
     * 重新排序商品图
     */
    reorderProductImages(fromIndex: number, toIndex: number) {
      const [movedImage] = this.productImages.splice(fromIndex, 1)
      this.productImages.splice(toIndex, 0, movedImage)

      const [movedPreview] = this.productImagePreviews.splice(fromIndex, 1)
      this.productImagePreviews.splice(toIndex, 0, movedPreview)
    },

    // ==================== 配置管理 ====================

    /**
     * 更新配置
     */
    updateConfig(config: Partial<ProductPhotoConfig>) {
      this.config = { ...this.config, ...config }
    },

    /**
     * 重置配置
     */
    resetConfig() {
      this.config = createDefaultConfig()
    },

    /**
     * 设置供应商
     */
    setProvider(provider: string | null) {
      this.selectedProvider = provider
      this.config.provider = provider || undefined
    },

    // ==================== 供应商管理 ====================

    /**
     * 加载供应商列表
     */
    async loadProviders() {
      try {
        const result = await getProviders()
        if (result.success && result.providers) {
          this.providers = result.providers
          // 如果没有选中的供应商，选择第一个
          if (!this.selectedProvider && this.providers.length > 0) {
            this.selectedProvider = this.providers[0].name
          }
        }
      } catch (e) {
        console.error('加载供应商列表失败:', e)
      }
    },

    // ==================== 生成管理 ====================

    /**
     * 开始生成
     */
    async startGeneration() {
      if (!this.canGenerate) {
        this.error = '请先上传模特图和商品图'
        return
      }

      this.stage = 'generating'
      this.error = null
      this.progress = {
        current: 0,
        total: this.config.variations,
        status: 'generating',
        message: '准备生成...'
      }

      // 初始化图片状态
      this.images = Array.from({ length: this.config.variations }, (_, i) => ({
        index: i,
        url: '',
        status: 'pending' as const
      }))

      const request: GenerateProductPhotoRequest = {
        modelImage: this.modelImage!,
        productImages: this.productImages,
        prompt: this.config.prompt,
        aspectRatio: this.config.aspectRatio,
        style: this.config.style,
        background: this.config.background,
        placement: this.config.placement,
        pose: this.config.pose,
        variations: this.config.variations,
        provider: this.config.provider
      }

      await generateProductPhoto(
        request,
        // onStart
        (event) => {
          this.taskId = event.task_id
          this.progress.message = event.message
        },
        // onProgress
        (event) => {
          this.progress.current = event.current
          this.progress.total = event.total
          if (event.message) {
            this.progress.message = event.message
          }
          // 更新对应图片状态为生成中
          if (event.current > 0 && event.current <= this.images.length) {
            const img = this.images[event.current - 1]
            if (img && img.status === 'pending') {
              img.status = 'generating'
            }
          }
        },
        // onComplete
        (event) => {
          const img = this.images.find(i => i.index === event.index)
          if (img) {
            img.status = 'done'
            img.url = event.image_url
          }
        },
        // onError
        (event) => {
          if (event.index !== undefined) {
            const img = this.images.find(i => i.index === event.index)
            if (img) {
              img.status = 'error'
              img.error = event.error
            }
          } else {
            this.error = event.error
          }
        },
        // onFinish
        (event) => {
          this.progress.status = event.success ? 'done' : 'error'
          this.progress.message = event.success ? '生成完成' : '生成失败'
          this.stage = 'result'
        },
        // onStreamError
        (error) => {
          this.error = error.message
          this.progress.status = 'error'
          this.progress.message = '生成失败'
        }
      )
    },

    /**
     * 重试生成失败的图片
     */
    async retryFailedImage(index: number) {
      if (!this.taskId) {
        this.error = '没有可重试的任务'
        return
      }

      const img = this.images.find(i => i.index === index)
      if (!img || img.status !== 'error') {
        return
      }

      img.status = 'retrying'
      img.error = undefined

      await retryGeneration(
        this.taskId,
        index,
        // onStart
        (event) => {
          this.progress.message = event.message
        },
        // onProgress
        (event) => {
          if (event.message) {
            this.progress.message = event.message
          }
        },
        // onComplete
        (event) => {
          const img = this.images.find(i => i.index === event.index)
          if (img) {
            img.status = 'done'
            img.url = event.image_url
          }
        },
        // onError
        (event) => {
          if (event.index !== undefined) {
            const img = this.images.find(i => i.index === event.index)
            if (img) {
              img.status = 'error'
              img.error = event.error
            }
          }
        },
        // onFinish
        () => {
          // 检查是否还有失败的图片
          if (!this.hasFailedImages) {
            this.progress.status = 'done'
            this.progress.message = '全部完成'
          }
        },
        // onStreamError
        (error) => {
          const img = this.images.find(i => i.index === index)
          if (img) {
            img.status = 'error'
            img.error = error.message
          }
        }
      )
    },

    /**
     * 重试所有失败的图片
     */
    async retryAllFailed() {
      const failedIndices = this.failedImages.map(img => img.index)
      for (const index of failedIndices) {
        await this.retryFailedImage(index)
      }
    },

    /**
     * 获取任务状态
     */
    async refreshTaskStatus() {
      if (!this.taskId) return

      try {
        const result = await getTaskStatus(this.taskId)
        if (result.success && result.task) {
          const task = result.task
          this.progress.status = task.status === 'completed' ? 'done' :
                                 task.status === 'failed' ? 'error' : 'generating'

          // 更新图片 URL
          task.results.forEach((url, index) => {
            const img = this.images.find(i => i.index === index)
            if (img && url) {
              img.url = url
              img.status = 'done'
            }
          })

          if (task.error) {
            this.error = task.error
          }
        }
      } catch (e) {
        console.error('获取任务状态失败:', e)
      }
    },

    /**
     * 获取图片 URL
     */
    getImageUrl(index: number, thumbnail: boolean = false): string {
      const img = this.images.find(i => i.index === index)
      if (!img || !img.url || !this.taskId) return ''

      // 如果 URL 已经是完整路径，直接返回
      if (img.url.startsWith('http') || img.url.startsWith('/')) {
        return img.url
      }

      return getProductPhotoImageUrl(this.taskId, img.url, thumbnail)
    },

    // ==================== 状态管理 ====================

    /**
     * 返回输入阶段
     */
    backToInput() {
      this.stage = 'input'
    },

    /**
     * 重新生成（保留配置）
     */
    regenerate() {
      this.stage = 'input'
      this.images = []
      this.taskId = null
      this.progress = {
        current: 0,
        total: 0,
        status: 'idle',
        message: ''
      }
      this.error = null
    },

    /**
     * 完全重置
     */
    reset() {
      this.stage = 'input'
      this.modelImage = null
      this.modelImagePreview = null
      this.productImages = []
      this.productImagePreviews = []
      this.config = createDefaultConfig()
      this.progress = {
        current: 0,
        total: 0,
        status: 'idle',
        message: ''
      }
      this.images = []
      this.taskId = null
      this.error = null
      // 清除 localStorage
      localStorage.removeItem(STORAGE_KEY)
    },

    /**
     * 保存状态到 localStorage
     */
    saveToStorage() {
      saveState(this)
    }
  }
})

// ==================== 自动保存 ====================

/**
 * 设置自动保存
 */
export function setupProductPhotoAutoSave() {
  const store = useProductPhotoStore()

  watch(
    () => ({
      stage: store.stage,
      config: store.config,
      progress: store.progress,
      images: store.images,
      taskId: store.taskId,
      selectedProvider: store.selectedProvider
    }),
    () => {
      store.saveToStorage()
    },
    { deep: true }
  )
}
