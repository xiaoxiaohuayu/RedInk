/**
 * 图片编辑 API
 *
 * 包含功能：
 * - 创建编辑会话
 * - 应用编辑指令
 * - 撤销/重做
 * - 保存编辑
 * - 取消编辑
 */

import axios from 'axios'

const API_BASE_URL = '/api'

// ==================== 类型定义 ====================

export interface EditSession {
  id: string
  task_id: string
  can_undo: boolean
  can_redo: boolean
  history_count: number
  history_index: number
  created_at: string
}

export interface CreateSessionRequest {
  taskId: string
  imageIndex?: number  // 默认 0
}

export interface ApplyEditRequest {
  instruction: string
  mask?: string  // base64 编码的蒙版图片
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
 * 将 canvas 转换为 base64 字符串
 */
export function canvasToBase64(canvas: HTMLCanvasElement): string {
  return canvas.toDataURL('image/png')
}

// ==================== API 函数 ====================

/**
 * 创建编辑会话
 *
 * @param request 创建请求参数
 * @returns 会话信息
 */
export async function createEditSession(request: CreateSessionRequest): Promise<{
  success: boolean
  session_id?: string
  session?: EditSession
  error?: string
}> {
  const response = await axios.post(`${API_BASE_URL}/edit/session`, {
    task_id: request.taskId,
    image_index: request.imageIndex ?? 0
  })
  return response.data
}

/**
 * 获取会话信息
 *
 * @param sessionId 会话 ID
 * @returns 会话信息
 */
export async function getSessionInfo(sessionId: string): Promise<{
  success: boolean
  session?: EditSession
  error?: string
}> {
  const response = await axios.get(`${API_BASE_URL}/edit/session/${sessionId}`)
  return response.data
}

/**
 * 应用编辑指令
 *
 * @param sessionId 会话 ID
 * @param request 编辑请求参数
 * @returns 编辑结果
 */
export async function applyEdit(
  sessionId: string,
  request: ApplyEditRequest
): Promise<{
  success: boolean
  session?: EditSession
  image_url?: string
  error?: string
}> {
  const response = await axios.post(`${API_BASE_URL}/edit/session/${sessionId}/apply`, {
    instruction: request.instruction,
    mask: request.mask
  })
  return response.data
}

/**
 * 应用编辑指令（使用 File 作为蒙版）
 *
 * @param sessionId 会话 ID
 * @param instruction 编辑指令
 * @param maskFile 蒙版文件
 * @returns 编辑结果
 */
export async function applyEditWithMaskFile(
  sessionId: string,
  instruction: string,
  maskFile?: File
): Promise<{
  success: boolean
  session?: EditSession
  image_url?: string
  error?: string
}> {
  let mask: string | undefined
  if (maskFile) {
    mask = await fileToBase64(maskFile)
  }

  return applyEdit(sessionId, { instruction, mask })
}

/**
 * 应用编辑指令（使用 Canvas 作为蒙版）
 *
 * @param sessionId 会话 ID
 * @param instruction 编辑指令
 * @param maskCanvas 蒙版 Canvas
 * @returns 编辑结果
 */
export async function applyEditWithMaskCanvas(
  sessionId: string,
  instruction: string,
  maskCanvas?: HTMLCanvasElement
): Promise<{
  success: boolean
  session?: EditSession
  image_url?: string
  error?: string
}> {
  let mask: string | undefined
  if (maskCanvas) {
    mask = canvasToBase64(maskCanvas)
  }

  return applyEdit(sessionId, { instruction, mask })
}

/**
 * 撤销编辑
 *
 * @param sessionId 会话 ID
 * @returns 撤销结果
 */
export async function undoEdit(sessionId: string): Promise<{
  success: boolean
  session?: EditSession
  image_url?: string
  error?: string
}> {
  const response = await axios.post(`${API_BASE_URL}/edit/session/${sessionId}/undo`)
  return response.data
}

/**
 * 重做编辑
 *
 * @param sessionId 会话 ID
 * @returns 重做结果
 */
export async function redoEdit(sessionId: string): Promise<{
  success: boolean
  session?: EditSession
  image_url?: string
  error?: string
}> {
  const response = await axios.post(`${API_BASE_URL}/edit/session/${sessionId}/redo`)
  return response.data
}

/**
 * 保存编辑结果
 *
 * @param sessionId 会话 ID
 * @returns 保存结果
 */
export async function saveEdit(sessionId: string): Promise<{
  success: boolean
  image_path?: string
  error?: string
}> {
  const response = await axios.post(`${API_BASE_URL}/edit/session/${sessionId}/save`)
  return response.data
}

/**
 * 取消编辑（删除会话）
 *
 * @param sessionId 会话 ID
 * @returns 是否成功
 */
export async function cancelEdit(sessionId: string): Promise<{
  success: boolean
  error?: string
}> {
  const response = await axios.delete(`${API_BASE_URL}/edit/session/${sessionId}`)
  return response.data
}

/**
 * 获取当前编辑图片 URL
 *
 * @param sessionId 会话 ID
 * @returns 图片 URL
 */
export function getCurrentImageUrl(sessionId: string): string {
  return `${API_BASE_URL}/edit/session/${sessionId}/current`
}

/**
 * 获取原始图片 URL
 *
 * @param sessionId 会话 ID
 * @returns 图片 URL
 */
export function getOriginalImageUrl(sessionId: string): string {
  return `${API_BASE_URL}/edit/session/${sessionId}/original`
}

/**
 * 获取当前编辑图片数据
 *
 * @param sessionId 会话 ID
 * @returns 图片 Blob
 */
export async function getCurrentImage(sessionId: string): Promise<Blob | null> {
  try {
    const response = await axios.get(`${API_BASE_URL}/edit/session/${sessionId}/current`, {
      responseType: 'blob'
    })
    return response.data
  } catch (error) {
    console.error('获取当前编辑图片失败:', error)
    return null
  }
}

/**
 * 获取原始图片数据
 *
 * @param sessionId 会话 ID
 * @returns 图片 Blob
 */
export async function getOriginalImage(sessionId: string): Promise<Blob | null> {
  try {
    const response = await axios.get(`${API_BASE_URL}/edit/session/${sessionId}/original`, {
      responseType: 'blob'
    })
    return response.data
  } catch (error) {
    console.error('获取原始图片失败:', error)
    return null
  }
}
