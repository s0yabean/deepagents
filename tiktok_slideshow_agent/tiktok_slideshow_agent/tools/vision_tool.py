import os
import base64
import httpx
import asyncio
import json
from pathlib import Path
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Helper to resolve paths (similar to renderer.py)
def _resolve_path(path: str) -> str:
    current_file = Path(__file__).resolve()
    base_path = current_file.parent.parent.parent # tools -> tiktok_slideshow_agent -> PROJECT_ROOT
    image_library_path = base_path / "image_library"
    
    if path.startswith("/image_library/"):
        return path.replace("/image_library/", str(image_library_path) + "/")
    elif path.startswith("image_library/"):
        return path.replace("image_library/", str(image_library_path) + "/")
    return path

async def _load_image_data(path: str) -> str:
    """Load image data as base64 string from local path or URL."""
    path = _resolve_path(path)
    
    if path.startswith("http://") or path.startswith("https://"):
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(path)
                resp.raise_for_status()
                return base64.b64encode(resp.content).decode('utf-8')
        except Exception as e:
            print(f"Warning: Failed to load remote image {path}: {e}")
            return None
    else:
        # Local file
        def _read_file_sync(p):
            if not os.path.exists(p):
                return None
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')

        return await asyncio.to_thread(_read_file_sync, path)

@tool
async def verify_visual_consistency(image_paths: list[str], style_description: str, creative_context: str) -> str:
    """
    Analyzes the selected images for visual consistency using a Vision LLM.
    
    Args:
        image_paths: List of file paths (local) or URLs (remote).
        style_description: The intended visual style (e.g., "Minimalist", "Dark Cinematic", "Bright and Airy").
        creative_context: The creative rationale or topic (e.g., "Slideshow about stock trading stress").
        
    Returns:
        A critique of the visual consistency, identifying any outliers.
    """
    
    # Initialize Vision Model (Ephemeral instance just for this tool)
    # uses same API key from env
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.2)
    
    # Load images
    image_contents = []
    valid_indices = []
    
    for i, path in enumerate(image_paths):
        b64_data = await _load_image_data(path)
        if b64_data:
            image_contents.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}
            })
            valid_indices.append(i + 1)
        else:
            print(f"Warning: Could not load image at {path}")

    if not image_contents:
        return "Error: No valid images could be loaded for verification."

    # Construct Prompt
    prompt_text = f"""
    You are an expert Art Director. I am showing you {len(image_contents)} images selected for a TikTok slideshow.
    
    **Context**: {creative_context}
    **Intended Style**: {style_description}
    
    **Your Task**:
    1.  Analyze if these images form a cohesive visual set suitable for the context.
    2.  Identify any outliers that clash with the group or the intended style (e.g. mixture of 3D render vs Photo-realism, or moody vs bright).
    3.  Provide a specific recommendation for any outlier.
    
    **Constraint**: Do NOT critique specific product details (e.g. missing logos, specific UI screens, or text on screen) as these are stock placeholders. Focus ONLY on visual style, mood, and lighting consistency.
    
    **Policy: The "Single Protagonist" Rule**:
    - Slide 1 (The Hook) MAY have a human subject/face to stop the scroll.
    - Slides 2+ MUST NOT feature a clear human face/body as the main subject. This is to prevent "character jumping" (confusing the viewer with different actors).
    - If Slide 2, 3, 4, or 5 has a prominent human face, FLAG IT AS AN OUTLIER immediately unless it is the EXACT same actor from Slide 1 (unlikely for stock usage).
    - Hands/partial body parts interacting with objects are acceptable. Full distinct people are NOT.
    
    **Images are provided in order (Slide {valid_indices[0]} to Slide {valid_indices[-1]}).**
    
    Return your feedback in this format:
    - **Consistency Score**: X/10
    - **Overall Vibe**: [Describe what you see]
    - **Outliers**: [None OR "Slide X is too dark/abstract compared to others"]
    - **Recommendation**: [Keep all OR "Replace Slide X with a generic office background"]
    """
    
    content_parts = [{"type": "text", "text": prompt_text}] + image_contents
    
    message = HumanMessage(content=content_parts)
    
    try:
        response = await llm.ainvoke([message])
        return response.content
    except Exception as e:
        return f"Error running visual verification: {str(e)}"

