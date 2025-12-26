import os
import shutil
from typing import List

class GoogleDriveTool:
    def __init__(self):
        # In a real scenario, we would init the Drive API client here.
        # For now, we will mock the upload by moving files to a local "Drive" folder.
        # Standardizing to use the 'output' directory as the drive root.
        self.mock_drive_root = "/Users/mindreader/Desktop/deepagents-quickstarts/tiktok_slideshow_agent/output"

    def _ensure_dir(self, path: str):
        if not os.path.exists(path):
            os.makedirs(path)

    def create_folder(self, folder_name: str) -> str:
        """
        Creates a folder in Drive (Mock: creates local directory).
        Returns the folder ID (Mock: folder path).
        """
        self._ensure_dir(self.mock_drive_root)
        folder_path = os.path.join(self.mock_drive_root, folder_name)
        self._ensure_dir(folder_path)
        return folder_path

    def upload_files(self, file_paths: List[str], folder_id: str) -> str:
        """
        Uploads files to the specified folder.
        Returns a link to the folder.
        """
        for file_path in file_paths:
            if os.path.exists(file_path):
                dest_path = os.path.join(folder_id, os.path.basename(file_path))
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                shutil.move(file_path, folder_id)
        
        # Return a mock link
        folder_name = os.path.basename(folder_id)
        return f"https://drive.google.com/drive/folders/mock-id-{folder_name}"
