# TikTok Visual Guidelines

Platform-specific visual requirements and best practices for TikTok slideshow content.

## Technical Requirements

### Aspect Ratio & Dimensions
- **Primary Format:** 9:16 (Portrait/Vertical)
- **Recommended Resolution:** 1080x1920 pixels minimum
- **Safe Zone:** Keep critical text/subjects within center 80% of frame
- **Status Bar Clearance:** Top 10% may be covered by status bar/notification

### File Specifications
- **Format:** MP4, MOV (after rendering slides to video)
- **Frame Rate:** 30fps minimum
- **Duration:** 15-60 seconds optimal (3-12 slides at 5 seconds each)
- **Max File Size:** 287.6 MB (though platform prefers <100 MB)

---

## Visual Content Rules

### The "Single Protagonist" Rule ⭐ **CRITICAL**

**Problem:** Random stock photos of different people across slides break narrative immersion and confuse viewers about whose "story" this is.

**Rule:**
- **Slide 1 (Hook):** MAY feature a human subject/face to stop the scroll
- **Slides 2+:** MUST NOT feature distinct human faces as the main subject

**Rationale:**
- Prevents "character jumping" (viewer confusion from seeing different actors)
- Maintains consistent POV (point-of-view)
- Focuses attention on the message, not random stock people

**Acceptable in Slides 2+:**
- Hands interacting with objects
- Partial body parts (no face visible)
- Silhouettes or heavily obscured figures
- Crowd scenes (no individual faces distinguishable)
- Background people (out of focus, not main subject)

**Not Acceptable in Slides 2+:**
- Close-up portraits of different people
- Multiple distinct faces across slides
- Any clearly identifiable human subject

**Implementation:**
- Pexels queries for slides 2+ automatically append "no people background"
- `verify_visual_consistency` flags slides with faces as outliers
- `select_best_fitting_image` penalizes candidates with human faces for non-hook slides

---

## Platform-Specific Visual Strategies

### Hook Slide (Slide 1) Requirements

**Purpose:** Stop the scroll within 0.5-1 second

**Visual Strategies:**
1. **High Contrast:** Bold colors, strong blacks/whites
2. **Human Face (Optional):** Eye contact with camera can increase engagement
3. **Text Placement:** Center-weighted, large font (avoid top/bottom 15%)
4. **Motion Hint:** Slight zoom/pan in video to signal "this is starting"

**Don't:**
- Overly busy backgrounds (text becomes unreadable)
- Low contrast text on similar-colored backgrounds
- Tiny text (must be readable on mobile)

### Body Slides (Slides 2-5) Requirements

**Purpose:** Deliver narrative without distraction

**Visual Strategies:**
1. **Background-Focused:** Images support text, don't compete
2. **Consistent Style:** Maintain visual flow from slide to slide
3. **Text Hierarchy:** Primary message clearly dominant
4. **Clean Composition:** Avoid cluttered backgrounds

**Don't:**
- Switch visual styles mid-narrative (moody→bright→moody)
- Use images that contradict the text message
- Include watermarks, logos, or text in background images

### CTA Slide (Final Slide) Requirements

**Purpose:** Drive engagement action (save, follow, comment)

**Visual Strategies:**
1. **Bright/Aspirational:** Positive, hopeful visuals
2. **Clean Space:** Room for CTA text without crowding
3. **Energy Shift:** Slightly more vibrant than body slides
4. **Visual Closure:** Signals "end of story"

**Don't:**
- Revert to moody visuals (breaks positive momentum)
- Overly complex backgrounds (CTA should be clear)
- Use same exact image as earlier slide (feels lazy)

---

## Visual Consistency Standards

### Color Grading Coherence

**Acceptable Variations Within a Slideshow:**
- ±20% luminosity between slides
- Gradual temperature shifts (moody→bright arc)
- Consistent saturation level within mood category

**Unacceptable Variations:**
- Sudden jumps (dark→bright→dark)
- Mixing color and black-and-white
- Conflicting color temperatures (warm and cool) without arc logic

### Composition Consistency

**Preferred:**
- Similar framing styles (all wide, or all close-up)
- Consistent rule-of-thirds placement
- Unified perspective (all eye-level OR all aerial)

**Avoid:**
- Random mix of perspectives
- Inconsistent subject placement
- Clashing compositional styles

---

## TikTok Engagement Patterns

### Visual Elements That Increase Watch Time

1. **Progressive Reveal:** Each slide adds new visual info (not repetitive)
2. **Mood Progression:** Clear emotional arc (moody→bright works best)
3. **Text-Image Synergy:** Visuals reinforce the text message
4. **Quality Signaling:** High-res, professional-looking images

### Visual Elements That Decrease Watch Time

1. **Static Repetition:** Same visual style all the way through (in narrative formats)
2. **Poor Image Quality:** Pixelated, compressed, watermarked images
3. **Text Clutter:** Too much text on busy backgrounds
4. **Visual Confusion:** Images contradict or distract from message

---

## Platform Algorithm Preferences

