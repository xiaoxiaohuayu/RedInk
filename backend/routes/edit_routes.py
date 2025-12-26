"""
图片编辑 API 路由

包含功能：
- 创建编辑会话
- 应用编辑指令
- 撤销/重做
- 保存编辑
- 取消编辑
"""

import base64
import logging
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO

from backend.services.image_edit import get_image_edit_service
from .utils import log_request, log_error

logger = logging.getLogger(__name__)


def create_edit_blueprint():
    """创建编辑路由蓝图（工厂函数，支持多次调用）"""
    edit_bp = Blueprint('edit', __name__, url_prefix='/edit')

    # ==================== 创建编辑会话 ====================

    @edit_bp.route('/session', methods=['POST'])
    def create_session():
        """
        创建编辑会话

        请求体：
        - task_id: 产品图生成任务 ID（必填）
        - image_index: 要编辑的图片索引（可选，默认 0）

        返回：
        - success: 是否成功
        - session_id: 会话 ID
        - session: 会话信息
        """
        try:
            data = request.get_json() or {}

            log_request('/edit/session [POST]', {
                'task_id': data.get('task_id'),
                'image_index': data.get('image_index', 0)
            })

            task_id = data.get('task_id')
            if not task_id:
                logger.warning("创建编辑会话请求缺少 task_id")
                return jsonify({
                    "success": False,
                    "error": "参数错误：task_id 不能为空。\n请提供任务ID。"
                }), 400

            image_index = int(data.get('image_index', 0))

            logger.info(f"🎨 创建编辑会话: task_id={task_id}, image_index={image_index}")

            service = get_image_edit_service()
            session_id = service.create_edit_session(task_id, image_index)

            if session_id is None:
                logger.warning(f"创建编辑会话失败: task_id={task_id}")
                return jsonify({
                    "success": False,
                    "error": f"创建编辑会话失败。\n可能原因：\n1. 任务不存在\n2. 图片索引无效"
                }), 404

            # 获取会话信息
            session_info = service.get_session_info(session_id)

            logger.info(f"✅ 编辑会话创建成功: session_id={session_id}")

            return jsonify({
                "success": True,
                "session_id": session_id,
                "session": session_info
            }), 201

        except Exception as e:
            log_error('/edit/session [POST]', e)
            return jsonify({
                "success": False,
                "error": f"创建编辑会话失败。\n错误详情: {str(e)}"
            }), 500


    # ==================== 应用编辑 ====================

    @edit_bp.route('/session/<session_id>/apply', methods=['POST'])
    def apply_edit(session_id):
        """
        应用编辑指令

        路径参数：
        - session_id: 会话 ID

        请求体：
        - instruction: 编辑指令（必填，如 "把包包往左移一点", "调亮一些"）
        - mask: 蒙版数据（可选，base64 编码的图片）

        返回：
        - success: 是否成功
        - session: 更新后的会话信息
        - image_url: 编辑后的图片 URL
        """
        try:
            data = request.get_json() or {}

            log_request(f'/edit/session/{session_id}/apply [POST]', {
                'instruction': data.get('instruction'),
                'has_mask': 'mask' in data
            })

            instruction = data.get('instruction')
            if not instruction:
                logger.warning("应用编辑请求缺少 instruction")
                return jsonify({
                    "success": False,
                    "error": "参数错误：instruction 不能为空。\n请提供编辑指令。"
                }), 400

            # 解析蒙版数据
            mask = None
            mask_data = data.get('mask')
            if mask_data:
                mask = _parse_image_data(mask_data)

            logger.info(f"✏️  应用编辑: session_id={session_id}, instruction={instruction}")

            service = get_image_edit_service()
            result = service.apply_edit(session_id, instruction, mask)

            if result is None:
                logger.warning(f"应用编辑失败: session_id={session_id}")
                return jsonify({
                    "success": False,
                    "error": "应用编辑失败。\n可能原因：\n1. 会话不存在或已过期\n2. 编辑操作失败"
                }), 404

            # 获取更新后的会话信息
            session_info = service.get_session_info(session_id)

            logger.info(f"✅ 编辑应用成功: session_id={session_id}")

            return jsonify({
                "success": True,
                "session": session_info,
                "image_url": f"/api/edit/session/{session_id}/current"
            }), 200

        except Exception as e:
            log_error(f'/edit/session/{session_id}/apply [POST]', e)
            return jsonify({
                "success": False,
                "error": f"应用编辑失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 撤销 ====================

    @edit_bp.route('/session/<session_id>/undo', methods=['POST'])
    def undo_edit(session_id):
        """
        撤销编辑

        路径参数：
        - session_id: 会话 ID

        返回：
        - success: 是否成功
        - session: 更新后的会话信息
        - image_url: 撤销后的图片 URL
        """
        try:
            log_request(f'/edit/session/{session_id}/undo [POST]')

            logger.info(f"↩️  撤销编辑: session_id={session_id}")

            service = get_image_edit_service()
            result = service.undo(session_id)

            if result is None:
                logger.warning(f"撤销失败: session_id={session_id}")
                return jsonify({
                    "success": False,
                    "error": "撤销失败。\n可能原因：\n1. 会话不存在或已过期\n2. 已在最早状态，无法撤销"
                }), 400

            # 获取更新后的会话信息
            session_info = service.get_session_info(session_id)

            logger.info(f"✅ 撤销成功: session_id={session_id}")

            return jsonify({
                "success": True,
                "session": session_info,
                "image_url": f"/api/edit/session/{session_id}/current"
            }), 200

        except Exception as e:
            log_error(f'/edit/session/{session_id}/undo [POST]', e)
            return jsonify({
                "success": False,
                "error": f"撤销失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 重做 ====================

    @edit_bp.route('/session/<session_id>/redo', methods=['POST'])
    def redo_edit(session_id):
        """
        重做编辑

        路径参数：
        - session_id: 会话 ID

        返回：
        - success: 是否成功
        - session: 更新后的会话信息
        - image_url: 重做后的图片 URL
        """
        try:
            log_request(f'/edit/session/{session_id}/redo [POST]')

            logger.info(f"↪️  重做编辑: session_id={session_id}")

            service = get_image_edit_service()
            result = service.redo(session_id)

            if result is None:
                logger.warning(f"重做失败: session_id={session_id}")
                return jsonify({
                    "success": False,
                    "error": "重做失败。\n可能原因：\n1. 会话不存在或已过期\n2. 已在最新状态，无法重做"
                }), 400

            # 获取更新后的会话信息
            session_info = service.get_session_info(session_id)

            logger.info(f"✅ 重做成功: session_id={session_id}")

            return jsonify({
                "success": True,
                "session": session_info,
                "image_url": f"/api/edit/session/{session_id}/current"
            }), 200

        except Exception as e:
            log_error(f'/edit/session/{session_id}/redo [POST]', e)
            return jsonify({
                "success": False,
                "error": f"重做失败。\n错误详情: {str(e)}"
            }), 500


    # ==================== 保存编辑 ====================

    @edit_bp.route('/session/<session_id>/save', methods=['POST'])
    def save_edit(session_id):
        """
        保存编辑结果

        路径参数：
        - session_id: 会话 ID

        返回：
        - success: 是否成功
        - image_path: 保存后的图片路径
        """
        try:
            log_request(f'/edit/session/{session_id}/save [POST]')

            logger.info(f"💾 保存编辑: session_id={session_id}")

            service = get_image_edit_service()
            image_path = service.save_edit(session_id)

            if image_path is None:
                logger.warning(f"保存编辑失败: session_id={session_id}")
                return jsonify({
                    "success": False,
                    "error": "保存编辑失败。\n可能原因：\n1. 会话不存在或已过期\n2. 保存操作失败"
                }), 404

            logger.info(f"✅ 编辑保存成功: session_id={session_id}, path={image_path}")

            return jsonify({
                "success": True,
                "image_path": image_path
            }), 200

        except Exception as e:
            log_error(f'/edit/session/{session_id}/save [POST]', e)
            return jsonify({
                "success": False,
                "error": f"保存编辑失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 取消编辑（删除会话） ====================

    @edit_bp.route('/session/<session_id>', methods=['DELETE'])
    def cancel_edit(session_id):
        """
        取消编辑（删除会话）

        路径参数：
        - session_id: 会话 ID

        返回：
        - success: 是否成功
        """
        try:
            log_request(f'/edit/session/{session_id} [DELETE]')

            logger.info(f"🗑️  取消编辑: session_id={session_id}")

            service = get_image_edit_service()
            success = service.cancel_edit(session_id)

            if not success:
                logger.warning(f"取消编辑失败: session_id={session_id}")
                return jsonify({
                    "success": False,
                    "error": f"取消编辑失败。\n会话可能不存在：{session_id}"
                }), 404

            logger.info(f"✅ 编辑取消成功: session_id={session_id}")

            return jsonify({
                "success": True
            }), 200

        except Exception as e:
            log_error(f'/edit/session/{session_id} [DELETE]', e)
            return jsonify({
                "success": False,
                "error": f"取消编辑失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 获取会话信息 ====================

    @edit_bp.route('/session/<session_id>', methods=['GET'])
    def get_session_info(session_id):
        """
        获取会话信息

        路径参数：
        - session_id: 会话 ID

        返回：
        - success: 是否成功
        - session: 会话信息
        """
        try:
            logger.debug(f"获取编辑会话信息: {session_id}")

            service = get_image_edit_service()
            session_info = service.get_session_info(session_id)

            if session_info is None:
                logger.warning(f"会话不存在: {session_id}")
                return jsonify({
                    "success": False,
                    "error": f"会话不存在：{session_id}"
                }), 404

            return jsonify({
                "success": True,
                "session": session_info
            }), 200

        except Exception as e:
            log_error(f'/edit/session/{session_id} [GET]', e)
            return jsonify({
                "success": False,
                "error": f"获取会话信息失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 获取当前编辑图片 ====================

    @edit_bp.route('/session/<session_id>/current', methods=['GET'])
    def get_current_image(session_id):
        """
        获取当前编辑图片

        路径参数：
        - session_id: 会话 ID

        返回：
        - 成功：图片文件
        - 失败：JSON 错误信息
        """
        try:
            logger.debug(f"获取当前编辑图片: {session_id}")

            service = get_image_edit_service()
            image_data = service.get_current_image(session_id)

            if image_data is None:
                logger.warning(f"会话或图片不存在: {session_id}")
                return jsonify({
                    "success": False,
                    "error": f"会话或图片不存在：{session_id}"
                }), 404

            return send_file(
                BytesIO(image_data),
                mimetype='image/png',
                download_name=f"edit_{session_id}.png"
            )

        except Exception as e:
            log_error(f'/edit/session/{session_id}/current [GET]', e)
            return jsonify({
                "success": False,
                "error": f"获取图片失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 获取原始图片 ====================

    @edit_bp.route('/session/<session_id>/original', methods=['GET'])
    def get_original_image(session_id):
        """
        获取原始图片

        路径参数：
        - session_id: 会话 ID

        返回：
        - 成功：图片文件
        - 失败：JSON 错误信息
        """
        try:
            logger.debug(f"获取原始图片: {session_id}")

            service = get_image_edit_service()
            image_data = service.get_original_image(session_id)

            if image_data is None:
                logger.warning(f"会话或图片不存在: {session_id}")
                return jsonify({
                    "success": False,
                    "error": f"会话或图片不存在：{session_id}"
                }), 404

            return send_file(
                BytesIO(image_data),
                mimetype='image/png',
                download_name=f"original_{session_id}.png"
            )

        except Exception as e:
            log_error(f'/edit/session/{session_id}/original [GET]', e)
            return jsonify({
                "success": False,
                "error": f"获取图片失败。\n错误详情: {str(e)}"
            }), 500

    return edit_bp


# ==================== 辅助函数 ====================

def _parse_image_data(image_data) -> bytes:
    """
    解析图片数据（支持 base64 字符串和二进制数据）

    Args:
        image_data: 图片数据（base64 字符串或 bytes）

    Returns:
        图片二进制数据
    """
    if image_data is None:
        return None

    if isinstance(image_data, bytes):
        return image_data

    if isinstance(image_data, str):
        # 移除可能的 data URL 前缀
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        return base64.b64decode(image_data)

    return None
