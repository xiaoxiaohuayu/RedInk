# Implementation Plan

## Phase 1: Backend Core Infrastructure

- [x] 1. Set up product photo generator infrastructure
  - [x] 1.1 Create `backend/product_generators/` directory structure
    - Create `__init__.py`, `base.py`, `factory.py`
    - _Requirements: 1.1, 1.2_
  - [x] 1.2 Implement `ProductPhotoGeneratorBase` abstract class
    - Define `ProductPhotoRequest` and `ProductPhotoResult` dataclasses
    - Define abstract methods: `generate()`, `validate_config()`
    - Define feature flags: `SUPPORTS_BACKGROUND_CHANGE`, `SUPPORTS_POSE_CHANGE`, etc.
    - _Requirements: 1.1, 7.1-7.6, 8.1-8.4, 9.1-9.4, 11.1-11.4_
  - [x] 1.3 Implement `ProductPhotoGeneratorFactory`
    - Create factory with `register()` and `create()` methods
    - _Requirements: 1.2_

- [x] 2. Create configuration system for product photo providers
  - [x] 2.1 Create `product_photo_providers.yaml.example` template
    - Include example configurations for multiple providers
    - _Requirements: 5.1_
  - [x] 2.2 Add config loading methods to `Config` class
    - Add `load_product_photo_providers_config()`
    - Add `get_active_product_photo_provider()`
    - Add `get_product_photo_provider_config()`
    - _Requirements: 5.1_

- [x] 3. Checkpoint - Ensure infrastructure is working
  - Ensure all tests pass, ask the user if questions arise.

## Phase 2: First Provider Implementation

- [x] 4. Implement first product photo generator (OpenAI Compatible as baseline)
  - [x] 4.1 Create `backend/product_generators/openai_compatible.py`
    - Implement image composition via chat completions API
    - Support model image + product images input
    - _Requirements: 1.1, 1.3, 5.2, 5.3_
  - [x] 4.2 Write property test for image format validation
    - **Property 1: Image Format Validation**
    - **Validates: Requirements 1.1**
  - [x] 4.3 Write property test for output format consistency
    - **Property 3: Output Format Consistency**
    - **Validates: Requirements 1.3**

## Phase 3: Product Photo Service

- [x] 5. Implement ProductPhotoService
  - [x] 5.1 Create `backend/services/product_photo.py`
    - Implement `generate_product_photo()` with SSE streaming
    - Implement task state management
    - Implement `retry_generation()`
    - _Requirements: 1.2, 1.5, 4.1, 4.2, 4.3_
  - [x] 5.2 Write property test for task ID uniqueness
    - **Property 2: Task ID Uniqueness**
    - **Validates: Requirements 1.2**
  - [x] 5.3 Write property test for failed task image preservation
    - **Property 7: Failed Task Image Preservation**
    - **Validates: Requirements 4.1**
  - [x] 5.4 Write property test for retry image reuse
    - **Property 8: Retry Image Reuse**
    - **Validates: Requirements 4.2**

- [x] 6. Checkpoint - Ensure service layer is working
  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: Product Photo API Routes

- [x] 7. Create product photo API routes
  - [x] 7.1 Create `backend/routes/product_photo_routes.py`
    - Implement `POST /api/product-photo/generate` (SSE)
    - Implement `POST /api/product-photo/retry`
    - Implement `GET /api/product-photo/task/{task_id}`
    - Implement `GET /api/product-photo/images/{task_id}/{filename}`
    - Implement `GET /api/product-photo/providers`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 7.2 Register routes in `backend/routes/__init__.py`
    - _Requirements: 5.1_
  - [x] 7.3 Write property test for API input format flexibility
    - **Property 9: API Input Format Flexibility**
    - **Validates: Requirements 5.2**
  - [x] 7.4 Write property test for API response format
    - **Property 10: API Response Format**
    - **Validates: Requirements 5.3**

## Phase 5: Template Management