@tool
async def select_best_fitting_image(candidate_urls: list[str], creative_context: str, slide_need: str, context_image_paths: list[str] = []) -> str:
    """
    Selects the best image from a list of candidates using a Vision LLM, considering context images.
    
    Args:
        candidate_urls: List of image URLs to evaluate.
        creative_context: The overall topic/theme of the slideshow.
        slide_need: Description of what this specific slide needs.
        context_image_paths: (Optional) List of paths/URLs of OTHER images already selected for the slideshow (to ensure consistency).
    
    Returns:
        JSON string with the best image URL and rationale.
    """
    
    # Initialize Vision Model
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.1)
    
    message_content = []
    
    # 1. Load Context Images (if any)
    context_count = 0
    if context_image_paths:
        message_content.append({"type": "text", "text": "**Step 1: Reference Images**\nThe following images are already selected for this slideshow. Use them to understand the established visual style (color grading, lighting, subject matter)."})
        for path in context_image_paths:
            b64_data = await _load_image_data(path)
            if b64_data:
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}
                })
                context_count += 1
            else:
                print(f"Warning: Could not load context image {path}")

    # 2. Load Candidate Images
    candidate_contents = []
    valid_candidate_urls = []
    
    message_content.append({"type": "text", "text": f"\n**Step 2: Candidate Selection**\nHere are {len(candidate_urls)} candidate images for the NEXT slide. Which one best fits the 'Slide Goal' AND matches the style of the Reference Images above?"})

    for i, url in enumerate(candidate_urls):
        b64_data = await _load_image_data(url)
        if b64_data:
            # We add a label before each candidate to make it easy for LLM to id
            message_content.append({"type": "text", "text": f"Candidate {i+1}:"})
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}
            })
            valid_candidate_urls.append(url)
        else:
            print(f"Warning: Could not load candidate {url}")
            
    if not valid_candidate_urls:
        return json.dumps({"error": "No valid candidate images could be loaded."})
        
    prompt_text = f"""
    You are an expert Art Director.
    
    **Context**: {creative_context}
    **Slide Goal**: {slide_need}
    
    **Task**: Select the ONE candidate image that best fits the context, goal, and visual consistency of the Reference Images.
    
    **CRITICAL CONSTRAINT: The "Single Protagonist" Rule**:
    - Unless the 'Slide Goal' EXPLICITLY asks for a human subject (rare for non-hook slides):
    - **Prefer images WITHOUT people** (scenery, objects, hands, abstract).
    - If a candidate has a clear, distinct human face that is NOT the same actor as Slide 1, **PENALIZE IT HEAVILY**.
    - We want to avoid "random stock photo people" appearing in the middle of the story.
    
    Return ONLY a JSON object:
    {{
        "best_candidate_number": <int, 1-based index (e.g. 1 for Candidate 1)>,
        "rationale": "<string explanation>"
    }}
    """
    
    # Append the prompt at the end
    message_content.append({"type": "text", "text": prompt_text})
    
    message = HumanMessage(content=message_content)
    
    try:
        response = await llm.ainvoke([message])
        content = response.content.replace('```json', '').replace('```', '').strip()
        result = json.loads(content)
        
        # Parse 1-based index to 0-based
        best_num = result.get("best_candidate_number", 1)
        idx = best_num - 1
        
        # Boundary check
        if idx < 0 or idx >= len(valid_candidate_urls):
            idx = 0
            
        return json.dumps({
            "best_url": valid_candidate_urls[idx],
            "rationale": result.get("rationale", "Selected by AI")
        })
        
    except Exception as e:
        return json.dumps({"error": f"Selection failed: {str(e)}", "best_url": valid_candidate_urls[0] if valid_candidate_urls else None})
