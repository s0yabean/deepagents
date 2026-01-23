"""
Image Selector - Core image selection algorithms for visual design workflow.
Provides mood-based selection with fallback strategies and non-blocking operations.
"""

import asyncio
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class ImageSelector:
    """Handles image selection based on mood arcs and creative briefs."""

    def __init__(self, image_library_path: Optional[str] = None):
        self.image_library_path = (
            Path(image_library_path) if image_library_path else None
        )
        self.metadata_file = (
            (self.image_library_path / "images.json")
            if self.image_library_path
            else None
        )
        self._images: Optional[List[Dict[str, Any]]] = None

    async def load_images(self) -> List[Dict[str, Any]]:
        """Load image metadata asynchronously."""
        if self._images is not None:
            return self._images

        if not self.metadata_file or not self.metadata_file.exists():
            self._images = []
            return []

        def _load_sync():
            if self.metadata_file and self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            return []

        loaded_images = await asyncio.to_thread(_load_sync)
        self._images = loaded_images
        return loaded_images

        if not self.metadata_file or not self.metadata_file.exists():
            return []

        def _load_sync():
            with open(self.metadata_file, "r") as f:
                return json.load(f)

        self._images = await asyncio.to_thread(_load_sync)
        return self._images

    async def select_for_mood(self, mood: str, count: int = 1) -> List[Dict[str, Any]]:
        """Select images matching a specific mood category."""
        images = await self.load_images()

        # Mood to category mapping
        mood_mapping = {
            "moody": ["cinematic_moody", "art_surreal"],
            "transitional": ["minimalist_bright"],
            "bright": ["minimalist_bright"],
            "bold": ["art_surreal", "cinematic_moody"],
            "lifestyle": ["minimalist_bright", "cinematic_moody"],
            "mysterious": ["cinematic_moody", "art_surreal"],
        }

        preferred_categories = mood_mapping.get(mood, ["minimalist_bright"])
        candidates = []

        for img in images:
            if img.get("category") in preferred_categories:
                img_copy = img.copy()
                img_copy["absolute_path"] = str(
                    self.image_library_path / img["category"] / img["filename"]
                )
                candidates.append(img_copy)

        # Return up to requested count
        return candidates[:count]

    async def select_for_arc(
        self, image_arc: List[str], slide_count: int
    ) -> List[Dict[str, Any]]:
        """Select images following a mood progression arc."""
        if len(image_arc) != slide_count:
            raise ValueError(
                f"Arc length ({len(image_arc)}) must match slide count ({slide_count})"
            )

        selections = []
        for mood in image_arc:
            mood_images = await self.select_for_mood(mood, 1)
            if mood_images:
                selections.extend(mood_images)
            else:
                # Fallback to any available image
                all_images = await self.load_images()
                if all_images:
                    fallback = all_images[0].copy()
                    fallback["absolute_path"] = str(
                        self.image_library_path
                        / fallback["category"]
                        / fallback["filename"]
                    )
                    selections.append(fallback)

        return selections


async def select_images_for_arc(
    image_arc: List[str], slide_count: int, library_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Main entry point for arc-based selection."""
    selector = ImageSelector(library_path)
    return await selector.select_for_arc(image_arc, slide_count)


async def select_images_for_mood(
    mood: str, count: int = 1, library_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Main entry point for mood-based selection."""
    selector = ImageSelector(library_path)
    return await selector.select_for_mood(mood, count)
