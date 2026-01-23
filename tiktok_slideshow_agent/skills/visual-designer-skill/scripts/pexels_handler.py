"""
Pexels Handler - Non-blocking Pexels API integration with retry logic.
Handles image search, download, and fallback strategies for visual design workflow.
"""

import asyncio
import os
import json
import time
from typing import List, Dict, Any, Optional
import httpx


class PexelsHandler:
    """Handles Pexels API interactions with non-blocking operations."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 10):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://api.pexels.com/v1/search"
        self.max_retries = 3
        self.retry_delay = 1.0

    async def search_images(
        self, query: str, per_page: int = 5, orientation: str = "portrait"
    ) -> List[Dict[str, Any]]:
        """
        Search for images on Pexels with non-blocking HTTP requests.
        Returns list of image metadata with URLs.
        """
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not configured")

        # Limit per_page to reasonable bounds
        per_page = min(max(per_page, 1), 15)

        params = {
            "query": query,
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
                                    "url": photo["src"][
                                        "portrait"
                                    ],  # Pre-cropped portrait
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
    ) -> List[Dict[str, Any]]:
        """
        Search with fallback queries if primary search yields insufficient results.
        """
        if fallback_queries is None:
            fallback_queries = [
                f"{primary_query} background",
                f"{primary_query} aesthetic",
                f"{primary_query} texture",
            ]

        # Try primary query first
        results = await self.search_images(primary_query, per_page)
        if len(results) >= per_page:
            return results

        # Try fallback queries
        for fallback_query in fallback_queries:
            if len(results) >= per_page:
                break

            try:
                fallback_results = await self.search_images(
                    fallback_query, per_page=min(per_page - len(results), 5)
                )
                results.extend(fallback_results)
            except Exception:
                continue  # Skip failed fallback queries

        return results[:per_page]


async def search_pexels_non_blocking(
    query: str,
    per_page: int = 5,
    orientation: str = "portrait",
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Main entry point for non-blocking Pexels search.
    Compatible with existing tool interface.
    """
    handler = PexelsHandler(api_key)
    return await handler.search_images(query, per_page, orientation)


async def search_pexels_fallback(
    query: str, needed: int = 5, api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Pexels with intelligent fallback strategies for visual design.
    """
    handler = PexelsHandler(api_key)
    return await handler.search_with_fallback(query, per_page=needed)
