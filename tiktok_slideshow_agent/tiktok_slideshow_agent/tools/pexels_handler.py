"""
Pexels Handler - Non-blocking Pexels API integration with retry logic and fallback strategies.
Integrated from skills/visual-designer-skill/scripts/pexels_handler.py
"""

import asyncio
import os
import json
from typing import List, Dict, Any, Optional
import httpx
from langchain_core.tools import tool


class PexelsHandler:
    """Handles Pexels API interactions with non-blocking operations and fallback strategies."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 10):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://api.pexels.com/v1/search"
        self.max_retries = 3
        self.retry_delay = 1.0

    async def search_images(
        self, query: str, per_page: int = 5, orientation: str = "portrait", slide_position: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Search for images on Pexels with non-blocking HTTP requests and auto-query optimization.
        Returns list of image metadata with URLs.
        """
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not configured")

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

        # Limit per_page to reasonable bounds
        per_page = min(max(per_page, 1), 15)

        params = {
            "query": enhanced_query,
            "orientation": orientation,
            "per_page": per_page,
            "page": 1,
        }

        headers = {"Authorization": self.api_key}

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(
                        self.base_url, params=params, headers=headers
                    )

                    if response.status_code == 200:
                        data = response.json()
                        photos = data.get("photos", [])

                        results = []
                        for photo in photos:
                            results.append(
                                {
                                    "id": photo["id"],
                                    "url": photo["src"]["portrait"],  # Pre-cropped portrait
                                    "photographer": photo["photographer"],
                                    "alt": photo.get("alt", "No description"),
                                    "avg_color": photo.get("avg_color", ""),
                                    "width": photo["width"],
                                    "height": photo["height"],
                                }
                            )

                        return results

                    elif response.status_code == 429:  # Rate limited
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2**attempt))
                            continue
                        else:
                            raise Exception(
                                f"Rate limited after {self.max_retries} attempts"
                            )

                    else:
                        raise Exception(f"Pexels API error: {response.status_code}")

            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise Exception(
                        f"Request timed out after {self.max_retries} attempts"
                    )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise Exception(f"Pexels search failed: {str(e)}")

        return []

    async def search_with_fallback(
        self,
        primary_query: str,
        fallback_queries: Optional[List[str]] = None,
        per_page: int = 5,
        slide_position: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Search with fallback queries if primary search yields insufficient results.
        Automatically generates smart fallback queries with mood keywords and modifiers.
        """
        if fallback_queries is None:
            # Smart fallback generation
            fallback_queries = [
                f"{primary_query} aesthetic",
                f"{primary_query} texture",
                f"{primary_query} minimalist",
            ]

        # Try primary query first
        results = await self.search_images(primary_query, per_page, slide_position=slide_position)
        if len(results) >= per_page:
            return results

        # Try fallback queries
        for fallback_query in fallback_queries:
            if len(results) >= per_page:
                break

            try:
                fallback_results = await self.search_images(
                    fallback_query,
                    per_page=min(per_page - len(results), 5),
                    slide_position=slide_position
                )
                results.extend(fallback_results)
            except Exception:
                continue  # Skip failed fallback queries

        return results[:per_page]


@tool
async def search_pexels_with_fallback(query: str, per_page: int = 5, slide_position: int = 1) -> str:
    """Search Pexels with automatic fallback queries if primary search yields insufficient results.

    This tool tries the primary query first, then automatically tries variations with
    aesthetic modifiers (aesthetic, texture, minimalist) if needed to get enough results.

    Args:
        query: Primary search keywords (e.g., "dark moody office", "bright beach").
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
    handler = PexelsHandler()
    try:
        results = await handler.search_with_fallback(query, per_page=per_page, slide_position=slide_position)
        if not results:
            return json.dumps({"message": f"No results found for query: {query}"})
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": f"Pexels search with fallback failed: {str(e)}"})
