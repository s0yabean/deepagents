---
name: agent-task-formatter
description: Provides standardized templates and formatting utilities for agent task descriptions. Use when delegating tasks to specialized agents to ensure consistent context passing, requirement injection, and minimal verbosity. Handles task description formatting, context reference systems, and requirement consolidation.
---

# Agent Task Formatter

## Overview

This skill provides standardized formatting utilities for creating concise, consistent task descriptions when delegating work to specialized agents. It eliminates repetitive context passing and ensures all necessary information is included without bloat.

## Core Capabilities

### 1. Task Description Templates
Pre-built templates for common agent delegation patterns:

**Creative Brief Tasks:**
```
task(agent="hook-agent", task="Generate hooks using Brief ID: {brief_id}")
```

**Content Creation Tasks:**
```
task(agent="content-strategist", task="Write script for '{topic}' using Brief ID: {brief_id}")
```

**Quality Assurance Tasks:**
```
task(agent="qa-specialist", task="Review package for '{topic}' against Brief ID: {brief_id}")
```

### 2. Context Consolidation
Automatically consolidates user requirements and constraints:
- Extract common requirements once
- Reference via IDs instead of repetition
- Inject requirements only where relevant

### 3. Requirement Injection
Smart requirement filtering based on agent role:
- Visual designers get format/image requirements
- Content strategists get tone/narrative requirements
- QA specialists get quality/compliance requirements

## Usage Patterns

### Basic Task Formatting
```python
format_task(
    agent="visual-designer",
    action="Select images",
    context={"brief_id": "brief_20241201_001", "slide_count": 4},
    requirements=["high-contrast", "no-text"]
)
```

### Requirement Management
1. **Parse Requirements**: Extract from user input once
2. **Categorize**: Group by relevance (visual, content, technical)
3. **Inject Selectively**: Add only relevant requirements to each task

### Context Reference System
- Store complex context (Creative Briefs, user requirements) centrally
- Use IDs for task descriptions
- Provide retrieval functions for agents that need full context

## Resources

### scripts/
- `task_formatter.py`: Core task description formatting utilities
- `requirement_parser.py`: Parses and categorizes user requirements

### references/
- `task_templates.md`: Complete catalog of task description templates
- `context_patterns.md`: Best practices for context passing and reference systems

### assets/
- `template_library/`: Pre-built task templates for common agent interactions
