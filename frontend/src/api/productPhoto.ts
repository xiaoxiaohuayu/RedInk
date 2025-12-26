/**
 * 产品图生成 API
 *
 * 包含功能：
 * - 生成产品图（SSE 流式返回）
 * - 重试生成
 * - 获取任务状态
 * - 获取可用供应商列表
 */

const API_BASE_URL = '/api'

// ==================== 类型定义 ====================

export interface BackgroundConfig {
  type: 'preset' | 'custom' | 'description' | 'original'
  preset?: string  // 街拍、室内、商场、户外、纯色
  customImage?: string  // base64 编码的图片
  description?: string
}

export interface PlacementConfig {
  position: 'auto' | 'left_hand' | 'right_hand' | 'shoulder' | 'chest' | 'waist'
  customInstruction?: string
}

export interface GenerateProductPhotoRequest {
  modelImage: File | string  // File 或 base64 字符串
  productImages: (File | string)[]  // File 数组或 base64 字符串数组
  prompt?: string
  aspectRatio?: string  // 默认 3:4
  style?: string  // 默认 自然
  background?: BackgroundConfig
  placement?: PlacementConfig
  pose?: string
  variations?: number  // 默认 1，最多 4
  provider?: string  // 指定供应商
}

export interface ProviderInfo {
  name: string
  displayName: string
  features: {
    backgroundChange: boolean
    poseChange: boolean
    multiProduct: boolean
    inpainting: boolean
  }
}

export interface TaskStatus {
  id: string
  status: 'pending' | 'generating' | 'completed' | 'failed'
  provider: string
  results: string[]
  error?: string
  progress?: number
}

// SSE 事件类型
export interface ProductPhotoStartEvent {
  task_id: string
  message: string
}

export interface ProductPhotoProgressEvent {
  task_id: string
  current: number
  total: number
  message?: string
}

export interface ProductPhotoCompleteEvent {
  task_id: string
  index: number
  image_url: string
}

export interface ProductPhotoErrorEvent {
  task_id: string
  index?: number
  error: string
}

export interface ProductPhotoFinishEvent {
  success: boolean
  task_id: string
  images: string[]
  total: number
  completed: number
  failed: number
}

// ==================== 辅助函数 ====================

/**
 * 将 File 转换为 base64 字符串
 */
async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/**
 * 准备图片数据（转换为 base64）
 */
async function prepareImageData(image: File | string): Promise<string> {
  if (typeof image === 'string') {
    return image
  }
  return fileToBase64(image)
}

/**
 * 准备图片列表数据
 */
async function prepareImageList(images: (File | string)[]): Promise<string[]> {
  return Promise.all(images.map(prepareImageData))
}

// ==================== API 函数 ====================

/**
 * 生成产品图（SSE 流式返回）
 *
 * @param request 生成请求参数
 * @param onStart 任务开始回调
 * @param onProgress 进度回调
 * @param onComplete 单张图片完成回调
 * @param onError 错误回调
 * @param onFinish 全部完成回调
 * @param onStreamError 流错误回调
 */
