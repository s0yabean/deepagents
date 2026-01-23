"""
Project Setup - Non-blocking project folder creation and management for publishing workflow.
Handles local and cloud directory setup with conflict resolution.
"""

import asyncio
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class ProjectSetupManager:
    """Manages project folder creation and setup."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else None

    async def setup_project_folders(
        self, topic: str, drive_parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create project folders locally and on Google Drive.
        Returns folder paths and IDs.
        """
        # Generate folder names
        folder_info = await self._generate_folder_names(topic)

        # Create local directories
        local_paths = await self._create_local_directories(
            folder_info["root_name"], self.base_path or Path("output")
        )

        # Create Drive folder (placeholder - would integrate with Drive API)
        drive_info = await self._create_drive_folder(
            folder_info["root_name"], drive_parent_id
        )

        return {**local_paths, **drive_info, "folder_name": folder_info["root_name"]}

    async def _generate_folder_names(self, topic: str) -> Dict[str, str]:
        """Generate timestamped folder names from topic."""
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%d%m%Y_%H%M")

        # Clean and shorten topic
        clean_topic = re.sub(r"[^a-zA-Z0-9\s]", "", topic)
        words = clean_topic.split()
        short_topic = "_".join(words[:3])
        reel_name = short_topic.lower().strip()[:30]

        root_name = f"{timestamp}_UTC_sayura_{reel_name}"

        return {"timestamp": timestamp, "reel_name": reel_name, "root_name": root_name}

    async def _create_local_directories(
        self, root_name: str, base_path: Path
    ) -> Dict[str, str]:
        """Create local directory structure."""

        def _create_sync():
            # Create root directory
            root_dir = base_path / root_name
            root_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            slideshows_dir = root_dir / "slideshows"
            metadata_dir = root_dir / "metadata"

            slideshows_dir.mkdir(exist_ok=True)
            metadata_dir.mkdir(exist_ok=True)

            return {
                "local_project_root": str(root_dir),
                "local_slideshows_dir": str(slideshows_dir),
                "local_metadata_dir": str(metadata_dir),
            }

        return await asyncio.to_thread(_create_sync)

    async def _create_drive_folder(
        self, folder_name: str, parent_id: Optional[str]
    ) -> Dict[str, str]:
        """
        Create Google Drive folder.
        This is a placeholder - actual implementation would use Drive API.
        """
        # Placeholder implementation
        # In real implementation, this would:
        # 1. Check if folder exists
        # 2. Create if needed
        # 3. Return folder ID

        await asyncio.sleep(0.01)  # Simulate async operation

        return {
            "project_root_id": f"drive_folder_{folder_name}",
            "drive_link": f"https://drive.google.com/drive/folders/placeholder_{folder_name}",
        }


async def setup_project_non_blocking(
    topic: str, base_path: Optional[str] = None, drive_parent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for non-blocking project setup.
    Creates both local and cloud project structure.
    """
    manager = ProjectSetupManager(base_path)
    return await manager.setup_project_folders(topic, drive_parent_id)


async def validate_project_structure(project_root: str) -> Dict[str, Any]:
    """
    Validate that project structure is correct and complete.
    """

    def _validate_sync():
        root_path = Path(project_root)

        required_dirs = ["slideshows", "metadata"]
        missing_dirs = []

        for dir_name in required_dirs:
            if not (root_path / dir_name).exists():
                missing_dirs.append(dir_name)

        return {
            "valid": len(missing_dirs) == 0,
            "missing_directories": missing_dirs,
            "project_root": str(root_path),
        }

    return await asyncio.to_thread(_validate_sync)
