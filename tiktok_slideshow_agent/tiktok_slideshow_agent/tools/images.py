import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any

class ImageLibraryTool:
    def __init__(self):
        # Calculate Base Path: tools -> tiktok_slideshow_agent -> PROJECT_ROOT
        current_file = Path(__file__).resolve()
        self.base_path = current_file.parent.parent.parent
        self.output_dir = self.base_path / "image_library"
        self.metadata_file = self.output_dir / "images.json"
        self._images = None

    @property
    def images(self) -> List[Dict[str, Any]]:
        if self._images is None:
            self._images = self._load_images()
        return self._images

    def _load_images(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.metadata_file):
            return []
        with open(self.metadata_file, "r") as f:
            return json.load(f)

    def search_images(self, query_tags: List[str] = None, category: str = None) -> List[Dict[str, Any]]:
        """
        Search for images based on tags and category.
        Returns a list of image metadata objects with absolute paths.
        """
        results = []
        for img in self.images:
            if category and img.get("category") != category:
                continue
            
            if query_tags:
                img_tags = set(img.get("tags", []))
                # Simple match: if any query tag is in img_tags
                # Or we could do all. Let's do intersection > 0 for now, or scoring.
                # Let's just return all if no tags, or filter by intersection.
                if not set(query_tags).intersection(img_tags):
                    continue
            
            # Add absolute path to the object for easier use downstream
            img_copy = img.copy()
            img_copy["absolute_path"] = os.path.join(self.base_path, img["category"], img["filename"])
            results.append(img_copy)
            
        return results

    def get_image_by_id(self, image_id: str) -> Dict[str, Any]:
        for img in self.images:
            if img["id"] == image_id:
                img_copy = img.copy()
                img_copy["absolute_path"] = os.path.join(self.base_path, img["category"], img["filename"])
                return img_copy
        return None

    def get_all_images_as_text(self) -> str:
        """Returns a formatted string of all images in the library."""
        output = "Available Image Library:\n"
        for img in self.images:
            output += f"- ID: {img['id']}\n"
            output += f"  Filename: {img['filename']}\n"
            output += f"  Category: {img['category']}\n"
            output += f"  Tags: {', '.join(img.get('tags', []))}\n"
            output += f"  Description: {img.get('description', '')}\n"
            output += f"  Absolute Path: {os.path.join(self.base_path, img['category'], img['filename'])}\n\n"
        return output
