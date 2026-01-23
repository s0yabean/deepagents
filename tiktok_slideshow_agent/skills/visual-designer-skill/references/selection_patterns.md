# Image Selection Patterns

Common workflows, decision trees, and best practices for image selection in TikTok slideshow production.

## Standard Workflow Patterns

### Pattern 1: Pure Local Selection (Ideal Scenario)

**When to Use:** Local library has abundant high-quality images across all mood categories

**Workflow:**
```
1. sync_image_library()
2. For each slide in arc:
   a. Query local library by mood category
   b. Collect 5+ candidates per slide
   c. Select best match based on text content
3. verify_visual_consistency(all_images)
4. If score ≥7/10 → finalize
5. If score <7/10 → replace outliers, re-verify
```

**Example (5-slide moody→bright arc):**
```json
Slide 1: /image_library/art_surreal/bold_contrast.jpg
Slide 2: /image_library/cinematic_moody/dark_office.jpg
Slide 3: /image_library/minimalist_bright/soft_light_desk.jpg
Slide 4: /image_library/minimalist_bright/airy_workspace.jpg
Slide 5: /image_library/minimalist_bright/bright_window.jpg
```

---

### Pattern 2: Hybrid Local + Pexels (Common Scenario)

**When to Use:** Local library has gaps for specific moods or slide contexts

**Workflow:**
```
1. sync_image_library()
2. For each slide in arc:
   a. Try local library first (3+ category combinations)
   b. If <3 strong candidates:
      - Use search_pexels_with_fallback(query, per_page=10, slide_position=N)
      - Collect 10+ Pexels candidates
      - Use select_best_fitting_image(candidates, context, slide_need, context_images)
3. verify_visual_consistency(all_images)
4. If score <7/10:
   - Identify outliers
   - Replace with better Pexels search (per_page=15)
5. Re-verify
```

**Example (5-slide arc with Pexels fallback):**
```json
Slide 1: /image_library/cinematic_moody/solo_bar.jpg (local)
Slide 2: https://images.pexels.com/photos/123456/... (Pexels - local lacked moody office)
Slide 3: https://images.pexels.com/photos/789012/... (Pexels - transitional scarce)
Slide 4: /image_library/minimalist_bright/sunset_pool.jpg (local)
Slide 5: /image_library/minimalist_bright/journaling.jpg (local)
```

---

### Pattern 3: Pexels-Heavy Selection (Sparse Library)

**When to Use:** Local library is empty or very limited

**Workflow:**
```
1. For each slide in arc:
   a. Build optimized query:
      - Mood keywords + context + "background"
      - If slide_position > 1: auto-appends "no people"
   b. search_pexels_with_fallback(query, per_page=15, slide_position=N)
   c. Collect context_images from previous selections
   d. select_best_fitting_image(candidates, context, slide_need, context_images)
2. verify_visual_consistency(all_images)
3. If score <7/10:
   - Replace outliers with alternative queries
   - Increase search depth (per_page=15)
4. Re-verify until ≥7/10
```

**Example (All Pexels):**
```json
Slide 1: https://images.pexels.com/photos/111111/... (bold hook)
Slide 2: https://images.pexels.com/photos/222222/... (moody struggle)
Slide 3: https://images.pexels.com/photos/333333/... (transitional discovery)
Slide 4: https://images.pexels.com/photos/444444/... (bright solution)
Slide 5: https://images.pexels.com/photos/555555/... (bright CTA)
```

---

## Decision Trees

### Decision Tree 1: Local vs. Pexels

```
For each slide:
├─ Query local library by mood category
│  ├─ Found 5+ strong candidates?
│  │  ├─ YES → Select best local image
│  │  └─ NO → Continue
│  ├─ Found 3-4 candidates?
│  │  ├─ Any perfect match?
│  │  │  ├─ YES → Select it
│  │  │  └─ NO → Use Pexels
│  │  └─ Continue
│  └─ Found <3 candidates?
│     └─ MUST use Pexels
```

### Decision Tree 2: Which Pexels Tool to Use

