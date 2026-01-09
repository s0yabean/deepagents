# Product Requirement Decisions (PRD) Log

This document tracks key product decisions, architectural changes, and policy enforcements for the TikTok Slideshow Agent.

## 2026-01-10: Visual Consistency & Narrative Integrity

### 1. "Single Protagonist" Rule (No Humans in Slides 2+)
**Context**: Random stock photos of different people across slides break the narrative illusion, confusing the viewer about whose "story" it is.
**Decision**: Enforce a strict policy where only the Hook slide (Slide 1) may feature a human subject. All subsequent slides must be background-focused.
**Implementation**:
-   **Designer Strategy**: For slides 2+, Pexels queries automatically append keywords like `"no people"`, `"scenery"`, `"object"`, or `"abstract"`.
-   **Validation**: `verify_visual_consistency` flags any non-hook slide with a face as an outlier.
-   **Selection**: `select_best_fitting_image` heavily penalizes candidates with human faces for non-hook slides.

### 2. Smart Image Selection ("Best of 3")
**Context**: The previous "pick first result" or "pick next result" loop was inefficient and often led to "blind" selection of poor images.
**Decision**: Implement a "Select Best" workflow.
**Implementation**:
-   **Broad Search**: Fetch 3-5 candidates from Pexels (Limit increased from 5 to 15 to safeguard quality).
-   **AI Judge**: Use a dedicated Vision Tool (`select_best_fitting_image`) to evaluate all candidates simultaneously against the `slide_need`.

### 3. Context-Aware Visual Consistency
**Context**: Images were being selected in isolation, leading to jarring style clashes (e.g., Slide 1 is Dark Moody, Slide 2 is Bright Neon).
**Decision**: The selection tool must see the *history* of approved images.
**Implementation**:
-   **Context Passing**: `select_best_fitting_image` now accepts `context_image_paths`.
-   **Logic**: The Vision AI explicitly compares new candidates against the passed "Reference Images" to match color grading and lighting.

### 4. "Effortless Plug" CTA Strategy
**Context**: Users found standard CTAs too salesy/aggressive for the current TikTok meta.
**Decision**: Introduce a new, ultra-low-pressure CTA style.
**Implementation**:
-   **Style**: Defined as `effortless_plug`.
-   **Copy Examples**: "Link in bio (if you want)", "Anyway, just thought I'd share."
-   **Placement**: Validated by `QA_INSTRUCTIONS` to ensure it feels incidental.

## System Tuning

### 5. Increased Agent Autonomy Limits
**Context**: Multi-step verification loops (Search -> Validate -> Correct -> Validate) were hitting early stop limits.
**Decision**: Increase system caps to allow for robust self-correction.
**Implementation**:
-   **Google Gemini AFC**: `max_function_calls` increased from 10 to **25**.
-   **Pexels Search Cap**: `limit` increased from 5 to **15**.

### 6. Human-in-Loop Reject Handling
**Context**: The "Interrupt" mechanism returned raw string feedback (e.g., "Change the image"), which the agent didn't know how to parse, causing stalls.
**Decision**: Explicitly instruct the QA Agent on how to format human feedback.
**Implementation**:
-   **Instruction**: If tool returns "Human Feedback: ...", the agent must translate this into a `{"status": "REJECT", ...}` JSON command to route the workflow back to the appropriate specialist.
