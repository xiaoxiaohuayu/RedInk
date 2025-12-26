# Requirements Document

## Introduction

本功能为红墨 AI 图文生成器添加"产品图生成"能力。用户可以上传一张模特图和多张商品图（衣服、鞋子、玩具、配饰、包包、手表等），AI 将自动合成一张专业的产品展示图，让模特"穿上"或"展示"这些商品。支持换背景、调整商品位置、保存模特模板、生成不同姿势，以及对生成结果进行二次编辑。这个功能主要面向电商卖家、品牌方和内容创作者，帮助他们快速生成高质量的产品宣传图。

## Glossary

- **Product_Photo_Generator**: 产品图生成系统，负责将模特图与商品图合成为产品展示图
- **Model_Image**: 模特图，包含人物的参考图片
- **Product_Image**: 商品图，需要展示的产品图片（衣服、鞋子、配饰、包包、手表等）
- **Composite_Image**: 合成图，最终生成的产品展示图
- **Generation_Task**: 生成任务，一次产品图生成的完整流程
- **Model_Template**: 模特模板，保存的模特图及其配置，可复用
- **Background_Scene**: 背景场景，产品图的背景环境（如街拍、室内、纯色等）
- **Product_Placement**: 商品位置，商品在模特身上或手中的具体位置
- **Edit_Session**: 编辑会话，对生成图片进行二次编辑的操作过程

## Requirements

### Requirement 1

**User Story:** As a 电商卖家, I want to 上传模特图和商品图来生成产品展示图, so that 我可以快速制作专业的产品宣传素材而无需实际拍摄。

#### Acceptance Criteria

1. WHEN a user uploads a model image and one or more product images THEN the Product_Photo_Generator SHALL accept the images and validate their formats (PNG, JPG, WEBP)
2. WHEN a user submits valid images for generation THEN the Product_Photo_Generator SHALL create a Generation_Task and return a unique task identifier
3. WHEN the generation process completes successfully THEN the Product_Photo_Generator SHALL return the Composite_Image in PNG format
4. IF a user uploads an invalid image format THEN the Product_Photo_Generator SHALL reject the upload and return a descriptive error message
5. WHILE a Generation_Task is in progress THEN the Product_Photo_Generator SHALL provide status updates to the user

### Requirement 2

**User Story:** As a 内容创作者, I want to 自定义生成参数, so that 我可以控制最终产品图的风格和效果。

#### Acceptance Criteria

1. WHEN a user specifies a prompt description THEN the Product_Photo_Generator SHALL incorporate the description into the generation process
2. WHEN a user selects an aspect ratio THEN the Product_Photo_Generator SHALL generate the Composite_Image with the specified dimensions
3. WHERE a user provides style preferences (e.g., 简约、时尚、复古、街头、高端) THEN the Product_Photo_Generator SHALL apply the style to the generated image
4. WHEN no custom parameters are provided THEN the Product_Photo_Generator SHALL use default settings (3:4 aspect ratio, 自然风格)

### Requirement 3

**User Story:** As a 品牌方, I want to 批量生成多张不同角度或风格的产品图, so that 我可以获得多样化的宣传素材。

#### Acceptance Criteria

1. WHEN a user requests multiple variations THEN the Product_Photo_Generator SHALL generate the specified number of Composite_Images (maximum 4)
2. WHEN generating multiple variations THEN the Product_Photo_Generator SHALL maintain consistency in product appearance across all images
3. WHEN batch generation completes THEN the Product_Photo_Generator SHALL return all generated images with individual download links

### Requirement 4

**User Story:** As a 用户, I want to 在生成失败时能够重试, so that 我不需要重新上传所有图片。

#### Acceptance Criteria

1. IF a Generation_Task fails THEN the Product_Photo_Generator SHALL preserve the uploaded images for retry
2. WHEN a user requests a retry THEN the Product_Photo_Generator SHALL reuse the previously uploaded images
3. WHEN a retry succeeds THEN the Product_Photo_Generator SHALL replace the failed result with the new Composite_Image

### Requirement 5

**User Story:** As a 开发者, I want to 通过 API 调用产品图生成功能, so that 我可以将此功能集成到其他系统中。

#### Acceptance Criteria

1. WHEN an API request is received with valid parameters THEN the Product_Photo_Generator SHALL process the request
2. WHEN the API receives image data THEN the Product_Photo_Generator SHALL accept both base64 encoded strings and multipart form data
3. WHEN the API generation completes THEN the Product_Photo_Generator SHALL return a JSON response containing the image URL or base64 data
4. IF the API request is malformed THEN the Product_Photo_Generator SHALL return an appropriate HTTP error code with a descriptive message

### Requirement 6

**User Story:** As a 用户, I want to 预览和下载生成结果, so that 我可以在下载前确认效果满意。

#### Acceptance Criteria

