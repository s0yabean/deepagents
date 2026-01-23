---
name: creative-brief-manager
description: Centralized management of Creative Briefs for content creation workflows. Use when orchestrating multi-agent content creation processes that require consistent creative direction, format selection, and narrative guidance across multiple specialized agents. Handles Creative Brief creation, validation, storage, and context-efficient referencing to reduce repetitive JSON passing.
---

# Creative Brief Manager

## Overview

This skill provides a centralized system for managing Creative Briefs in multi-agent content creation workflows. Instead of passing verbose JSON Creative Briefs to every downstream agent, this skill enables efficient storage and reference-based context passing.

## Core Capabilities

### 1. Creative Brief Creation & Validation
Store and validate Creative Brief JSON structures with required fields:
- `format_id`: Content format identifier
- `hooks`: Hook strategy guidelines
- `narrative_arc`: Story structure guidance
- `image_arc`: Visual progression guidance
- `product_positioning`: How to handle promotional content

### 2. Context-Efficient Referencing
Instead of embedding full Creative Brief JSON in every task description, use reference IDs:
```
task(agent="hook-agent", task="Generate hooks using Creative Brief ID: brief_20241201_001")
```

### 3. Brief Retrieval & Summarization
Provide concise summaries for task contexts while maintaining full brief access when needed.

## Usage Patterns

### Basic Workflow
1. **Store Brief**: `store_creative_brief(brief_json)` → returns `brief_id`
2. **Reference in Tasks**: Use `brief_id` instead of full JSON
3. **Retrieve When Needed**: `get_creative_brief_summary(brief_id)` for task contexts
4. **Full Access**: `get_creative_brief_full(brief_id)` when complete brief required

### Task Description Templates
**Before (verbose):**
```
task(agent="content-strategist", task="Write script following this Creative Brief: {\"format_id\": \"transformation-story\", \"hooks\": [...], \"narrative_arc\": [...], ...}")
```

**After (concise):**
```
task(agent="content-strategist", task="Write script using Creative Brief ID: brief_20241201_001")
```

## Resources

### scripts/
- `validate_brief.py`: Validates Creative Brief JSON structure and required fields
- `brief_manager.py`: Core brief storage and retrieval functionality

### references/
- `brief_formats.md`: Documentation of supported format types and their requirements
- `brief_schema.md`: Complete JSON schema for Creative Brief validation

### assets/
- `brief_templates/`: Pre-built brief templates for common content types
