---
name: publisher-skill
description: End-to-end publishing system for content creation workflows. Use when rendering slides, uploading to cloud storage, and delivering final content with non-blocking operations for LangSmith compatibility.
---

# Publisher Skill

## Overview

Provides comprehensive publishing capabilities for content creation agents, handling slide rendering, cloud storage uploads, and notification delivery with full non-blocking operation support.

## Publishing Checklist (MANDATORY)

Follow this checklist in order. DO NOT skip steps:

1. **Setup** - Create project folder structure (local + Drive)
2. **Read** - Load approved metadata.json from disk
3. **Render** - Generate all slide images
4. **Upload** - Upload slides + metadata.json to Drive
5. **Verify** - Confirm all files present in Drive (CRITICAL - DO NOT SKIP)
6. **Notify** - Send email notification ONLY after verification passes
7. **Report** - Provide final summary with Drive link

## Core Capabilities

### 1. Project Setup & Management
Non-blocking project folder creation with duplicate detection and proper path resolution.

**Setup Process:**
- Timestamped folder generation
- Local and cloud directory creation
- Path validation and conflict resolution
- Metadata directory initialization

### 2. Slide Rendering Pipeline
Asynchronous slide rendering with URL download support and subprocess management.

**Rendering Features:**
- Local file and URL image handling
- Playwright-based screenshot capture
- Timeout and error recovery
- Temp file cleanup and resource management

### 3. Cloud Storage Integration
Non-blocking Google Drive uploads with authentication management and batch operations.

**Storage Operations:**
- OAuth token refresh handling
- Batch file uploads with progress tracking
- Folder creation and permission management
- Error recovery and retry logic

### 4. Upload Verification
Post-upload validation ensuring all required files are present in cloud storage.

**Verification Features:**
- Confirms metadata.json presence in Drive folder
- Validates expected slide count matches actual uploaded files
- Provides detailed error reporting for missing files
- Prevents email notifications if upload incomplete

**CRITICAL**: This step is MANDATORY and must occur after upload and BEFORE email notification.

### 5. Notification & Delivery
SMTP-based email notifications with fallback handling and recipient management.

**Delivery Features:**
- Multi-recipient support
- HTML/plain text formatting
- Authentication and connection pooling
- Status tracking and error reporting

## Usage Workflow

### Complete Publishing Pipeline
```python
# 1. Setup project structure
project_info = await setup_project_non_blocking(topic, base_path)

# 2. Render slides asynchronously
rendered_paths = []
for slide in approved_slides:
    path = await render_slide_non_blocking(
        slide["text"],
        slide["image_path"],
        slide["slide_number"],
        project_info["slideshows_dir"]
    )
    rendered_paths.append(path)

# 3. Upload to cloud storage (MUST include metadata.json)
drive_link = await upload_batch_non_blocking(
    rendered_paths + [metadata_path],
    project_info["drive_folder_id"]
)

# 4. VERIFY upload (MANDATORY - DO NOT SKIP)
verification_result = await verify_drive_upload(
    folder_id=project_info["drive_folder_id"],
    expected_slide_count=len(approved_slides)
)
# If verification fails, STOP and report error. DO NOT send email.
if "VERIFICATION FAILED" in verification_result:
    raise Exception(verification_result)

# 5. Send notifications (ONLY after verification passes)
await send_notification_non_blocking(
    subject=f"TikTok Slideshow Ready: {topic}",
    content=f"Your slideshow is ready: {drive_link}",
    recipients=get_admin_emails()
)
```

### Error Handling & Recovery
```python
try:
    result = await publish_content_with_retries(
        slides=slides,
        topic=topic,
        max_retries=3,
        timeout_per_step=60
    )
except PublishingError as e:
    # Fallback to partial delivery
    await send_error_notification(e, partial_results)
```

## Resources

### scripts/
- `project_setup.py`: Non-blocking project folder creation and management
- `slide_renderer.py`: Async slide rendering with URL download support
- `drive_publisher.py`: Google Drive integration with token management
- `notification_handler.py`: Email/SMS delivery with retry logic

### references/
- `oauth_guide.md`: Google Drive authentication and token refresh procedures
- `rendering_guide.md`: Playwright setup and troubleshooting for slide rendering
- `smtp_config.md`: Email server configuration and security best practices
- `error_handling.md`: Recovery strategies for publishing failures

### assets/
- `email_templates/`: Pre-configured email templates for different notification types
- `config_templates/`: Default configuration files for cloud storage and SMTP