```
Need to search Pexels:
├─ Is query very specific?
│  ├─ YES → search_pexels(query, per_page=10, slide_position)
│  └─ NO → Continue
├─ Is query generic/broad?
│  ├─ YES → search_pexels_with_fallback(query, per_page=10, slide_position)
│  │  (Auto-tries query + "aesthetic", query + "texture", etc.)
│  └─ NO → Continue
└─ Unsure? → Use search_pexels_with_fallback (safer)
```

### Decision Tree 3: How Many Results to Request

```
Requesting Pexels results:
├─ First search for this slide?
│  ├─ YES → Start with per_page=10
│  └─ NO → Continue
├─ Previous search had <5 good candidates?
│  ├─ YES → Increase to per_page=15
│  └─ NO → Continue
└─ Already searched twice?
   └─ MAX out at per_page=15 (API limit)
```

### Decision Tree 4: Handling Outliers

```
verify_visual_consistency returns score <7/10:
├─ Check feedback for outlier slides
├─ For each outlier:
│  ├─ Is it a Pexels image?
│  │  ├─ YES → Search again with refined query
│  │  └─ NO → Try Pexels
│  ├─ Is it a local image?
│  │  ├─ Try alternative local category
│  │  └─ If no alternatives → Use Pexels
└─ Replace outliers, re-verify
```

---

## Anti-Patterns (What NOT to Do)

### ❌ Anti-Pattern 1: "Good Enough" Rationalization

**Behavior:**
```
Local library has 2 minimalist_bright images for "moody" slide
Agent thinks: "These are close enough, minimalist can look moody with the right text"
→ Skips Pexels search
```

**Why This Fails:**
- Breaks mood arc progression
- Visual-text mismatch confuses viewer
- Consistency check will flag as outlier

**Correct Approach:**
```
<3 candidates for moody → MUST use Pexels
Query: "dark moody [context] cinematic background"
```

---

### ❌ Anti-Pattern 2: Single-Category Search

**Behavior:**
```
For "moody" slide:
- Query only cinematic_moody category
- Find 1 candidate
- Accept it without trying other categories
```

**Why This Fails:**
- Misses art_surreal category (also supports moody)
- Doesn't exhaust local options before using Pexels

**Correct Approach:**
```
For "moody" slide:
1. Query cinematic_moody (2 candidates)
2. Query art_surreal (1 candidate)
3. Query any with tag:"dark" (2 more candidates)
Total: 5 candidates → select best
```

---

### ❌ Anti-Pattern 3: Blind Pexels Acceptance

**Behavior:**
```
search_pexels("office") returns 10 results
Agent picks first result without using select_best_fitting_image
```

**Why This Fails:**
- First result may not fit context or mood
- Ignores visual consistency with other selected images
- No consideration of slide-specific needs

**Correct Approach:**
```
search_pexels("dark moody office background", per_page=10, slide_position=2)
candidates = [10 URLs]
context_images = [slide_1_path]  # Already selected images
best = select_best_fitting_image(
    candidates,
    creative_context="Slideshow about work stress",
    slide_need="Moody office representing struggle",
    context_image_paths=context_images
)
```

---

### ❌ Anti-Pattern 4: Skipping Consistency Verification

**Behavior:**
```
Agent selects 5 images (3 local, 2 Pexels)
Assumes they look good together
Finalizes without calling verify_visual_consistency
```

**Why This Fails:**
- Outliers go undetected
- Visual style clashes ship to production
- Poor viewer experience

**Correct Approach:**
```
ALWAYS call verify_visual_consistency before finalizing
If score <7/10 → identify and replace outliers
Re-verify after replacements
```

---

### ❌ Anti-Pattern 5: Generic Pexels Queries

**Behavior:**
```
For moody slide about office stress:
Query: "office"
```

**Why This Fails:**
- Returns mix of bright/moody/lifestyle office images
- No mood targeting
- Wastes API calls sorting through irrelevant results

**Correct Approach:**
```
For moody slide about office stress:
Query: "dark moody office stress cinematic background"
OR use search_pexels_with_fallback to try variations
```

---

## Best Practices

### Best Practice 1: Context-Aware Selection

**Principle:** Images should reinforce the text message, not distract from it

