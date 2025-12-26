/**
 * 模特模板管理 API
 *
 * 包含功能：
 * - 列出所有模板
 * - 保存新模板
 * - 获取模板图片
 * - 更新模板信息
 * - 删除模板
 */

import axios from 'axios'

const API_BASE_URL = '/api'

// ==================== 类型定义 ====================

export interface Template {
  id: string
  name: string
  thumbnail_url: string
  created_at: string
  metadata?: Record<string, unknown>
}

export interface TemplateInfo {
  id: string
  name: string
  created_at: string
  metadata?: Record<string, unknown>
}

export interface SaveTemplateRequest {
  name: string
  image: File | string  // File 或 base64 字符串
  metadata?: Record<string, unknown>
}

export interface UpdateTemplateRequest {
  name?: string
  metadata?: Record<string, unknown>
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

// ==================== API 函数 ====================

/**
 * 列出所有模板
 *
 * @returns 模板列表
 */
export async function listTemplates(): Promise<{
  success: boolean
  templates?: Template[]
  error?: string
}> {
  const response = await axios.get(`${API_BASE_URL}/templates`)
  return response.data
}

/**
 * 保存新模板
 *
 * @param request 保存请求参数
 * @returns 新创建的模板 ID
 */
export async function saveTemplate(request: SaveTemplateRequest): Promise<{
  success: boolean
  template_id?: string
  error?: string
}> {
  // 准备图片数据
  let imageData: string
  if (typeof request.image === 'string') {
    imageData = request.image
  } else {
    imageData = await fileToBase64(request.image)
  }

  const response = await axios.post(`${API_BASE_URL}/templates`, {
    name: request.name,
    image: imageData,
    metadata: request.metadata
  })
  return response.data
}

/**
 * 使用 FormData 保存模板（适用于大文件）
 *
 * @param request 保存请求参数
 * @returns 新创建的模板 ID
 */
export async function saveTemplateWithFormData(request: SaveTemplateRequest): Promise<{
  success: boolean
  template_id?: string
  error?: string
}> {
  const formData = new FormData()
  formData.append('name', request.name)

  if (typeof request.image === 'string') {
    formData.append('image', request.image)
  } else {
    formData.append('image', request.image)
  }

  if (request.metadata) {
    formData.append('metadata', JSON.stringify(request.metadata))
  }

  const response = await axios.post(`${API_BASE_URL}/templates`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

/**
 * 获取模板图片 URL
 *
 * @param templateId 模板 ID
 * @returns 图片 URL
 */
export function getTemplateImageUrl(templateId: string): string {
  return `${API_BASE_URL}/templates/${templateId}`
}

/**
 * 获取模板缩略图 URL
 *
 * @param templateId 模板 ID
 * @returns 缩略图 URL
 */
export function getTemplateThumbnailUrl(templateId: string): string {
  return `${API_BASE_URL}/templates/${templateId}/thumbnail`
}

/**
 * 获取模板图片数据
 *
 * @param templateId 模板 ID
 * @returns 图片 Blob
 */
export async function getTemplateImage(templateId: string): Promise<Blob | null> {
  try {
    const response = await axios.get(`${API_BASE_URL}/templates/${templateId}`, {
      responseType: 'blob'
    })
    return response.data
  } catch (error) {
    console.error('获取模板图片失败:', error)
    return null
  }
}

/**
 * 获取模板信息（不含图片数据）
 *
 * @param templateId 模板 ID
 * @returns 模板信息
 */
export async function getTemplateInfo(templateId: string): Promise<{
  success: boolean
  template?: TemplateInfo
  error?: string
}> {
  const response = await axios.get(`${API_BASE_URL}/templates/${templateId}/info`)
  return response.data
}

/**
 * 更新模板信息
 *
 * @param templateId 模板 ID
 * @param request 更新请求参数
 * @returns 是否成功
 */
export async function updateTemplate(
  templateId: string,
  request: UpdateTemplateRequest
): Promise<{
  success: boolean
  error?: string
}> {
  const response = await axios.put(`${API_BASE_URL}/templates/${templateId}`, request)
  return response.data
}

/**
 * 删除模板
 *
 * @param templateId 模板 ID
 * @returns 是否成功
 */
export async function deleteTemplate(templateId: string): Promise<{
  success: boolean
  error?: string
}> {
  const response = await axios.delete(`${API_BASE_URL}/templates/${templateId}`)
  return response.data
}
