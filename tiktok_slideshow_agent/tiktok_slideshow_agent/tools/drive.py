import os
import shutil
import asyncio
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes required for the agent
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send'
]

class GoogleDriveTool:
    def __init__(self):
        # Calculate Base Path: tools -> tiktok_slideshow_agent -> PROJECT_ROOT
        current_file = Path(__file__).resolve()
        self.base_path = current_file.parent.parent.parent
        
        # Path to credentials.json (downloaded from Cloud Console)
        self.creds_file = self.base_path / "credentials.json"
        
        # Paths to save tokens
        self.token_file_drive = self.base_path / "token_drive.json" # Kept for legacy compatibility if needed, but we use one token for both scopes now
        self.token_file = self.base_path / "token.json" # Unified token
        
        self.creds = None
        self.drive_service = None
        self.gmail_service = None

    async def _authenticate(self):
        """Authenticates the user and creates service clients."""
        if self.creds and self.creds.valid:
            return

        def run_auth_flow():
            creds = None
            token_path = self.token_file
            
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.creds_file):
                        raise FileNotFoundError(f"Credentials file not found at {self.creds_file}. Please add it to enable Google Services.")
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.creds_file), SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            return creds

        self.creds = await asyncio.to_thread(run_auth_flow)
        
        # Build services in a thread because build() does synchronous IO (reading discovery docs)
        def build_services():
            return (
                build('drive', 'v3', credentials=self.creds),
                build('gmail', 'v1', credentials=self.creds)
            )

        if not self.drive_service or not self.gmail_service:
            self.drive_service, self.gmail_service = await asyncio.to_thread(build_services)

    async def _ensure_service(self):
        if not self.drive_service or not self.gmail_service:
            await self._authenticate()

    async def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Creates a folder in Google Drive.
        Returns the folder ID.
        """
        await self._ensure_service()
        
        def _create_sync():
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
                
            file = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            return file.get('id')
            
        return await asyncio.to_thread(_create_sync)

    async def upload_files(self, file_paths: List[str], folder_id: str) -> str:
        """
        Uploads files to the specified Drive folder.
        Returns a generic link to the folder.
        """
        await self._ensure_service()
        
        def _upload_sync(f_path):
            file_name = os.path.basename(f_path)
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            media = MediaFileUpload(f_path, resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f"Uploaded {file_name} with ID: {file.get('id')}")

        for file_path in file_paths:
            if os.path.exists(file_path):
                # We do this one by one in thread to avoid blocking
                await asyncio.to_thread(_upload_sync, file_path)
        
        return f"https://drive.google.com/drive/folders/{folder_id}"

    async def send_email(self, to_email: str, subject: str, body: str) -> str:
        """
        Sends an email using the Gmail API.
        """
        await self._ensure_service()
        
        def _send_sync():
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            msg = MIMEText(body)
            message.attach(msg)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body_payload = {'raw': raw_message}
            
            message = self.gmail_service.users().messages().send(
                userId='me', body=body_payload).execute()
            return message['id']

        msg_id = await asyncio.to_thread(_send_sync)
        return f"Email sent successfully. ID: {msg_id}"

