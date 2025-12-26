"""
模特模板管理 API 路由

包含功能：
- 列出所有模板
- 保存新模板
- 获取模板图片
- 更新模板信息
- 删除模板
"""

import base64
import logging
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from dataclasses import asdict

from backend.services.template import get_template_service
from .utils import log_request, log_error

logger = logging.getLogger(__name__)


def create_template_blueprint():
    """创建模板路由蓝图（工厂函数，支持多次调用）"""
    template_bp = Blueprint('templates', __name__, url_prefix='/templates')

    # ==================== 列出所有模板 ====================

    @template_bp.route('', methods=['GET'])
    def list_templates():
        """
        列出所有模板

        返回：
        - success: 是否成功
        - templates: 模板列表，每个模板包含 id, name, thumbnail_url, created_at
        """
        try:
            log_request('/templates [GET]')

            service = get_template_service()
            templates = service.list_templates()

            # 转换为字典列表
            templates_data = [asdict(t) for t in templates]

            logger.info(f"📋 获取模板列表: 共 {len(templates_data)} 个模板")

            return jsonify({
                "success": True,
                "templates": templates_data
            }), 200

        except Exception as e:
            log_error('/templates [GET]', e)
            return jsonify({
                "success": False,
                "error": f"获取模板列表失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 保存新模板 ====================

    @template_bp.route('', methods=['POST'])
    def save_template():
        """
        保存新模板

        请求体（支持 JSON 和 multipart/form-data）：
        - name: 模板名称（必填）
        - image: 图片数据（base64 字符串或文件，必填）
        - metadata: 可选的元数据（JSON 对象）

        返回：
        - success: 是否成功
        - template_id: 新创建的模板 ID
        """
        try:
            # 解析请求数据
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = _parse_multipart_template_request(request)
            else:
                data = request.get_json() or {}

            log_request('/templates [POST]', {
                'name': data.get('name'),
                'has_image': 'image' in data
            })

            # 验证必填字段
            name = data.get('name')
            if not name:
                logger.warning("保存模板请求缺少名称")
                return jsonify({
                    "success": False,
                    "error": "参数错误：name 不能为空。\n请提供模板名称。"
                }), 400

            # 解析图片数据
            image = _parse_image_data(data.get('image'))
            if not image:
                logger.warning("保存模板请求缺少图片")
                return jsonify({
                    "success": False,
                    "error": "参数错误：image 不能为空。\n请提供模板图片。"
                }), 400

            # 获取可选的元数据
            metadata = data.get('metadata')

            logger.info(f"💾 保存模板: name={name}")

            service = get_template_service()
            template_id = service.save_template(name, image, metadata)

            logger.info(f"✅ 模板保存成功: id={template_id}")

            return jsonify({
                "success": True,
                "template_id": template_id
            }), 201

        except Exception as e:
            log_error('/templates [POST]', e)
            return jsonify({
                "success": False,
                "error": f"保存模板失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 获取模板图片 ====================

    @template_bp.route('/<template_id>', methods=['GET'])
    def get_template(template_id):
        """
        获取模板图片

        路径参数：
        - template_id: 模板 ID

        返回：
        - 成功：图片文件
        - 失败：JSON 错误信息
        """
        try:
            logger.debug(f"获取模板图片: {template_id}")

            service = get_template_service()
            image_data = service.get_template(template_id)

            if image_data is None:
                logger.warning(f"模板不存在: {template_id}")
                return jsonify({
                    "success": False,
                    "error": f"模板不存在：{template_id}"
                }), 404

            # 返回图片
            return send_file(
                BytesIO(image_data),
                mimetype='image/png',
                download_name=f"{template_id}.png"
            )

        except Exception as e:
            log_error(f'/templates/{template_id} [GET]', e)
            return jsonify({
                "success": False,
                "error": f"获取模板失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 获取模板缩略图 ====================

    @template_bp.route('/<template_id>/thumbnail', methods=['GET'])
    def get_template_thumbnail(template_id):
        """
        获取模板缩略图

        路径参数：
        - template_id: 模板 ID

        返回：
        - 成功：缩略图文件
        - 失败：JSON 错误信息
        """
        try:
            logger.debug(f"获取模板缩略图: {template_id}")

            service = get_template_service()
            thumbnail_data = service.get_template_thumbnail(template_id)

            if thumbnail_data is None:
                logger.warning(f"模板不存在: {template_id}")
                return jsonify({
                    "success": False,
                    "error": f"模板不存在：{template_id}"
                }), 404

            # 返回缩略图
            return send_file(
                BytesIO(thumbnail_data),
                mimetype='image/png',
                download_name=f"{template_id}_thumb.png"
            )

        except Exception as e:
            log_error(f'/templates/{template_id}/thumbnail [GET]', e)
            return jsonify({
                "success": False,
                "error": f"获取模板缩略图失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 更新模板信息 ====================

    @template_bp.route('/<template_id>', methods=['PUT'])
    def update_template(template_id):
        """
        更新模板信息

        路径参数：
        - template_id: 模板 ID

        请求体：
        - name: 新名称（可选）
        - metadata: 新元数据（可选）

        返回：
        - success: 是否成功
        """
        try:
            data = request.get_json() or {}

            log_request(f'/templates/{template_id} [PUT]', {
                'name': data.get('name'),
                'has_metadata': 'metadata' in data
            })

            name = data.get('name')
            metadata = data.get('metadata')

            # 至少需要一个更新字段
            if name is None and metadata is None:
                logger.warning("更新模板请求没有提供任何更新字段")
                return jsonify({
                    "success": False,
                    "error": "参数错误：至少需要提供 name 或 metadata 字段。"
                }), 400

            logger.info(f"📝 更新模板: id={template_id}, name={name}")

            service = get_template_service()
            success = service.update_template(template_id, name=name, metadata=metadata)

            if not success:
                logger.warning(f"模板不存在或更新失败: {template_id}")
                return jsonify({
                    "success": False,
                    "error": f"模板不存在或更新失败：{template_id}"
                }), 404

            logger.info(f"✅ 模板更新成功: id={template_id}")

            return jsonify({
                "success": True
            }), 200

        except Exception as e:
            log_error(f'/templates/{template_id} [PUT]', e)
            return jsonify({
                "success": False,
                "error": f"更新模板失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 删除模板 ====================

    @template_bp.route('/<template_id>', methods=['DELETE'])
    def delete_template(template_id):
        """
        删除模板

        路径参数：
        - template_id: 模板 ID

        返回：
        - success: 是否成功
        """
        try:
            log_request(f'/templates/{template_id} [DELETE]')

            logger.info(f"🗑️  删除模板: id={template_id}")

            service = get_template_service()
            success = service.delete_template(template_id)

            if not success:
                logger.warning(f"模板不存在: {template_id}")
                return jsonify({
                    "success": False,
                    "error": f"模板不存在：{template_id}"
                }), 404

            logger.info(f"✅ 模板删除成功: id={template_id}")

            return jsonify({
                "success": True
            }), 200

        except Exception as e:
            log_error(f'/templates/{template_id} [DELETE]', e)
            return jsonify({
                "success": False,
                "error": f"删除模板失败。\n错误详情: {str(e)}"
            }), 500

    # ==================== 获取模板信息 ====================

    @template_bp.route('/<template_id>/info', methods=['GET'])
    def get_template_info(template_id):
        """
        获取模板信息（不含图片数据）

        路径参数：
        - template_id: 模板 ID

        返回：
        - success: 是否成功
        - template: 模板信息
        """
        try:
            logger.debug(f"获取模板信息: {template_id}")

            service = get_template_service()
            info = service.get_template_info(template_id)

            if info is None:
                logger.warning(f"模板不存在: {template_id}")
                return jsonify({
                    "success": False,
                    "error": f"模板不存在：{template_id}"
                }), 404

            return jsonify({
                "success": True,
                "template": info
            }), 200

        except Exception as e:
            log_error(f'/templates/{template_id}/info [GET]', e)
            return jsonify({
                "success": False,
                "error": f"获取模板信息失败。\n错误详情: {str(e)}"
            }), 500

    return template_bp


# ==================== 辅助函数 ====================

def _parse_multipart_template_request(req) -> dict:
    """
    解析 multipart/form-data 请求

    Args:
        req: Flask request 对象

    Returns:
        解析后的数据字典
    """
    data = {}

    # 解析表单字段
    for key in req.form:
        value = req.form[key]
        # 尝试解析 JSON 字符串（用于 metadata）
        if key == 'metadata':
            try:
                import json
                data[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                data[key] = value
        else:
            data[key] = value

    # 解析文件
    if 'image' in req.files:
        data['image'] = req.files['image'].read()

    return data


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
