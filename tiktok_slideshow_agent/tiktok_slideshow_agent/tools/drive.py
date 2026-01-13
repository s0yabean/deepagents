import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes required for Drive
SCOPES = ['https://www.googleapis.com/auth/drive']  # Full Drive access


class GoogleDriveTool:
    def __init__(self):
        current_file = Path(__file__).resolve()
        self.base_path = current_file.parent.parent.parent

        # Path to OAuth credentials (personal account for everything)
        self.oauth_credentials_file = self.base_path / "credentials.json"
        self.oauth_token_file = self.base_path / "token.json"

        self.drive_service = None
        self._initialized = False

    async def _authenticate(self):
        """Authenticates using OAuth 2.0 (personal account)."""
        if self._initialized and self.drive_service:
            return

        def build_service():
            creds = None
            # Token file stores the user's access and refresh tokens
            if os.path.exists(self.oauth_token_file):
                creds = Credentials.from_authorized_user_file(str(self.oauth_token_file), SCOPES)

            # If no valid credentials, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.oauth_credentials_file):
                        raise FileNotFoundError(
                            f"OAuth credentials file not found at {self.oauth_credentials_file}. "
                            "Please download it from Google Cloud Console."
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.oauth_credentials_file), SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.oauth_token_file, 'w') as token:
                    token.write(creds.to_json())

            return build('drive', 'v3', credentials=creds)

        self.drive_service = await asyncio.to_thread(build_service)
        self._initialized = True

    async def _ensure_service(self):
        if not self.drive_service:
            await self._authenticate()

    async def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Creates a folder in Google Drive.
        Returns the folder ID.
        """
        await self._ensure_service()

        # Use parent_id from param, or fall back to env variable
        if not parent_id:
            parent_id = os.getenv('GOOGLE_DRIVE_PARENT_ID')

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
                await asyncio.to_thread(_upload_sync, file_path)
        
        return f"https://drive.google.com/drive/folders/{folder_id}"

    async def send_email(self, to_email: str, subject: str, body: str) -> str:
        """
        Sends an email using SMTP with App Password.
        """
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        smtp_from = os.getenv('SMTP_FROM', smtp_username)
        
        if not smtp_username or not smtp_password:
            return "Email not sent: SMTP credentials not configured"
        
        def _send_sync():
            message = MIMEMultipart()
            message['From'] = smtp_from
            message['To'] = to_email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(message)
            
            return f"Email sent successfully to {to_email}"

        result = await asyncio.to_thread(_send_sync)
        return result
