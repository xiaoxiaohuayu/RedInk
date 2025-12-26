# Design Document: Product Photo Generator

## Overview

产品图生成器是红墨 AI 图文生成器的新功能模块，允许用户上传模特图和商品图，通过 AI 合成专业的产品展示图。

**关键设计决策：**
- 产品图生成与现有小红书图文生成使用**独立的生成器体系**
- 每个 AI 供应商一个独立文件，便于维护和扩展
- 供应商配置独立于现有的 `image_providers.yaml`

核心能力：
- 模特 + 商品图合成
- 多种商品类型智能定位
- 背景场景切换
- 模特模板管理
- 姿势生成
- 二次编辑（局部修改、撤销/重做）

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                         │
├─────────────────────────────────────────────────────────────────┤
│  ProductPhotoView.vue  │  EditView.vue  │  TemplateView.vue     │
│         ↓                     ↓                  ↓              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  productPhotoStore.ts  │  templateStore.ts                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  productPhotoApi.ts                                         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                               ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (Flask)                          │
├─────────────────────────────────────────────────────────────────┤
│  Routes                                                         │
│  ├── product_photo_routes.py  (产品图生成 API)                   │
│  ├── template_routes.py       (模特模板管理 API)                 │
│  └── edit_routes.py           (图片编辑 API)                     │
│                              ↓                                  │
│  Services                                                       │
│  ├── product_photo.py         (产品图生成服务)                   │
│  ├── template.py              (模板管理服务)                     │
│  └── image_edit.py            (图片编辑服务)                     │
│                              ↓                                  │
│  Product Photo Generators (独立体系，与现有 generators 分离)      │
│  ├── product_generators/                                        │
│  │   ├── __init__.py                                           │
│  │   ├── base.py              (产品图生成器基类)                 │
│  │   ├── factory.py           (工厂类)                          │
│  │   ├── kolors_virtual_tryon.py  (可灵换装 API)                │
│  │   ├── kling_ai.py          (Kling AI)                       │
│  │   ├── runway_ml.py         (Runway ML)                      │
│  │   ├── stable_diffusion.py  (Stable Diffusion Inpainting)    │
│  │   └── ... (其他供应商)                                       │
│  │                                                              │
│  └── 现有 generators/ (小红书图文生成，保持不变)                  │
│      ├── google_genai.py                                        │
│      ├── image_api.py                                           │
│      └── openai_compatible.py                                   │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│  Configuration                                                  │
│  ├── image_providers.yaml          (现有，小红书图文生成)         │
│  └── product_photo_providers.yaml  (新增，产品图生成专用)         │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│  Storage                                                        │
│  ├── history/{task_id}/       (生成的图片)                       │
│  ├── templates/               (模特模板)                         │
│  └── edit_sessions/           (编辑会话临时文件)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend Components

#### 1. Product Photo Generator Base Class (`backend/product_generators/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class ProductPhotoRequest:
    """产品图生成请求"""
    model_image: bytes
    product_images: List[bytes]
    prompt: str = ""
    aspect_ratio: str = "3:4"
    style: str = "自然"
    background: Optional['BackgroundConfig'] = None
    placement: Optional['PlacementConfig'] = None
    pose: Optional[str] = None

@dataclass
class ProductPhotoResult:
    """产品图生成结果"""
    success: bool
    image_data: Optional[bytes] = None
    error: Optional[str] = None