1. WHEN a Composite_Image is generated THEN the Product_Photo_Generator SHALL display a preview in the user interface
2. WHEN a user is unsatisfied with the result THEN the Product_Photo_Generator SHALL allow regeneration with modified parameters
3. WHEN a user approves the result THEN the Product_Photo_Generator SHALL provide download options (original quality, compressed)

### Requirement 7

**User Story:** As a 电商卖家, I want to 支持多种商品类型, so that 我可以为不同品类的产品生成展示图。

#### Acceptance Criteria

1. WHEN a user uploads clothing items (衣服、裤子、裙子) THEN the Product_Photo_Generator SHALL position the items on the model's body appropriately
2. WHEN a user uploads footwear (鞋子、靴子、拖鞋) THEN the Product_Photo_Generator SHALL position the items on the model's feet
3. WHEN a user uploads accessories (配饰、项链、耳环、手链) THEN the Product_Photo_Generator SHALL position the items on appropriate body parts
4. WHEN a user uploads bags (包包、背包、手提包) THEN the Product_Photo_Generator SHALL position the items in the model's hand or on shoulder
5. WHEN a user uploads watches or wrist items THEN the Product_Photo_Generator SHALL position the items on the model's wrist
6. WHEN a user uploads toys or handheld products THEN the Product_Photo_Generator SHALL position the items in the model's hands

### Requirement 8

**User Story:** As a 品牌方, I want to 更换背景场景, so that 我可以让产品图适配不同的营销场景。

#### Acceptance Criteria

1. WHEN a user selects a preset background scene (街拍、室内、商场、户外、纯色) THEN the Product_Photo_Generator SHALL apply the selected background to the Composite_Image
2. WHEN a user uploads a custom background image THEN the Product_Photo_Generator SHALL use the uploaded image as the background
3. WHEN a user specifies a background description THEN the Product_Photo_Generator SHALL generate an appropriate background based on the description
4. WHEN no background is specified THEN the Product_Photo_Generator SHALL retain the original background from the model image

### Requirement 9

**User Story:** As a 用户, I want to 调整商品在模特身上的位置, so that 我可以获得更自然的展示效果。

#### Acceptance Criteria

1. WHEN a user specifies a Product_Placement position THEN the Product_Photo_Generator SHALL place the product at the specified location
2. WHEN a user selects from preset positions (左手、右手、肩上、胸前、腰间) THEN the Product_Photo_Generator SHALL apply the selected position
3. WHEN a user provides position adjustment instructions in the prompt THEN the Product_Photo_Generator SHALL interpret and apply the adjustments
4. WHEN no position is specified THEN the Product_Photo_Generator SHALL automatically determine the optimal position based on product type

### Requirement 10

**User Story:** As a 高频用户, I want to 保存模特模板以便复用, so that 我可以快速为同一模特生成不同商品的展示图。

#### Acceptance Criteria

1. WHEN a user saves a model image as a template THEN the Product_Photo_Generator SHALL store the Model_Template with a user-defined name
2. WHEN a user views saved templates THEN the Product_Photo_Generator SHALL display all Model_Templates with preview thumbnails
3. WHEN a user selects a saved template THEN the Product_Photo_Generator SHALL load the Model_Image for new generation tasks
4. WHEN a user deletes a template THEN the Product_Photo_Generator SHALL remove the Model_Template from storage
5. WHEN a user edits a template name THEN the Product_Photo_Generator SHALL update the template metadata

### Requirement 11

**User Story:** As a 内容创作者, I want to 生成不同姿势的模特图, so that 我可以获得更丰富的产品展示角度。

#### Acceptance Criteria

1. WHEN a user selects a pose preset (站立、坐姿、行走、侧身、回眸) THEN the Product_Photo_Generator SHALL generate the model in the selected pose
2. WHEN a user describes a custom pose in the prompt THEN the Product_Photo_Generator SHALL interpret and apply the described pose
3. WHEN generating pose variations THEN the Product_Photo_Generator SHALL maintain the model's facial features and overall appearance
4. WHEN no pose is specified THEN the Product_Photo_Generator SHALL retain the original pose from the model image

### Requirement 12

**User Story:** As a 用户, I want to 对生成的图片进行二次编辑, so that 我可以对细节进行微调而不需要完全重新生成。

#### Acceptance Criteria

1. WHEN a user initiates an Edit_Session THEN the Product_Photo_Generator SHALL load the Composite_Image into the editing interface
2. WHEN a user provides edit instructions (e.g., "把包包往左移一点", "调亮一些", "去掉背景杂物") THEN the Product_Photo_Generator SHALL apply the specified modifications
3. WHEN a user requests local edits using a mask or selection THEN the Product_Photo_Generator SHALL modify only the selected region
4. WHEN a user confirms the edits THEN the Product_Photo_Generator SHALL save the modified image as a new version
5. WHEN a user cancels the edits THEN the Product_Photo_Generator SHALL discard changes and retain the original Composite_Image
6. WHEN editing is complete THEN the Product_Photo_Generator SHALL maintain edit history for undo/redo operations (maximum 10 steps)
