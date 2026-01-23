---
name: visual-designer-skill
description: Advanced image selection and visual design system for content creation agents. Use when selecting background images for slideshows, ensuring visual consistency, and managing image libraries with fallback strategies for TikTok-style content.
---

# Visual Designer Skill

## Overview

Provides comprehensive image selection and visual design capabilities for content creation workflows. Handles library management, mood-based selection, visual consistency validation, and fallback image sourcing with non-blocking operations.

## Core Capabilities

### 1. Image Library Management
Sync and search local image libraries with metadata categorization and absolute path resolution.

**Key Operations:**
- Library synchronization with metadata updates
- Category-based search with tag filtering
- Absolute path resolution for rendering
- Duplicate detection and cleanup

### 2. Mood-Based Selection
Select images following creative brief image arcs with TikTok-specific visual requirements.

**Mood Categories:**
- `moody`: Dark, cinematic, tension-building
- `transitional`: Neutral bridge between moods
- `bright`: Light, aspirational, hopeful
- `bold`: High contrast, attention-grabbing
- `lifestyle`: Relatable, everyday scenarios

### 3. Visual Consistency Validation
Ensure selected images work together visually with AI-powered consistency checking.

**Validation Process:**
- Style coherence analysis
- Color palette compatibility
- Mood progression verification
- Outlier detection and replacement

### 4. Fallback Image Sourcing
Non-blocking Pexels integration for missing image requirements with smart query generation.

**Fallback Strategy:**
- Local library first priority
- Pexels search with background-focused queries
- Visual consistency verification
- URL handling for rendering pipeline

## Usage Workflow

### Basic Image Selection
```python
# 1. Sync library
await sync_image_library()

# 2. Select images for arc
images = await select_images_for_arc(
    image_arc=["moody", "transitional", "bright"],
    slide_count=3
)

# 3. Validate consistency
validation = await verify_visual_consistency(images, style_description)
```

### Advanced Selection with Fallbacks
```python
# Attempt local selection first
local_images = await search_local_images(category="cinematic_moody")

# Fallback to Pexels if insufficient
if len(local_images) < required_count:
    pexels_images = await search_pexels_fallback(
        query="dark moody background",
        needed=required_count - len(local_images)
    )
    images.extend(pexels_images)

# Final validation
await verify_and_replace_outliers(images, creative_context)
```

## Resources

### scripts/
- `image_selector.py`: Core image selection algorithms with mood mapping
- `visual_validator.py`: Visual consistency checking with outlier detection
- `pexels_handler.py`: Non-blocking Pexels integration with retry logic
- `library_manager.py`: Image library sync and metadata management

### references/
- `mood_categories.md`: Detailed definitions of visual mood categories
- `tiktok_visual_guidelines.md`: Platform-specific visual requirements
- `selection_patterns.md`: Best practices for image selection workflows
- `error_handling.md`: Fallback strategies and error recovery

### assets/
- `default_configs/`: Pre-configured mood mappings and selection rules
- `sample_images/`: Reference images for mood categories