export async function generateProductPhoto(
  request: GenerateProductPhotoRequest,
  onStart: (event: ProductPhotoStartEvent) => void,
  onProgress: (event: ProductPhotoProgressEvent) => void,
  onComplete: (event: ProductPhotoCompleteEvent) => void,
  onError: (event: ProductPhotoErrorEvent) => void,
  onFinish: (event: ProductPhotoFinishEvent) => void,
  onStreamError: (error: Error) => void
): Promise<void> {
  try {
    // 准备请求数据
    const modelImage = await prepareImageData(request.modelImage)
    const productImages = await prepareImageList(request.productImages)

    // 准备背景配置
    let background = request.background
    if (background?.customImage && typeof background.customImage !== 'string') {
      background = {
        ...background,
        customImage: await fileToBase64(background.customImage as unknown as File)
      }
    }

    const requestBody = {
      model_image: modelImage,
      product_images: productImages,
      prompt: request.prompt || '',
      aspect_ratio: request.aspectRatio || '3:4',
      style: request.style || '自然',
      background: background,
      placement: request.placement,
      pose: request.pose,
      variations: request.variations || 1,
      provider: request.provider
    }

    const response = await fetch(`${API_BASE_URL}/product-photo/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim()) continue

        const eventMatch = line.match(/^event: (.+)$/m)
        const dataMatch = line.match(/^data: (.+)$/m)

        if (!eventMatch || !dataMatch) continue

        const eventType = eventMatch[1].trim()
        const eventData = dataMatch[1].trim()

        try {
          const data = JSON.parse(eventData)

          switch (eventType) {
            case 'start':
              onStart(data)
              break
            case 'progress':
              onProgress(data)
              break
            case 'complete':
              onComplete(data)
              break
            case 'error':
              onError(data)
              break
            case 'finish':
              onFinish(data)
              break
          }
        } catch (e) {
          console.error('解析 SSE 数据失败:', e)
        }
      }
    }
  } catch (error) {
    onStreamError(error as Error)
  }
}

/**
 * 重试生成失败的图片（SSE 流式返回）
 *
 * @param taskId 任务 ID
 * @param index 要重试的图片索引
 * @param onStart 任务开始回调
 * @param onProgress 进度回调
 * @param onComplete 完成回调
 * @param onError 错误回调
 * @param onFinish 全部完成回调
 * @param onStreamError 流错误回调
 */
export async function retryGeneration(
  taskId: string,
  index: number = 0,
  onStart: (event: ProductPhotoStartEvent) => void,
  onProgress: (event: ProductPhotoProgressEvent) => void,
  onComplete: (event: ProductPhotoCompleteEvent) => void,
  onError: (event: ProductPhotoErrorEvent) => void,
  onFinish: (event: ProductPhotoFinishEvent) => void,
  onStreamError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/product-photo/retry`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId,
        index
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim()) continue

        const eventMatch = line.match(/^event: (.+)$/m)
        const dataMatch = line.match(/^data: (.+)$/m)

        if (!eventMatch || !dataMatch) continue

        const eventType = eventMatch[1].trim()
        const eventData = dataMatch[1].trim()

        try {
          const data = JSON.parse(eventData)

          switch (eventType) {
            case 'start':
              onStart(data)
              break
            case 'progress':
              onProgress(data)
              break
            case 'complete':
              onComplete(data)
              break
            case 'error':
              onError(data)
              break
            case 'finish':
              onFinish(data)
              break
          }
        } catch (e) {
          console.error('解析 SSE 数据失败:', e)
        }
      }
    }
  } catch (error) {
    onStreamError(error as Error)
  }
}

/**
 * 获取任务状态
 *
 * @param taskId 任务 ID
 * @returns 任务状态信息
 */
export async function getTaskStatus(taskId: string): Promise<{
  success: boolean
  task?: TaskStatus
  error?: string
}> {
  const response = await fetch(`${API_BASE_URL}/product-photo/task/${taskId}`)
  return response.json()
}

/**
 * 获取生成的图片 URL
 *
 * @param taskId 任务 ID
 * @param filename 文件名
 * @param thumbnail 是否返回缩略图（默认 true）
 * @returns 图片 URL
 */
export function getProductPhotoImageUrl(
  taskId: string,
  filename: string,
  thumbnail: boolean = true
): string {
  const thumbParam = thumbnail ? '?thumbnail=true' : '?thumbnail=false'
  return `${API_BASE_URL}/product-photo/images/${taskId}/${filename}${thumbParam}`
}

/**
 * 获取可用的产品图生成供应商列表
 *
 * @returns 供应商列表
 */
export async function getProviders(): Promise<{
  success: boolean
  providers?: ProviderInfo[]
  error?: string
}> {
  const response = await fetch(`${API_BASE_URL}/product-photo/providers`)
  return response.json()
}

/**
 * 健康检查
 *
 * @returns 服务状态
 */
export async function healthCheck(): Promise<{
  success: boolean
  message?: string
}> {
  const response = await fetch(`${API_BASE_URL}/product-photo/health`)
  return response.json()
}
