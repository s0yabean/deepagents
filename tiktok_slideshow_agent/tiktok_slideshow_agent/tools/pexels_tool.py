from langchain_core.tools import tool
import os
import httpx
import json

@tool
def search_pexels(query: str, per_page: int = 5, slide_position: int = 1) -> str:
    """Search for high-quality, portrait-oriented images on Pexels with automatic query optimization.

    Use this when local image library is insufficient.

    Args:
        query: Search keywords (e.g., "minimalist beach sunset", "dark moody city").
        per_page: Number of images to return (default: 5, max: 15).
        slide_position: Slide number (1-based). Used to auto-optimize query.
                       Slide 1 (Hook): Allows people in images.
                       Slides 2+: Automatically appends "no people background" for consistency.

    Returns:
        JSON string containing list of image objects:
        [{
            "id": 123,
            "url": "https://...",
            "photographer": "Name",
            "avg_color": "#Hex",
            "alt": "Description"
        }]
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return json.dumps({"error": "PEXELS_API_KEY not found in environment settings."})

    # Auto-enhance query based on slide position (Single Protagonist Rule)
    enhanced_query = query
    if slide_position > 1:
        # Body slides: enforce no-people constraint for visual consistency
        if "no people" not in query.lower() and "background" not in query.lower():
            enhanced_query = f"{query} no people background"
        elif "no people" not in query.lower():
            enhanced_query = f"{query} no people"
        elif "background" not in query.lower():
            enhanced_query = f"{query} background"

    # Strict limits to respect rate limiting (200/hour)
    limit = min(per_page, 15)
    
    # Force portrait (9:16 aspect ratio roughly)
    params = {
        "query": enhanced_query,
        "orientation": "portrait",
        "per_page": limit,
        "page": 1
    }
    
    headers = {
        "Authorization": api_key
    }
    
    try:
        # Using synchronous httpx call inside the tool 
        # (tools are synchronous by default in this agent setup unless async is explicitly handled)
        with httpx.Client() as client:
            response = client.get("https://api.pexels.com/v1/search", params=params, headers=headers, timeout=10.0)
            
        if response.status_code != 200:
            return json.dumps({
                "error": f"Pexels API Error: {response.status_code}",
                "details": response.text
            })
            
        data = response.json()
        photos = data.get("photos", [])
        
        results = []
        for p in photos:
            # We prefer 'original' if it's high quality, or 'portrait' size if bandwidth is concern.
            # Using 'src.portrait' ensures it fits the aspect ratio well (1200x800 cropped).
            # But 'original' is safer for maximizing quality.
            # Let's provide both mapped to 'url'
            image_url = p["src"]["portrait"] # Pre-cropped to portrait is often safer for 9:16
            
            results.append({
                "id": p["id"],
                "url": image_url,
                "photographer": p["photographer"],
                "avg_color": p.get("avg_color", ""),
                "alt": p.get("alt", "No description")
            })
            
        if not results:
            return json.dumps({"message": f"No results found for query: {query}"})
            
        return json.dumps(results)
        
    except Exception as e:
        return json.dumps({"error": f"Exception calling Pexels: {str(e)}"})
