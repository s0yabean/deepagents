# Mood Categories Reference

Comprehensive guide to visual mood categories for TikTok slideshow image selection.

## Core Mood Categories

### Moody
**Definition:** Dark, cinematic, tension-building visuals that convey struggle, complexity, or depth.

**Visual Characteristics:**
- Low-key lighting (shadows dominate, minimal highlights)
- Desaturated or muted color palette
- Cool tones (blues, grays, dark greens)
- High contrast between light and shadow
- Cinematic grain or texture

**Best Used For:**
- Problem slides (slides 2-3 in transformation stories)
- Establishing tension or conflict
- "Before" states in before/after narratives
- Introspective or serious topics

**Local Library Categories:**
- `cinematic_moody` (primary)
- `art_surreal` (for abstract moody vibes)

**Pexels Query Keywords:**
- "dark cinematic [subject]"
- "moody shadows [context]"
- "dramatic lighting [scene]"
- Examples: "dark moody office", "cinematic shadows city night"

---

### Transitional
**Definition:** Neutral bridge between moody and bright, representing the turning point or discovery moment.

**Visual Characteristics:**
- Balanced lighting (neither too dark nor too bright)
- Soft, diffused light
- Moderate saturation
- Warm-neutral color temperature
- Clean, minimal composition

**Best Used For:**
- Discovery slides (slide 3 in 5-slide arcs)
- Transition moments in narratives
- Product introduction slides
- "Aha moment" representations

**Local Library Categories:**
- `minimalist_bright` (softer, muted images)
- `cinematic_moody` (lighter, less dramatic images)

**Pexels Query Keywords:**
- "soft light [subject]"
- "neutral [context] background"
- "clean minimal [scene]"
- Examples: "soft natural light desk", "neutral workspace aesthetic"

---

### Bright
**Definition:** Light, aspirational, hopeful visuals that convey solutions, success, or positive transformation.

**Visual Characteristics:**
- High-key lighting (abundant highlights, minimal shadows)
- Saturated or vibrant color palette
- Warm tones (golds, whites, pastels)
- Airy, spacious composition
- Clean, polished aesthetic

**Best Used For:**
- Solution slides (slides 4-5 in transformation stories)
- "After" states in before/after narratives
- CTA slides (call-to-action)
- Aspirational lifestyle content

**Local Library Categories:**
- `minimalist_bright` (primary)

**Pexels Query Keywords:**
- "bright airy [subject]"
- "light minimalist [context]"
- "clean white [scene]"
- Examples: "bright minimalist room", "airy white workspace"

---

### Bold
**Definition:** High-contrast, attention-grabbing visuals with dramatic impact.

**Visual Characteristics:**
- Extreme contrast (strong blacks and whites)
- Vivid, saturated colors
- Dynamic composition (diagonal lines, asymmetry)
- Eye-catching focal points
- Abstract or geometric elements

**Best Used For:**
- Hook slides (slide 1) to stop the scroll
- Statement slides with bold text
- Listicle headers
- Attention-demanding moments

**Local Library Categories:**
- `art_surreal` (primary for abstract bold)
- `cinematic_moody` (for dramatic high-contrast)

**Pexels Query Keywords:**
- "bold contrast [subject]"
- "dramatic [context]"
- "high contrast [scene]"
- Examples: "bold geometric abstract", "dramatic contrast architecture"

---

### Lifestyle
**Definition:** Relatable, everyday scenarios that connect with viewer experiences.

**Visual Characteristics:**
- Natural, candid-feeling composition
- Moderate lighting (neither dramatic nor flat)
- Warm, inviting color palette
- Human-scale perspective
- Contextual details (everyday objects, familiar settings)

**Best Used For:**
- POV (point-of-view) content
- Relatable narrative slides
- "You" or "Your" oriented messaging
- Everyday problem/solution contexts

**Local Library Categories:**
- `minimalist_bright` (lifestyle-oriented images)
- `cinematic_moody` (casual lifestyle shots)

