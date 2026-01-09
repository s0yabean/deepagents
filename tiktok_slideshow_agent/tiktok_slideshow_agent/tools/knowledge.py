import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class KnowledgeBaseTool:
    def __init__(self):
        # Calculate Base Path: tools -> tiktok_slideshow_agent -> PROJECT_ROOT
        current_file = Path(__file__).resolve()
        self.base_path = current_file.parent.parent.parent
        self.kb_file = self.base_path / "knowledge_base.json"

    def _ensure_file_exists(self):
        if not self.kb_file.exists():
            with open(self.kb_file, "w") as f:
                json.dump([], f)

    def _load_history(self) -> List[Dict]:
        self._ensure_file_exists()
        with open(self.kb_file, "r") as f:
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

        with open(self.kb_file, "w") as f:
            json.dump(history, f, indent=2)
            
    def get_recent_slideshows(self, limit: int = 5) -> List[Dict]:
        history = self._load_history()
        return history[-limit:]