**Implementation:**
```python
slide_text = "I was drowning in emails"
slide_need = "Moody image representing email overwhelm"

# Good query
query = "dark cluttered desk laptop email stress background"

# Bad query
query = "office"  # Too generic
```

---

### Best Practice 2: Progressive Context Building

**Principle:** Use previously selected images as context for next selections

**Implementation:**
```python
# Slide 1 selected
context_images = [slide_1_path]

# When selecting Slide 2
best_slide_2 = select_best_fitting_image(
    candidate_urls,
    creative_context="Work stress transformation story",
    slide_need="Deep moody struggle image",
    context_image_paths=context_images  # Show AI what style we're going for
)

# Slide 2 selected, add to context
context_images.append(slide_2_path)

# When selecting Slide 3, context now has Slides 1-2
# AI can see the established visual style
```

---

### Best Practice 3: Fallback Escalation

**Principle:** Increase search breadth if initial attempts fail

**Implementation:**
```python
# Attempt 1: Specific query, moderate results
results = search_pexels("dark moody office", per_page=5, slide_position=2)

# If <3 good candidates
# Attempt 2: Use fallback tool, more results
results = search_pexels_with_fallback("dark moody office", per_page=10, slide_position=2)

# If still <3 good candidates
# Attempt 3: Broaden query, max results
results = search_pexels_with_fallback("moody workspace", per_page=15, slide_position=2)
```

---

### Best Practice 4: Mood Arc Validation

**Principle:** Verify the selected images follow the intended mood progression

**Check List:**
```
□ Slide 1 (Hook): Is it bold/attention-grabbing?
□ Slides 2-3 (Problem/Moody): Are they darker than Slide 1?
□ Slide 3 (Transitional): Is it lighter than Slide 2, darker than Slide 4?
□ Slides 4-5 (Solution/Bright): Are they significantly brighter than Slide 3?
□ Overall: Does the arc feel like a progression (not random)?
```

---

## Common Workflow Examples

### Example 1: Standard 5-Slide Transformation Story

**Topic:** "How I fixed my sleep schedule"

**Arc:** ["bold", "moody", "transitional", "bright", "bright"]

**Workflow:**
```
1. sync_image_library()

2. Slide 1 (Hook - Bold):
   - Local query: art_surreal + tag:"bold"
   - Found 4 candidates
   - Select: /image_library/art_surreal/geometric_contrast.jpg

3. Slide 2 (Problem - Moody):
   - Local query: cinematic_moody + tag:"bedroom"
   - Found 1 candidate (insufficient)
   - Pexels: search_pexels("dark moody bedroom insomnia", per_page=10, slide_position=2)
   - Got 10 results
   - select_best_fitting_image(candidates, context=[slide_1_path])
   - Select: https://images.pexels.com/photos/123456/...

4. Slide 3 (Discovery - Transitional):
   - Local query: minimalist_bright (softer ones)
   - Found 2 candidates (insufficient)
   - Pexels: search_pexels_with_fallback("soft light bedroom calm", per_page=10, slide_position=3)
   - Got 12 results (fallback added results)
   - select_best_fitting_image(candidates, context=[slide_1_path, slide_2_path])
   - Select: https://images.pexels.com/photos/789012/...

5. Slide 4 (Solution - Bright):
   - Local query: minimalist_bright
   - Found 7 candidates
   - Select: /image_library/minimalist_bright/morning_light_bed.jpg

6. Slide 5 (CTA - Bright):
   - Local query: minimalist_bright + tag:"wellness"
   - Found 5 candidates
   - Select: /image_library/minimalist_bright/peaceful_bedroom.jpg

7. Verify:
   - verify_visual_consistency(all_5_images, "Sleep improvement transformation", "Topic about fixing sleep")
   - Result: "Consistency Score: 8/10, No outliers"
   - ✅ Finalize
```

---

### Example 2: Listicle Format (Consistent Style)

**Topic:** "5 signs you're burnt out"

**Arc:** ["consistent", "consistent", "consistent", "consistent", "consistent"]