**Pexels Query Keywords:**
- "lifestyle [context]"
- "everyday [scene]"
- "casual [subject]"
- Examples: "lifestyle morning coffee", "everyday workspace aesthetic"

---

### Mysterious
**Definition:** Intriguing, shadowy visuals that create curiosity and suspense.

**Visual Characteristics:**
- Partially obscured subjects
- Shallow depth of field (selective focus)
- Deep shadows with hints of light
- Ambiguous composition
- Cool, dark color palette

**Best Used For:**
- Secret/insider content format
- Mystery-solving narratives
- "What they don't tell you" hooks
- Teaser slides

**Local Library Categories:**
- `cinematic_moody` (primary)
- `art_surreal` (for abstract mystery)

**Pexels Query Keywords:**
- "mysterious shadows [subject]"
- "dark atmospheric [context]"
- "shadowy [scene]"
- Examples: "mysterious dark hallway", "shadowy silhouette aesthetic"

---

### Consistent
**Definition:** Unified visual style throughout all slides (no mood progression).

**Visual Characteristics:**
- Same lighting style across all slides
- Consistent color palette
- Uniform saturation levels
- Matching composition style
- Cohesive aesthetic identity

**Best Used For:**
- Listicle format (7 tips, 5 signs, etc.)
- Educational content
- Step-by-step tutorials
- Brand-focused content

**Selection Strategy:**
- Pick ONE category and stick with it for all slides
- Examples: All `minimalist_bright` OR all `cinematic_moody`
- Avoid mixing categories in this format

**Pexels Query Keywords:**
- Use the same base query for all slides
- Add slide-specific context (e.g., "minimalist office", "minimalist desk", "minimalist workspace")

---

## Mood Progression Arcs

### Classic Transformation Arc (5 slides)
```
["moody", "moody", "transitional", "bright", "bright"]
```
- Slides 1-2: Establish problem/struggle (moody)
- Slide 3: Discovery/turning point (transitional)
- Slides 4-5: Solution/success (bright)

### Fast Transformation Arc (4 slides)
```
["moody", "transitional", "bright", "bright"]
```
- Slide 1: Problem (moody)
- Slide 2: Discovery (transitional)
- Slides 3-4: Solution (bright)

### Mystery-Reveal Arc (5 slides)
```
["mysterious", "mysterious", "transitional", "bold", "bright"]
```
- Slides 1-2: Build intrigue (mysterious)
- Slide 3: Revelation moment (transitional)
- Slide 4: Big reveal (bold)
- Slide 5: Call-to-action (bright)

---

## Selection Decision Trees

### When Local Library Lacks Sufficient Candidates

**If <3 candidates for a mood category:**
1. Use Pexels with optimized query
2. Start with per_page=10 for good selection pool
3. Use `select_best_fitting_image` with context

**If local library is completely empty for a category:**
1. Use `search_pexels_with_fallback` (tries multiple query variations)
2. Increase per_page to 15 if initial results insufficient
3. Verify consistency before finalizing

---

## Common Pitfalls

### ❌ Wrong: Rationalizing "Good Enough"
- "This minimalist_bright image is close enough for moody"
- **Impact:** Breaks arc progression, confuses viewer

### ✅ Right: Strict Mood Adherence
- "This doesn't match moody criteria → search Pexels"
- **Impact:** Maintains narrative flow

### ❌ Wrong: Generic Queries
- Query: "office"
- **Result:** Random mix of moody/bright/lifestyle

### ✅ Right: Mood-Enhanced Queries
- Query: "dark moody office cinematic"
- **Result:** Targeted mood match

### ❌ Wrong: Skipping Consistency Check
- Assume images work together without verification
- **Result:** Outliers break visual flow

### ✅ Right: Mandatory Verification
- Always call `verify_visual_consistency` before finalizing
- **Result:** Catch outliers before they ship
