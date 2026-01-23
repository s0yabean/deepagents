"""
Library Manager - Image library synchronization and management.
Handles metadata updates, path resolution, and library maintenance.
"""

import asyncio
import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path


class LibraryManager:
    """Manages image library synchronization and metadata."""

    def __init__(self, library_path: Optional[str] = None):
        self.library_path = Path(library_path) if library_path else None
        self.metadata_file = (
            self.library_path / "images.json" if self.library_path else None
        )
        self._metadata: Optional[Dict[str, Any]] = None

    async def sync_library(self) -> Dict[str, Any]:
        """
        Synchronize image library by scanning directories and updating metadata.
        Returns sync results with statistics.
        """
        if not self.library_path or not self.library_path.exists():
            return {
                "status": "error",
                "message": "Library path not found",
                "stats": {"scanned": 0, "updated": 0, "errors": 1},
            }

        try:
            # Load existing metadata
            existing_images = await self._load_metadata()

            # Scan directories
            found_images = await self._scan_directories()

            # Update metadata
            updated_metadata, stats = await self._update_metadata(
                existing_images, found_images
            )

            # Save updated metadata
            await self._save_metadata(updated_metadata)

            return {
                "status": "success",
                "message": f"Library sync completed: {stats['updated']} updated, {stats['new']} new",
                "stats": stats,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Sync failed: {str(e)}",
                "stats": {"scanned": 0, "updated": 0, "errors": 1},
            }

    async def _load_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load existing metadata asynchronously."""
        if not self.metadata_file or not self.metadata_file.exists():
            return {"images": []}

        def _load_sync():
            if self.metadata_file:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            return {"images": []}

        try:
            return await asyncio.to_thread(_load_sync)
        except Exception:
            return {"images": []}

    async def _scan_directories(self) -> List[Dict[str, Any]]:
        """Scan library directories for image files."""
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        found_images = []

        def _scan_sync():
            images = []
            if not self.library_path:
                return images

            for category_dir in self.library_path.iterdir():
                if not category_dir.is_dir():
                    continue

                category_name = category_dir.name
                for image_file in category_dir.iterdir():
                    if not image_file.is_file():
                        continue

                    if image_file.suffix.lower() not in image_extensions:
                        continue

                    # Generate ID from file path
                    file_path = str(image_file.relative_to(self.library_path))
                    image_id = hashlib.md5(file_path.encode()).hexdigest()[:8]

                    images.append(
                        {
                            "id": image_id,
                            "filename": image_file.name,
                            "category": category_name,
                            "path": file_path,
                            "size": image_file.stat().st_size,
                            "modified": image_file.stat().st_mtime,
                        }
                    )

            return images

        return await asyncio.to_thread(_scan_sync)

    async def _update_metadata(
        self, existing: Dict[str, List[Dict[str, Any]]], found: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Update metadata with found images."""
        existing_images = {img["id"]: img for img in existing.get("images", [])}
        stats = {"scanned": len(found), "updated": 0, "new": 0, "removed": 0}

        updated_images = []

        # Process found images
        for found_img in found:
            img_id = found_img["id"]

            if img_id in existing_images:
                # Check if file changed
                existing_img = existing_images[img_id]
                if (
                    existing_img.get("modified", 0) != found_img["modified"]
                    or existing_img.get("size", 0) != found_img["size"]
                ):
                    # Update existing
                    updated_img = existing_img.copy()
                    updated_img.update(found_img)
                    updated_images.append(updated_img)
                    stats["updated"] += 1
                else:
                    # Keep existing (may have additional metadata)
                    updated_images.append(existing_img)
            else:
                # New image
                updated_images.append(found_img)
                stats["new"] += 1

        # Note: Removed images detection would require additional logic

        return {"images": updated_images}, stats

    async def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save metadata to file asynchronously."""
        if not self.metadata_file:
            return

        def _save_sync():
            if self.metadata_file:
                # Ensure directory exists
                self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

                with open(self.metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

        await asyncio.to_thread(_save_sync)

    async def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        metadata = await self._load_metadata()
        images = metadata.get("images", [])

        categories = {}
        total_size = 0

        for img in images:
            category = img.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            total_size += img.get("size", 0)

        return {
            "total_images": len(images),
            "categories": categories,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "last_sync": metadata.get("last_sync"),
        }


async def sync_image_library(library_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for library synchronization.
    Non-blocking with proper error handling.
    """
    manager = LibraryManager(library_path)
    return await manager.sync_library()


async def get_image_library_stats(library_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get library statistics without full sync.
    """
    manager = LibraryManager(library_path)
    return await manager.get_library_stats()