**Workflow:**
```
1. sync_image_library()

2. Pick ONE category for all slides: minimalist_bright

3. For each slide (1-5):
   - Query: minimalist_bright + tag varies by slide context
   - Slide 1: "workspace" → /image_library/minimalist_bright/desk_a.jpg
   - Slide 2: "coffee" → /image_library/minimalist_bright/coffee_cup.jpg
   - Slide 3: "laptop" → /image_library/minimalist_bright/laptop_hands.jpg
   - Slide 4: "window" → /image_library/minimalist_bright/window_light.jpg
   - Slide 5: "journal" → /image_library/minimalist_bright/journaling.jpg

4. Verify:
   - verify_visual_consistency(all_5_images, "Listicle format", "Burnout signs list")
   - Result: "Consistency Score: 9/10, Unified aesthetic"
   - ✅ Finalize
```

---

## Troubleshooting Guide

### Issue: verify_visual_consistency score <7/10

**Diagnosis Steps:**
1. Read the verification feedback - which slides are outliers?
2. Compare outlier images to the arc:
   - Is the mood correct? (moody slide actually bright?)
   - Is the color grading consistent?
   - Is there a style clash? (photo vs. 3D render)

**Solutions:**
- **Wrong mood:** Replace with correct mood category image
- **Color clash:** Replace with similar color temperature image
- **Style clash:** Replace with matching style (all photos OR all abstract)
- **Human face in body slide:** Replace with background-focused image

---

### Issue: Pexels returns <5 results

**Diagnosis:**
- Query too specific (e.g., "dark moody office with coffee mug at 3pm")
- Rare subject matter
- Niche aesthetic

**Solutions:**
1. Use search_pexels_with_fallback (tries query variations automatically)
2. Broaden query (remove overly specific terms)
3. Try alternative mood keywords (see mood_categories.md)
4. Increase per_page to 15 (max)
5. If still insufficient, accept fewer results and select best available

---

### Issue: All local images rejected (insufficient quality)

**Diagnosis:**
- Local library needs updating
- Mood category underrepresented in library
- Slide context too specific for generic library

**Solutions:**
1. MUST use Pexels for this slide
2. Use search_pexels_with_fallback with broad query
3. Request 15 results for good selection pool
4. Use select_best_fitting_image to pick optimal candidate

---

### Issue: Agent keeps using only local images (never Pexels)

**Root Cause:** Rationalizing "good enough" without following checklist

**Prevention:**
- Follow Image Selection Checklist (MANDATORY)
- Enforce <3 candidates = MUST use Pexels rule
- Don't skip exhaustive local search step
- Verify workflow includes Pexels trigger checks

---

## Workflow Verification Checklist

Before finalizing any slideshow image selection:

- [ ] Followed Image Selection Checklist (SKILL.md)
- [ ] Tried 3+ category combinations for each mood
- [ ] Used Pexels for any mood with <3 local candidates
- [ ] Used slide_position parameter in all Pexels queries
- [ ] Used select_best_fitting_image for Pexels candidate selection
- [ ] Called verify_visual_consistency before finalizing
- [ ] Consistency score ≥7/10 achieved
- [ ] No outliers remaining unaddressed
- [ ] All images follow Single Protagonist Rule (no random faces in slides 2+)
- [ ] Mood arc makes logical sense (progression or consistent)

---

## Quick Reference: Tool Usage Matrix

| Scenario | Tool to Use | Parameters |
|----------|-------------|------------|
| Refresh local library | `sync_image_library()` | None |
| Specific Pexels query | `search_pexels(query, per_page, slide_position)` | per_page=10, slide_position=N |
| Broad/generic Pexels query | `search_pexels_with_fallback(query, per_page, slide_position)` | per_page=10, slide_position=N |
| Pick best from Pexels results | `select_best_fitting_image(candidates, context, slide_need, context_images)` | Include context_images |
| Verify final selections | `verify_visual_consistency(images, style, context)` | All selected image paths |

---

## Success Metrics

**A well-selected image set has:**
- ✅ Consistency score ≥7/10
- ✅ Zero outliers flagged
- ✅ Mood arc follows intended progression
- ✅ No human faces in body slides (unless intentional)
- ✅ High-quality, high-resolution images
- ✅ Text-image synergy (visuals support message)
- ✅ Platform-optimized (portrait, clean backgrounds, readable text space)
