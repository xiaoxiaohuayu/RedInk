/**
 * 模特模板状态管理
 *
 * 管理功能：
 * - 模板列表
 * - 模板选择
 * - 模板 CRUD 操作
 *
 * Requirements: 10.1, 10.2, 10.3
 */

import { defineStore } from 'pinia'
import {
  listTemplates,
  saveTemplate,
  deleteTemplate,
  updateTemplate,
  getTemplateImageUrl,
  getTemplateThumbnailUrl,
  type Template,
  type SaveTemplateRequest,
  type UpdateTemplateRequest
} from '../api/template'

// ==================== 类型定义 ====================

export interface TemplateState {
  // 模板列表
  templates: Template[]

  // 当前选中的模板 ID
  selectedTemplateId: string | null

  // 加载状态
  loading: boolean

  // 错误信息
  error: string | null

  // 是否已加载
  loaded: boolean
}

// ==================== Store 定义 ====================

export const useTemplateStore = defineStore('template', {
  state: (): TemplateState => ({
    templates: [],
    selectedTemplateId: null,
    loading: false,
    error: null,
    loaded: false
  }),

  getters: {
    /**
     * 获取当前选中的模板
     */
    selectedTemplate(): Template | undefined {
      if (!this.selectedTemplateId) return undefined
      return this.templates.find(t => t.id === this.selectedTemplateId)
    },

    /**
     * 模板数量
     */
    templateCount(): number {
      return this.templates.length
    },

    /**
     * 是否有模板
     */
    hasTemplates(): boolean {
      return this.templates.length > 0
    },

    /**
     * 按创建时间排序的模板（最新的在前）
     */
    sortedTemplates(): Template[] {
      return [...this.templates].sort((a, b) => {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
    }
  },

  actions: {
    // ==================== 模板列表 ====================

    /**
     * 加载模板列表
     */
    async loadTemplates() {
      if (this.loading) return

      this.loading = true
      this.error = null

      try {
        const result = await listTemplates()
        if (result.success && result.templates) {
          this.templates = result.templates
          this.loaded = true
        } else {
          this.error = result.error || '加载模板失败'
        }
      } catch (e) {
        this.error = e instanceof Error ? e.message : '加载模板失败'
        console.error('加载模板列表失败:', e)
      } finally {
        this.loading = false
      }
    },

    /**
     * 刷新模板列表
     */
    async refreshTemplates() {
      this.loaded = false
      await this.loadTemplates()
    },

    // ==================== 模板选择 ====================

    /**
     * 选择模板
     */
    selectTemplate(templateId: string | null) {
      this.selectedTemplateId = templateId
    },

    /**
     * 清除选择
     */
    clearSelection() {
      this.selectedTemplateId = null
    },

    // ==================== 模板 CRUD ====================

    /**
     * 保存新模板
     */
    async saveNewTemplate(
      name: string,
      image: File | string,
      metadata?: Record<string, unknown>
    ): Promise<string | null> {
      this.loading = true
      this.error = null

      try {
        const request: SaveTemplateRequest = {
          name,
          image,
          metadata
        }

        const result = await saveTemplate(request)
        if (result.success && result.template_id) {
          // 刷新模板列表
          await this.refreshTemplates()
          return result.template_id
        } else {
          this.error = result.error || '保存模板失败'
          return null
        }
      } catch (e) {
        this.error = e instanceof Error ? e.message : '保存模板失败'
        console.error('保存模板失败:', e)
        return null
      } finally {
        this.loading = false
      }
    },

    /**
     * 更新模板
     */
    async updateExistingTemplate(
      templateId: string,
      updates: UpdateTemplateRequest
    ): Promise<boolean> {
      this.loading = true
      this.error = null

      try {
        const result = await updateTemplate(templateId, updates)
        if (result.success) {
          // 更新本地状态
          const template = this.templates.find(t => t.id === templateId)
          if (template && updates.name) {
            template.name = updates.name
          }
          return true
        } else {
          this.error = result.error || '更新模板失败'
          return false
        }
      } catch (e) {
        this.error = e instanceof Error ? e.message : '更新模板失败'
        console.error('更新模板失败:', e)
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除模板
     */
    async removeTemplate(templateId: string): Promise<boolean> {
      this.loading = true
      this.error = null

      try {
        const result = await deleteTemplate(templateId)
        if (result.success) {
          // 从本地列表中移除
          this.templates = this.templates.filter(t => t.id !== templateId)

          // 如果删除的是当前选中的模板，清除选择
          if (this.selectedTemplateId === templateId) {
            this.selectedTemplateId = null
          }

          return true
        } else {
          this.error = result.error || '删除模板失败'
          return false
        }
      } catch (e) {
        this.error = e instanceof Error ? e.message : '删除模板失败'
        console.error('删除模板失败:', e)
        return false
      } finally {
        this.loading = false
      }
    },

    // ==================== 辅助方法 ====================

    /**
     * 获取模板图片 URL
     */
    getImageUrl(templateId: string): string {
      return getTemplateImageUrl(templateId)
    },

    /**
     * 获取模板缩略图 URL
     */
    getThumbnailUrl(templateId: string): string {
      return getTemplateThumbnailUrl(templateId)
    },

    /**
     * 根据 ID 获取模板
     */
    getTemplateById(templateId: string): Template | undefined {
      return this.templates.find(t => t.id === templateId)
    },

    /**
     * 搜索模板（按名称）
     */
    searchTemplates(query: string): Template[] {
      if (!query.trim()) return this.templates

      const lowerQuery = query.toLowerCase()
      return this.templates.filter(t =>
        t.name.toLowerCase().includes(lowerQuery)
      )
    },

    /**
     * 清除错误
     */
    clearError() {
      this.error = null
    },

    /**
     * 重置状态
     */
    reset() {
      this.templates = []
      this.selectedTemplateId = null
      this.loading = false
      this.error = null
      this.loaded = false
    }
  }
})