- [x] 8. Implement template management service
  - [x] 8.1 Create `backend/services/template.py`
    - Implement `save_template()`, `list_templates()`, `get_template()`
    - Implement `delete_template()`, `update_template()`
    - Create `templates/` storage directory
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - [x] 8.2 Write property test for template save and retrieve round trip
    - **Property 12: Template Save and Retrieve Round Trip**
    - **Validates: Requirements 10.1, 10.3**
  - [x] 8.3 Write property test for template list completeness
    - **Property 13: Template List Completeness**
    - **Validates: Requirements 10.2**
  - [x] 8.4 Write property test for template deletion
    - **Property 14: Template Deletion**
    - **Validates: Requirements 10.4**

- [x] 9. Create template API routes
  - [x] 9.1 Create `backend/routes/template_routes.py`
    - Implement `GET /api/templates`
    - Implement `POST /api/templates`
    - Implement `GET /api/templates/{template_id}`
    - Implement `PUT /api/templates/{template_id}`
    - Implement `DELETE /api/templates/{template_id}`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - [x] 9.2 Register routes in `backend/routes/__init__.py`
    - _Requirements: 10.1_

- [x] 10. Checkpoint - Ensure template management is working
  - Ensure all tests pass, ask the user if questions arise.

## Phase 6: Image Editing Service

- [x] 11. Implement image editing service
  - [x] 11.1 Create `backend/services/image_edit.py`
    - Implement `create_edit_session()`
    - Implement `apply_edit()` with instruction parsing
    - Implement `undo()`, `redo()` with history management (max 10 steps)
    - Implement `save_edit()`, `cancel_edit()`
    - Create `edit_sessions/` storage directory
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  - [x] 11.2 Write property test for edit history limit
    - **Property 18: Edit History Limit**
    - **Validates: Requirements 12.6**
  - [x] 11.3 Write property test for edit cancel preservation
    - **Property 17: Edit Cancel Preservation**
    - **Validates: Requirements 12.5**
  - [x] 11.4 Write property test for edit version save
    - **Property 16: Edit Version Save**
    - **Validates: Requirements 12.4**

- [x] 12. Create edit API routes
  - [x] 12.1 Create `backend/routes/edit_routes.py`
    - Implement `POST /api/edit/session`
    - Implement `POST /api/edit/session/{session_id}/apply`
    - Implement `POST /api/edit/session/{session_id}/undo`
    - Implement `POST /api/edit/session/{session_id}/redo`
    - Implement `POST /api/edit/session/{session_id}/save`
    - Implement `DELETE /api/edit/session/{session_id}`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  - [x] 12.2 Register routes in `backend/routes/__init__.py`
    - _Requirements: 12.1_

- [x] 13. Checkpoint - Ensure editing service is working
  - Ensure all tests pass, ask the user if questions arise.

## Phase 7: Frontend - Core Components

- [x] 14. Create frontend API layer
  - [x] 14.1 Create `frontend/src/api/productPhoto.ts`
    - Implement `generateProductPhoto()` with SSE handling
    - Implement `retryGeneration()`, `getTaskStatus()`
    - Implement `getProviders()`
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 14.2 Create `frontend/src/api/template.ts`
    - Implement template CRUD operations
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - [x] 14.3 Create `frontend/src/api/edit.ts`
    - Implement edit session operations
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 15. Create Pinia stores
  - [x] 15.1 Create `frontend/src/stores/productPhoto.ts`
    - Manage generation state, task progress, results
    - _Requirements: 1.5, 6.1, 6.2_
  - [x] 15.2 Create `frontend/src/stores/template.ts`
    - Manage template list and selection
    - _Requirements: 10.1, 10.2, 10.3_

## Phase 8: Frontend - Upload Components

- [x] 16. Create image upload components
  - [x] 16.1 Create `ModelImageUploader.vue`
    - Support drag & drop, file selection
    - Support loading from saved templates
    - Image preview and validation
    - _Requirements: 1.1, 10.3_
  - [x] 16.2 Create `ProductImageUploader.vue`
    - Support multiple image upload
    - Image preview, reorder, remove
    - _Requirements: 1.1, 7.1-7.6_

