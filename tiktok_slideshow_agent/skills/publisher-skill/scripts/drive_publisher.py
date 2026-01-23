"""
Drive Publisher - Non-blocking Google Drive integration with OAuth management.
Handles file uploads, folder creation, and authentication for publishing workflow.
"""

import asyncio
import os
from typing import List, Optional, Dict, Any
import httpx


class DrivePublisher:
    """Handles Google Drive operations with non-blocking HTTP requests."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.api_base = "https://www.googleapis.com/drive/v3"
        self.upload_base = "https://www.googleapis.com/upload/drive/v3"

    async def authenticate(self, token: str) -> bool:
        """
        Validate OAuth token with a simple API call.
        Returns True if token is valid.
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_base}/about", params={"fields": "user"}, headers=headers
                )
                return response.status_code == 200
        except Exception:
            return False

    async def create_folder(
        self, name: str, parent_id: Optional[str] = None, token: str = ""
    ) -> Optional[str]:
        """
        Create a folder in Google Drive.
        Returns the folder ID if successful.
        """
        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}

        if parent_id:
            metadata["parents"] = parent_id

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.api_base}/files", json=metadata, headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("id")
                else:
                    print(f"Drive folder creation failed: {response.status_code}")
                    return None

        except Exception as e:
            print(f"Drive folder creation error: {str(e)}")
            return None

    async def upload_file(
        self, file_path: str, folder_id: str, token: str = ""
    ) -> Optional[str]:
        """
        Upload a single file to Google Drive.
        Returns the file ID if successful.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # Prepare metadata
        metadata = {"name": file_name, "parents": [folder_id]}

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # Start resumable upload
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                # Request upload URL
                response = await client.post(
                    f"{self.upload_base}/files?uploadType=resumable",
                    json=metadata,
                    headers=headers,
                )

                if response.status_code != 200:
                    raise Exception(f"Upload initiation failed: {response.status_code}")

                upload_url = response.headers.get("Location")
                if not upload_url:
                    raise Exception("No upload URL received")

                # Upload file content
                with open(file_path, "rb") as f:
                    file_data = f.read()

                upload_headers = {
                    "Content-Length": str(len(file_data)),
                    "Content-Type": "application/octet-stream",
                }

                upload_response = await client.put(
                    upload_url,
                    content=file_data,
                    headers=upload_headers,
                    timeout=self.timeout_seconds * 2,  # Longer timeout for uploads
                )

                if upload_response.status_code in [200, 201]:
                    upload_data = upload_response.json()
                    return upload_data.get("id")
                else:
                    raise Exception(
                        f"File upload failed: {upload_response.status_code}"
                    )

        except Exception as e:
            raise Exception(f"Drive upload error: {str(e)}")

    async def upload_files_batch(
        self,
        file_paths: List[str],
        folder_id: str,
        token: str = "",
        max_concurrent: int = 3,
    ) -> Dict[str, Any]:
        """
        Upload multiple files concurrently.
        Returns results with success/failure status for each file.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def upload_with_semaphore(file_path: str):
            async with semaphore:
                try:
                    file_id = await self.upload_file(file_path, folder_id, token)
                    return file_path, {"status": "success", "file_id": file_id}
                except Exception as e:
                    return file_path, {"status": "error", "error": str(e)}

        tasks = [upload_with_semaphore(path) for path in file_paths]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in batch_results:
            if isinstance(result, Exception):
                # Handle unexpected errors
                results["unknown"] = {"status": "error", "error": str(result)}
            elif isinstance(result, tuple) and len(result) == 2:
                file_path, status = result
                results[file_path] = status
            else:
                # Handle unexpected result format
                results["unknown"] = {
                    "status": "error",
                    "error": f"Unexpected result: {result}",
                }

        # Generate folder link
        folder_link = f"https://drive.google.com/drive/folders/{folder_id}"

        return {
            "results": results,
            "folder_link": folder_link,
            "total_files": len(file_paths),
            "successful_uploads": sum(
                1 for r in results.values() if r.get("status") == "success"
            ),
        }


async def upload_batch_non_blocking(
    file_paths: List[str], folder_id: str, token: str = "", max_concurrent: int = 3
) -> str:
    """
    Main entry point for batch file uploads.
    Returns a link to the folder containing the uploads.
    """
    publisher = DrivePublisher()
    result = await publisher.upload_files_batch(
        file_paths, folder_id, token, max_concurrent
    )
    return result["folder_link"]


async def create_drive_folder_non_blocking(
    name: str, parent_id: Optional[str] = None, token: str = ""
) -> Optional[str]:
    """
    Create a Google Drive folder.
    Returns the folder ID if successful.
    """
    publisher = DrivePublisher()
    return await publisher.create_folder(name, parent_id, token)