### What TikTok Rewards (Based on PRD Observations)

**High Completion Rate:**
- Clear narrative progression (visual arc supports this)
- Consistent visual quality
- Mobile-optimized text sizing

**High Engagement (Saves/Shares):**
- Aspirational final slides (bright, positive visuals)
- Visually distinct hook (stops scroll)
- Professional, cohesive aesthetic

**High Relevance Score:**
- Topic-image alignment (visuals match content theme)
- Platform-native feel (vertical format, clean design)
- Recent trends (minimalist, cinematic aesthetics popular in 2026)

---

## Common Visual Mistakes on TikTok

### ❌ Mistake 1: Horizontal Images Cropped to Vertical
**Problem:** Looks unprofessional, loses key visual elements
**Solution:** Use portrait-oriented images from start (Pexels orientation: "portrait")

### ❌ Mistake 2: Text Over Faces
**Problem:** Accessibility (face partially hidden) + distracting
**Solution:** Use background-focused images for text-heavy slides

### ❌ Mistake 3: Overused Stock Photos
**Problem:** Viewer fatigue ("I've seen this image 100 times")
**Solution:** Use lesser-known stock sources, Pexels' deeper catalog

### ❌ Mistake 4: Inconsistent Aesthetic
**Problem:** Looks like a random slideshow, not a crafted story
**Solution:** Follow mood arcs, verify consistency before publishing

### ❌ Mistake 5: Ignoring Safe Zones
**Problem:** Text/subjects cut off by UI elements
**Solution:** Keep key elements within center 80% of frame

---

## Visual Testing Checklist

Before finalizing slideshow images:

- [ ] All images portrait-oriented (9:16 aspect ratio)
- [ ] Hook slide passes "stop the scroll" test (bold, high-contrast)
- [ ] No distinct human faces in slides 2+ (Single Protagonist Rule)
- [ ] Mood arc progression makes sense (moody→bright or consistent)
- [ ] `verify_visual_consistency` score ≥7/10
- [ ] No outliers flagged by verification tool
- [ ] Text-image synergy (visuals support message)
- [ ] Clean backgrounds (no watermarks, clutter, text)
- [ ] Final CTA slide is bright/aspirational
- [ ] All images high-resolution (no pixelation)

---

## Platform Trends (2026)

### Currently Popular Visual Styles
1. **Minimalist Aesthetic:** Clean, white/neutral backgrounds
2. **Cinematic Grading:** Film-like color tones (teal-orange, moody blues)
3. **Soft Lighting:** Natural, diffused light (not harsh studio lighting)
4. **Texture Focus:** Backgrounds with subtle texture (not flat)

### Declining Styles (Avoid)
1. **Overly Filtered:** Instagram-style heavy filters
2. **Clip Art:** Cartoon/graphic elements (unless intentional brand style)
3. **Stock Photo Clichés:** Forced smiles, handshake photos, generic office
4. **Neon/Cyberpunk:** Over-saturated neon aesthetics (2023-2024 trend)

---

## Accessibility Considerations

### Visual Accessibility
- **Contrast Ratio:** Minimum 4.5:1 for text-on-background
- **Color Blindness:** Don't rely solely on color to convey information
- **Motion Sensitivity:** Avoid rapid flashing or strobing effects

### Mobile-First Design
- **Thumb Zone:** Keep interactive hints (e.g., "swipe up") in bottom 30%
- **Readability:** Text must be readable on smallest TikTok-supported screens
- **Touch Targets:** If using interactive elements, minimum 44x44 pixels

---

## Reference Workflows

### For Moody→Bright Arc (5 slides)
1. **Slide 1 (Hook):** Bold/moody hybrid (high contrast, attention-grabbing)
2. **Slide 2 (Problem):** Deep moody (dark, cinematic, struggle)
3. **Slide 3 (Discovery):** Transitional (neutral, soft light, turning point)
4. **Slide 4 (Solution):** Bright (airy, aspirational, hopeful)
5. **Slide 5 (CTA):** Bright (clean, positive, call-to-action ready)

### For Consistent Style (Listicle)
- **All Slides:** Same category (e.g., all `minimalist_bright`)
- **Variation:** Change subject, not style (desk→coffee→window, all minimalist)
- **Avoid:** Mixing categories even slightly (breaks cohesion)

---

## Emergency Fallbacks

### If Local Library Is Empty for a Category
1. Use `search_pexels_with_fallback` (tries multiple query variations)
2. Start with per_page=10 for selection pool
3. Use `select_best_fitting_image` to pick best candidate with context

### If Pexels Returns Poor Results
1. Increase per_page to 15
2. Try alternative mood keywords (see mood_categories.md)
3. If still insufficient, reuse a strong local image (better than bad Pexels image)

### If Consistency Check Fails (<7/10)
1. Identify outlier slides from verification feedback
2. Search for replacements targeting the outlier slides
3. Re-verify after replacement
4. If still failing after 2 attempts, adjust arc (e.g., make all slides same mood)
