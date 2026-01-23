---
name: orchestrator-workflow
description: Manages complex multi-step orchestration workflows with proper state management and turn-based execution. Use when coordinating multiple specialized agents in sequential processes with state updates, rejection handling, and strict workflow requirements. Handles write_todos/task separation, workflow state tracking, and rejection loop management.
---

# Orchestrator Workflow

## Overview

This skill provides patterns and utilities for managing complex multi-agent orchestration workflows. It handles the critical requirement of separating state updates from task delegations, manages workflow state tracking, and provides templates for handling rejections and loops.

## Core Capabilities

### 1. Turn-Based State Management
Enforces the critical rule: ONE write_todos PER TURN, separate from task delegations.

**Correct Pattern:**
```
# Turn 1: Update state only
write_todos([...])

# Turn 2: Delegate tasks only
task(agent="specialist", task="...")
```

### 2. Workflow State Tracking
Maintains workflow progress through required states:
- `pending`: Task not yet started
- `in_progress`: Currently working on (limit to ONE task at a time)
- `completed`: Task finished successfully
- `rejected`: Task failed, needs retry or fallback

### 3. Rejection Handling
Manages rejection loops with configurable limits and fallback strategies:
- Track rejection count per step
- Implement backtracking to previous steps
- Force approval after max attempts

## Usage Patterns

### Basic Orchestration Flow
1. **Parse Request**: Extract topic, context, tone, requirements
2. **Plan Workflow**: Create todo list with proper dependencies
3. **Execute Steps**: Delegate to agents with state updates between each step
4. **Handle Rejections**: Loop back or escalate as needed
5. **Complete Workflow**: Finalize and report results

### State Update Rules
- Always include `"owner"` field in todos
- Mark tasks `in_progress` when starting work
- Complete current tasks before starting new ones
- Cancel irrelevant tasks when workflow changes

### Task Delegation Templates
**Standard Task:**
```
task(agent="creative-director", task="Create brief for: [topic]. Context: [context]")
```

**With Creative Brief Reference:**
```
task(agent="hook-agent", task="Generate hooks using Brief ID: [brief_id]")
```

## Resources

### scripts/
- `workflow_validator.py`: Validates workflow state transitions and requirements
- `state_manager.py`: Utilities for managing complex workflow states

### references/
- `workflow_patterns.md`: Common orchestration patterns and anti-patterns
- `state_schema.md`: Complete state management schema and validation rules

### assets/
- `workflow_templates/`: Pre-built workflow templates for common orchestration patterns
