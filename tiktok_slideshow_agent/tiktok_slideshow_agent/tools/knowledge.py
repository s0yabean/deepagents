import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any

class KnowledgeBaseTool:
    def __init__(self, kb_path: str = "knowledge_base"):
        self.base_path = "/Users/mindreader/Desktop/deepagents-quickstarts/tiktok_slideshow_agent"
        self.slideshows_file = os.path.join(self.base_path, "slideshows.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.slideshows_file):
            with open(self.slideshows_file, "w") as f:
                json.dump([], f)

    def save_slideshow(self, project_id: str, topic: str, slides: List[Dict], drive_link: str):
        """
        Saves a completed slideshow run to the history.
        """
        with open(self.slideshows_file, "r") as f:
            history = json.load(f)

        entry = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "topic": topic,
            "created_at": datetime.utcnow().isoformat(),
            "slide_count": len(slides),
            "slides": slides,
            "drive_folder_link": drive_link
        }

        history.append(entry)

        with open(self.slideshows_file, "w") as f:
            json.dump(history, f, indent=2)
            
    def get_recent_slideshows(self, limit: int = 5) -> List[Dict]:
        with open(self.slideshows_file, "r") as f:
            history = json.load(f)
        return history[-limit:]