## Phase 9: Frontend - Configuration Components

- [x] 17. Create configuration selector components
  - [x] 17.1 Create `BackgroundSelector.vue`
    - Preset backgrounds (街拍、室内、商场、户外、纯色)
    - Custom background upload
    - Description input
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [x] 17.2 Create `PoseSelector.vue`
    - Preset poses (站立、坐姿、行走、侧身、回眸)
    - Custom pose description
    - _Requirements: 11.1, 11.2_
  - [x] 17.3 Create `StyleSelector.vue`
    - Style presets (简约、时尚、复古、街头、高端)
    - _Requirements: 2.3_
  - [x] 17.4 Create `PlacementSelector.vue`
    - Position presets (左手、右手、肩上、胸前、腰间、自动)
    - Custom instruction input
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [x] 17.5 Create `ProviderSelector.vue`
    - Display available providers with feature support indicators
    - _Requirements: 5.1_

## Phase 10: Frontend - Main Views

- [x] 18. Create main product photo view
  - [x] 18.1 Create `ProductPhotoView.vue`
    - Integrate all upload and configuration components
    - Generation progress display with SSE
    - Result preview with regenerate option
    - Download functionality
    - _Requirements: 1.5, 2.1, 2.2, 2.4, 3.1, 3.3, 6.1, 6.2, 6.3_
  - [x] 18.2 Write property test for variation count limit
    - **Property 5: Variation Count Limit**
    - **Validates: Requirements 3.1**
  - [x] 18.3 Write property test for download URL validity
    - **Property 6: Download URL Validity**
    - **Validates: Requirements 3.3**

- [x] 19. Create template management view
  - [x] 19.1 Create `TemplateManageView.vue`
    - Template grid with thumbnails
    - Save, rename, delete operations
    - _Requirements: 10.1, 10.2, 10.4, 10.5_
  - [x] 19.2 Create `TemplateCard.vue`
    - Template preview card component
    - _Requirements: 10.2_

## Phase 11: Frontend - Image Editor

- [x] 20. Create image editor view
  - [x] 20.1 Create `ProductPhotoEditView.vue`
    - Load generated image for editing
    - Instruction input for AI editing
    - Undo/redo controls
    - Save/cancel buttons
    - _Requirements: 12.1, 12.2, 12.4, 12.5, 12.6_
  - [x] 20.2 Create `ImageEditor.vue` component
    - Canvas-based mask drawing
    - Brush size control
    - Clear mask button
    - _Requirements: 12.3_
  - [x] 20.3 Write property test for edit mask application
    - **Property 15: Edit Mask Application**
    - **Validates: Requirements 12.3**

## Phase 12: Frontend - Router and Navigation

- [x] 21. Update router and navigation
  - [x] 21.1 Add routes to `frontend/src/router/index.ts`
    - `/product-photo` - ProductPhotoView
    - `/product-photo/edit/:taskId/:imageIndex` - ProductPhotoEditView
    - `/templates` - TemplateManageView
    - _Requirements: 6.1_
  - [x] 21.2 Add navigation links to app layout
    - Add "产品图生成" to main navigation
    - _Requirements: 6.1_

## Phase 13: Additional Providers (Optional)

- [x] 22. Implement additional product photo generators
  - [x] 22.1 Create `backend/product_generators/kolors_virtual_tryon.py`
    - Implement Kolors Virtual Try-on API integration
    - _Requirements: 7.1, 7.2_
  - [x] 22.2 Create `backend/product_generators/kling_ai.py`
    - Implement Kling AI integration
    - _Requirements: 7.1-7.6_
  - [x] 22.3 Create `backend/product_generators/stable_diffusion.py`
    - Implement Stable Diffusion Inpainting integration
    - _Requirements: 8.1, 8.2, 12.3_

- [x] 23. Final Checkpoint - Ensure all features are working
  - Ensure all tests pass, ask the user if questions arise.