class ProductPhotoGeneratorBase(ABC):
    """产品图生成器抽象基类"""
    
    # 供应商名称
    PROVIDER_NAME: str = "base"
    
    # 供应商支持的功能
    SUPPORTS_BACKGROUND_CHANGE: bool = False
    SUPPORTS_POSE_CHANGE: bool = False
    SUPPORTS_MULTI_PRODUCT: bool = False
    SUPPORTS_INPAINTING: bool = False
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
    
    @abstractmethod
    def generate(self, request: ProductPhotoRequest) -> ProductPhotoResult:
        """生成产品图"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass
    
    def supports_feature(self, feature: str) -> bool:
        """检查是否支持某功能"""
        feature_map = {
            'background_change': self.SUPPORTS_BACKGROUND_CHANGE,
            'pose_change': self.SUPPORTS_POSE_CHANGE,
            'multi_product': self.SUPPORTS_MULTI_PRODUCT,
            'inpainting': self.SUPPORTS_INPAINTING,
        }
        return feature_map.get(feature, False)
```

#### 2. Example Provider Implementation (`backend/product_generators/kolors_virtual_tryon.py`)

```python
"""可灵虚拟换装 API"""
import requests
from typing import Dict, Any
from .base import ProductPhotoGeneratorBase, ProductPhotoRequest, ProductPhotoResult

class KolorsVirtualTryonGenerator(ProductPhotoGeneratorBase):
    """可灵虚拟换装生成器"""
    
    PROVIDER_NAME = "kolors_virtual_tryon"
    SUPPORTS_BACKGROUND_CHANGE = False
    SUPPORTS_POSE_CHANGE = False
    SUPPORTS_MULTI_PRODUCT = False  # 一次只能换一件
    SUPPORTS_INPAINTING = False
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get('model', 'kolors-virtual-try-on')
        # 可灵特有的参数
        self.category = config.get('category', 'upper_body')  # upper_body, lower_body, full_body
    
    def generate(self, request: ProductPhotoRequest) -> ProductPhotoResult:
        """调用可灵换装 API"""
        # 可灵 API 特有的请求格式
        payload = {
            "model": self.model,
            "human_image": self._encode_image(request.model_image),
            "cloth_image": self._encode_image(request.product_images[0]),
            "category": self.category,
        }
        # ... API 调用逻辑
        pass
    
    def validate_config(self) -> bool:
        return bool(self.api_key and self.base_url)
```

#### 3. Generator Factory (`backend/product_generators/factory.py`)

```python
"""产品图生成器工厂"""
from typing import Dict, Any
from .base import ProductPhotoGeneratorBase

class ProductPhotoGeneratorFactory:
    """产品图生成器工厂"""
    
    GENERATORS = {}
    
    @classmethod
    def register(cls, name: str, generator_class: type):
        """注册生成器"""
        cls.GENERATORS[name] = generator_class
    
    @classmethod
    def create(cls, provider: str, config: Dict[str, Any]) -> ProductPhotoGeneratorBase:
        """创建生成器实例"""
        if provider not in cls.GENERATORS:
            raise ValueError(f"不支持的产品图生成供应商: {provider}")
        return cls.GENERATORS[provider](config)

# 自动注册所有生成器
from .kolors_virtual_tryon import KolorsVirtualTryonGenerator
from .kling_ai import KlingAIGenerator
# ... 其他导入

ProductPhotoGeneratorFactory.register('kolors_virtual_tryon', KolorsVirtualTryonGenerator)
ProductPhotoGeneratorFactory.register('kling_ai', KlingAIGenerator)
# ... 其他注册
```

#### 4. ProductPhotoService (`backend/services/product_photo.py`)

```python
class ProductPhotoService:
    """产品图生成服务"""
    
    def __init__(self, provider_name: str = None):
        # 从 product_photo_providers.yaml 加载配置
        config = Config.load_product_photo_providers_config()
        if provider_name is None:
            provider_name = config.get('active_provider')
        
        provider_config = config['providers'][provider_name]
        provider_type = provider_config.get('type', provider_name)
        
        self.generator = ProductPhotoGeneratorFactory.create(
            provider_type, provider_config
        )
    
    def generate_product_photo(
        self,
        model_image: bytes,
        product_images: List[bytes],
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """生成产品图（SSE 流式返回）"""
        pass
```

#### 5. TemplateService (`backend/services/template.py`)

```python
class TemplateService:
    """模特模板管理服务"""
    
    def save_template(self, name: str, image: bytes, metadata: Optional[Dict] = None) -> str:
        """保存模板，返回模板 ID"""
        pass
    
    def list_templates(self) -> List[TemplateInfo]:
        """列出所有模板"""
        pass
    
    def get_template(self, template_id: str) -> Optional[bytes]:
        """获取模板图片"""
        pass
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        pass
    
    def update_template(self, template_id: str, name: Optional[str] = None) -> bool:
        """更新模板信息"""
        pass
```

#### 6. ImageEditService (`backend/services/image_edit.py`)

```python
class ImageEditService:
    """图片编辑服务"""
    
    MAX_HISTORY_STEPS = 10
    
    def create_edit_session(self, image: bytes, task_id: str) -> str:
        """创建编辑会话"""
        pass
    
    def apply_edit(self, session_id: str, instruction: str, mask: Optional[bytes] = None) -> bytes:
        """应用编辑指令"""
        pass
    
    def undo(self, session_id: str) -> Optional[bytes]:
        """撤销"""
        pass
    
    def redo(self, session_id: str) -> Optional[bytes]:
        """重做"""
        pass
    
    def save_edit(self, session_id: str) -> str:
        """保存编辑结果"""
        pass
    
    def cancel_edit(self, session_id: str) -> bool:
        """取消编辑"""
        pass
```

### Configuration File

新增 `product_photo_providers.yaml`：

```yaml
# 产品图生成服务商配置（独立于小红书图文生成）
active_provider: kolors_virtual_tryon

providers:
  # 可灵虚拟换装
  kolors_virtual_tryon:
    type: kolors_virtual_tryon
    api_key: your-api-key
    base_url: https://api.klingai.com
    model: kolors-virtual-try-on
    category: upper_body  # upper_body, lower_body, full_body
  
  # Kling AI
  kling_ai:
    type: kling_ai
    api_key: your-api-key
    base_url: https://api.klingai.com
    model: kling-v1
    # Kling 特有参数
    quality: high
  
  # Stable Diffusion Inpainting
  stable_diffusion:
    type: stable_diffusion
    api_key: your-api-key
    base_url: https://api.stability.ai
    model: stable-diffusion-xl-1024-v1-0
    # SD 特有参数
    cfg_scale: 7
    steps: 30
  
  # 通用 OpenAI 兼容接口
  openai_compatible:
    type: openai_compatible
    api_key: your-api-key
    base_url: https://your-api-endpoint.com
    model: your-model
```

### API Routes

#### 1. Product Photo Routes (`/api/product-photo`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | 生成产品图（SSE） |
| POST | `/retry` | 重试生成 |
| GET | `/task/{task_id}` | 获取任务状态 |
| GET | `/images/{task_id}/{filename}` | 获取生成的图片 |
| GET | `/providers` | 获取可用供应商列表及其支持的功能 |

#### 2. Template Routes (`/api/templates`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | 列出所有模板 |
| POST | `/` | 保存新模板 |
| GET | `/{template_id}` | 获取模板图片 |
| PUT | `/{template_id}` | 更新模板信息 |
| DELETE | `/{template_id}` | 删除模板 |

#### 3. Edit Routes (`/api/edit`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/session` | 创建编辑会话 |
| POST | `/session/{session_id}/apply` | 应用编辑 |
| POST | `/session/{session_id}/undo` | 撤销 |
| POST | `/session/{session_id}/redo` | 重做 |
| POST | `/session/{session_id}/save` | 保存编辑 |
| DELETE | `/session/{session_id}` | 取消编辑 |

### Frontend Components

#### Views
- `ProductPhotoView.vue` - 产品图生成主页面
- `ProductPhotoEditView.vue` - 图片二次编辑页面
- `TemplateManageView.vue` - 模特模板管理页面

#### Components
- `ModelImageUploader.vue` - 模特图上传组件
- `ProductImageUploader.vue` - 商品图上传组件（支持多张）
- `BackgroundSelector.vue` - 背景选择器
- `PoseSelector.vue` - 姿势选择器
- `StyleSelector.vue` - 风格选择器
- `PlacementSelector.vue` - 商品位置选择器
- `ImageEditor.vue` - 图片编辑器（支持蒙版绘制）
- `TemplateCard.vue` - 模板卡片组件
- `ProviderSelector.vue` - 供应商选择器（显示各供应商支持的功能）

## Data Models

### Backend Models

```python
@dataclass
class BackgroundConfig:
    type: str  # "preset" | "custom" | "description" | "original"
    preset: Optional[str] = None  # 街拍、室内、商场、户外、纯色
    custom_image: Optional[bytes] = None
    description: Optional[str] = None

@dataclass
class PlacementConfig:
    position: str  # "auto" | "left_hand" | "right_hand" | "shoulder" | "chest" | "waist"
    custom_instruction: Optional[str] = None

@dataclass
class TemplateInfo:
    id: str
    name: str
    thumbnail_url: str
    created_at: str
    
@dataclass
class EditSession:
    id: str
    task_id: str
    original_image: bytes
    current_image: bytes
    history: List[bytes]  # 最多 10 步
    history_index: int
    created_at: str

@dataclass
class ProductPhotoTask:
    id: str
    status: str  # "pending" | "generating" | "completed" | "failed"
    provider: str  # 使用的供应商
    model_image: bytes
    product_images: List[bytes]
    config: Dict[str, Any]
    results: List[str]
    error: Optional[str] = None
```

### Frontend Types

```typescript
interface BackgroundConfig {
  type: 'preset' | 'custom' | 'description' | 'original'
  preset?: string
  customImage?: File
  description?: string
}

interface PlacementConfig {
  position: 'auto' | 'left_hand' | 'right_hand' | 'shoulder' | 'chest' | 'waist'
  customInstruction?: string
}

interface GenerateRequest {
  modelImage: File | string
  productImages: File[]
  prompt?: string
  aspectRatio?: string
  style?: string
  background?: BackgroundConfig
  placement?: PlacementConfig
  pose?: string
  variations?: number
  provider?: string  // 指定供应商
}

interface ProviderInfo {
  name: string
  displayName: string
  features: {
    backgroundChange: boolean
    poseChange: boolean
    multiProduct: boolean
    inpainting: boolean
  }
}

interface Template {
  id: string
  name: string
  thumbnailUrl: string
  createdAt: string
}

interface EditSession {
  id: string
  canUndo: boolean
  canRedo: boolean
  currentImageUrl: string
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Image Format Validation
*For any* uploaded image file, the system should accept it if and only if its format is PNG, JPG, or WEBP.
**Validates: Requirements 1.1**

### Property 2: Task ID Uniqueness
*For any* two generation requests, the returned task IDs should be different.
**Validates: Requirements 1.2**

### Property 3: Output Format Consistency
*For any* successful generation, the returned image should be valid PNG format.
**Validates: Requirements 1.3**

### Property 4: Aspect Ratio Compliance
*For any* generation request with a specified aspect ratio, the output image dimensions should match the requested ratio (within 1% tolerance).
**Validates: Requirements 2.2**

### Property 5: Variation Count Limit
*For any* generation request with N variations (where N > 0), the system should generate exactly min(N, 4) images.
**Validates: Requirements 3.1**

### Property 6: Download URL Validity
*For any* completed batch generation, all returned image URLs should be accessible and return valid image data.
**Validates: Requirements 3.3**

### Property 7: Failed Task Image Preservation
*For any* failed generation task, the uploaded images should remain accessible for retry.
**Validates: Requirements 4.1**

### Property 8: Retry Image Reuse
*For any* retry request on a failed task, the system should use the previously uploaded images without requiring re-upload.
**Validates: Requirements 4.2**

### Property 9: API Input Format Flexibility
*For any* valid image data, the API should accept both base64 encoded strings and multipart form data.
**Validates: Requirements 5.2**

### Property 10: API Response Format
*For any* successful API generation, the response should contain either a valid image URL or valid base64 image data.
**Validates: Requirements 5.3**

### Property 11: Custom Background Inclusion
*For any* generation request with a custom background image, the background image should be included in the generation context.
**Validates: Requirements 8.2**

### Property 12: Template Save and Retrieve Round Trip
*For any* saved template, retrieving it by ID should return the same image data.
**Validates: Requirements 10.1, 10.3**

### Property 13: Template List Completeness
*For any* set of saved templates, listing templates should return all of them with valid thumbnail URLs.
**Validates: Requirements 10.2**

### Property 14: Template Deletion
*For any* deleted template, subsequent retrieval attempts should fail.
**Validates: Requirements 10.4**

### Property 15: Edit Mask Application
*For any* edit request with a mask, only the masked region should be modified (verified by comparing unmasked pixels).
**Validates: Requirements 12.3**

### Property 16: Edit Version Save
*For any* confirmed edit, a new version should be saved and accessible.
**Validates: Requirements 12.4**

### Property 17: Edit Cancel Preservation
*For any* cancelled edit session, the original image should remain unchanged.
**Validates: Requirements 12.5**

### Property 18: Edit History Limit
*For any* edit session, the history should contain at most 10 entries.
**Validates: Requirements 12.6**

## Error Handling

### Backend Error Handling

1. **图片验证错误**
   - 格式不支持：返回 400，提示支持的格式
   - 文件过大：返回 413，提示大小限制
   - 图片损坏：返回 400，提示重新上传

2. **生成错误**
   - API 调用失败：返回 500，包含详细错误信息
   - 超时：返回 504，建议重试
   - 安全过滤：返回 400，提示修改内容
   - 供应商不支持的功能：返回 400，提示切换供应商

3. **模板错误**
   - 模板不存在：返回 404
   - 存储空间不足：返回 507

4. **编辑错误**
   - 会话不存在：返回 404
   - 会话过期：返回 410
   - 无法撤销/重做：返回 400

### Frontend Error Handling

1. **上传错误** - 显示友好提示，支持重新选择
2. **生成错误** - 显示错误详情，提供重试按钮
3. **网络错误** - 自动重连 SSE，显示连接状态
4. **功能不支持** - 提示用户切换到支持该功能的供应商
