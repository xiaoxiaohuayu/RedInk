"""
产品图生成相关 API 路由

包含功能：
- 生成产品图（SSE 流式返回）
- 重试生成
- 获取任务状态
- 获取生成的图片
- 获取可用供应商列表
"""

import os
import json
import base64
import logging
from flask import Blueprint, request, jsonify, Response, send_file
from backend.services.product_photo import get_product_photo_service
from .utils import log_request, log_error

logger = logging.getLogger(__name__)


def create_product_photo_blueprint():
    """创建产品图路由蓝图（工厂函数，支持多次调用）"""
    product_photo_bp = Blueprint('product_photo', __name__, url_prefix='/product-photo')

    # ==================== 产品图生成 ====================

    @product_photo_bp.route('/generate', methods=['POST'])
    def generate_product_photo():
        """
        生成产品图（SSE 流式返回）

        请求体（支持 JSON 和 multipart/form-data）：
        - model_image: 模特图（base64 字符串或文件）
        - product_images: 商品图列表（base64 字符串数组或文件）
        - prompt: 用户自定义提示词（可选）
        - aspect_ratio: 宽高比（可选，默认 3:4）
        - style: 风格（可选，默认 自然）
        - background: 背景配置（可选）
        - placement: 商品位置配置（可选）
        - pose: 姿势（可选）
        - variations: 生成变体数量（可选，默认 1，最多 4）
        - provider: 指定供应商（可选）

        返回：
        SSE 事件流，包含以下事件类型：
        - start: 任务开始
        - progress: 生成进度
        - complete: 单张图片完成
        - error: 生成错误
        - finish: 全部完成
        """
        try:
            # 解析请求数据（支持 JSON 和 multipart）
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = _parse_multipart_request(request)
            else:
                data = request.get_json() or {}

            log_request('/product-photo/generate', {
                'has_model_image': 'model_image' in data,
                'product_images_count': len(data.get('product_images', [])),
                'variations': data.get('variations', 1),
                'provider': data.get('provider')
            })

            # 解析模特图
            model_image = _parse_image_data(data.get('model_image'))
            if not model_image:
                logger.warning("产品图生成请求缺少模特图")
                return jsonify({
                    "success": False,
                    "error": "参数错误：model_image 不能为空。\n请提供模特图片。"
                }), 400

            # 解析商品图
            product_images = _parse_image_list(data.get('product_images', []))
            if not product_images:
                logger.warning("产品图生成请求缺少商品图")
                return jsonify({
                    "success": False,
                    "error": "参数错误：product_images 不能为空。\n请提供至少一张商品图片。"
                }), 400

            # 获取其他参数
            prompt = data.get('prompt', '')
            aspect_ratio = data.get('aspect_ratio', '3:4')
            style = data.get('style', '自然')
            background = data.get('background')
            placement = data.get('placement')
            pose = data.get('pose')
            variations = min(int(data.get('variations', 1)), 4)
            provider = data.get('provider')

            logger.info(f"🖼️  开始产品图生成任务: variations={variations}, provider={provider}")

            # 获取服务实例
            service = get_product_photo_service(provider)

            def generate():
                """SSE 事件生成器"""
                for event in service.generate_product_photo(
                    model_image=model_image,
                    product_images=product_images,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    style=style,
                    background=background,
                    placement=placement,
                    pose=pose,
                    variations=variations,
                ):
                    event_type = event["event"]
                    event_data = event["data"]

                    # 格式化为 SSE 格式
                    yield f"event: {event_type}\n"
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                }
            )

        except Exception as e:
            log_error('/product-photo/generate', e)
            error_msg = str(e)
            return jsonify({
                "success": False,
                "error": f"产品图生成异常。\n错误详情: {error_msg}\n建议：检查产品图生成服务配置和后端日志"
            }), 500

    # ==================== 重试生成 ====================

    @product_photo_bp.route('/retry', methods=['POST'])
    def retry_generation():
        """
        重试生成失败的图片

        请求体：
        - task_id: 任务 ID（必填）
        - index: 要重试的图片索引（可选，默认 0）

        返回：
        SSE 事件流
        """
        try:
            data = request.get_json() or {}
            task_id = data.get('task_id')
            index = int(data.get('index', 0))

            log_request('/product-photo/retry', {
                'task_id': task_id,
                'index': index
            })

            if not task_id:
                logger.warning("重试请求缺少 task_id")
                return jsonify({
                    "success": False,
                    "error": "参数错误：task_id 不能为空。\n请提供任务ID。"
                }), 400

            logger.info(f"🔄 重试产品图生成: task_id={task_id}, index={index}")

            service = get_product_photo_service()

            def generate():
                """SSE 事件生成器"""
                for event in service.retry_generation(task_id, index):
                    event_type = event["event"]
                    event_data = event["data"]

                    yield f"event: {event_type}\n"
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                }
            )

        except Exception as e:
            log_error('/product-photo/retry', e)
            error_msg = str(e)
            return jsonify({
                "success": False,
                "error": f"重试产品图生成失败。\n错误详情: {error_msg}"
            }), 500

    # ==================== 任务状态 ====================

    @product_photo_bp.route('/task/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        """
        获取任务状态

        路径参数：
        - task_id: 任务 ID

        返回：
        - success: 是否成功
        - task: 任务状态信息
        """
        try:
            logger.debug(f"获取产品图任务状态: {task_id}")

            service = get_product_photo_service()
            status = service.get_task_status(task_id)

            if status is None:
                return jsonify({
                    "success": False,
                    "error": f"任务不存在：{task_id}\n可能原因：\n1. 任务ID错误\n2. 任务已过期或被清理\n3. 服务重启导致状态丢失"
                }), 404

            return jsonify({
                "success": True,
                "task": status
            }), 200

        except Exception as e:
            log_error('/product-photo/task', e)
            error_msg = str(e)
            return jsonify({
                "success": False,
                "error": f"获取任务状态失败。\n错误详情: {error_msg}"
            }), 500

    # ==================== 图片获取 ====================

    @product_photo_bp.route('/images/<task_id>/<filename>', methods=['GET'])
    def get_image(task_id, filename):
        """
        获取生成的图片

        路径参数：
        - task_id: 任务 ID
        - filename: 文件名

        查询参数：
        - thumbnail: 是否返回缩略图（默认 true）

        返回：
        - 成功：图片文件
        - 失败：JSON 错误信息
        """
        try:
            logger.debug(f"获取产品图: {task_id}/{filename}")

            # 检查是否请求缩略图
            thumbnail = request.args.get('thumbnail', 'true').lower() == 'true'

            service = get_product_photo_service()

            # 尝试获取缩略图
            if thumbnail:
                thumb_filename = f"thumb_{filename}"
                thumb_path = service.get_image_path(task_id, thumb_filename)
                if thumb_path:
                    return send_file(thumb_path, mimetype='image/png')

            # 获取原图
            filepath = service.get_image_path(task_id, filename)

            if not filepath:
                return jsonify({
                    "success": False,
                    "error": f"图片不存在：{task_id}/{filename}"
                }), 404

            return send_file(filepath, mimetype='image/png')

        except Exception as e:
            log_error('/product-photo/images', e)
            error_msg = str(e)
            return jsonify({
                "success": False,
                "error": f"获取图片失败: {error_msg}"
            }), 500

    # ==================== 供应商列表 ====================

    @product_photo_bp.route('/providers', methods=['GET'])
    def get_providers():
        """
        获取可用的产品图生成供应商列表

        返回：
        - success: 是否成功
        - providers: 供应商列表，包含名称和支持的功能
        """
        try:
            logger.debug("获取产品图供应商列表")

            service = get_product_photo_service()
            providers = service.get_providers()

            return jsonify({
                "success": True,
                "providers": providers
            }), 200

        except Exception as e:
            log_error('/product-photo/providers', e)
            error_msg = str(e)
            return jsonify({
                "success": False,
                "error": f"获取供应商列表失败。\n错误详情: {error_msg}"
            }), 500

    # ==================== 健康检查 ====================

    @product_photo_bp.route('/health', methods=['GET'])
    def health_check():
        """
        健康检查接口

        返回：
        - success: 服务是否正常
        - message: 状态消息
        """
        return jsonify({
            "success": True,
            "message": "产品图生成服务正常运行"
        }), 200

    return product_photo_bp


# ==================== 辅助函数 ====================

def _parse_multipart_request(req) -> dict:
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
        # 尝试解析 JSON 字符串
        if key in ['background', 'placement']:
            try:
                data[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                data[key] = value
        elif key == 'variations':
            data[key] = int(value)
        else:
            data[key] = value

    # 解析文件
    if 'model_image' in req.files:
        data['model_image'] = req.files['model_image'].read()

    # 解析多个商品图文件
    product_images = []
    if 'product_images' in req.files:
        files = req.files.getlist('product_images')
        for f in files:
            product_images.append(f.read())
    # 也支持 product_images[0], product_images[1] 格式
    for key in req.files:
        if key.startswith('product_images['):
            product_images.append(req.files[key].read())

    if product_images:
        data['product_images'] = product_images

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


def _parse_image_list(images) -> list:
    """
    解析图片列表

    Args:
        images: 图片数据列表

    Returns:
        图片二进制数据列表
    """
    if not images:
        return []

    result = []
    for img in images:
        parsed = _parse_image_data(img)
        if parsed:
            result.append(parsed)

    return result
