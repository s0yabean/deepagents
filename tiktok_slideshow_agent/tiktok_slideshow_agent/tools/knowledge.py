import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any

class KnowledgeBaseTool:
    def __init__(self, kb_path: str = "knowledge_base"):
        self.base_path = "/Users/mindreader/Desktop/deepagents-quickstarts/tiktok_slideshow_agent"
        self.slideshows_file = os.path.join(self.base_path, "slideshows.json")

    def _ensure_file_exists(self):
        if not os.path.exists(self.slideshows_file):
            with open(self.slideshows_file, "w") as f:
                json.dump([], f)

    def _load_history(self) -> List[Dict]:
        self._ensure_file_exists()
        with open(self.slideshows_file, "r") as f:
            return json.load(f)

    def save_slideshow(self, project_id: str, topic: str, slides: List[Dict], drive_link: str):
        """
        Saves a completed slideshow run to the history.
        """
        history = self._load_history()

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
        history = self._load_history()
        return history[-limit:]
