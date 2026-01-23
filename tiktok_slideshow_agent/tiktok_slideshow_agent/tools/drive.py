import os
import asyncio
import smtplib
import requests
import json
import time
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes required for Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]  # Full Drive access


class GoogleDriveTool:
    def __init__(self):
        current_file = Path(__file__).resolve()
        self.base_path = current_file.parent.parent.parent

        # GitHub configuration for token fetching
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.token_repo_url = os.getenv("GOOGLE_OAUTH_TOKEN_REPO_URL")

        # GitHub Actions configuration for token refresh
        self.github_repo_owner = os.getenv("GITHUB_REPO_OWNER", "s0yabean")
        self.github_repo_name = os.getenv("GITHUB_REPO_NAME", "lambda_jobs")
        self.github_workflow_file = os.getenv(
            "GITHUB_WORKFLOW_FILE", "refresh_google_token.yml"
        )
        self.github_default_branch = os.getenv("GITHUB_DEFAULT_BRANCH", "master")

        # Token refresh settings
        self.expiry_threshold_minutes = int(
            os.getenv("TOKEN_EXPIRY_THRESHOLD_MINUTES", "40")
        )
        self.refresh_poll_timeout = int(
            os.getenv("TOKEN_REFRESH_POLL_TIMEOUT", "60")
        )  # Increased to 60s

        # Local cache file (optional)
        self.oauth_token_file = self.base_path / "token.json"

        self.drive_service = None
        self._initialized = False
        self._current_token_data = None
        self._refresh_triggered_at = None  # Track when refresh was triggered
        self._old_token_for_refresh = None  # Store old token to detect change

    async def _fetch_token_from_github(self) -> Dict:
        """Fetches token.json from private GitHub repository."""
        if not self.github_token or not self.token_repo_url:
            raise ValueError(
                "GITHUB_TOKEN and GOOGLE_OAUTH_TOKEN_REPO_URL must be set in environment variables"
            )

        def _fetch_sync():
            headers = {"Authorization": f"token {self.github_token}"}
            response = requests.get(self.token_repo_url, headers=headers)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_fetch_sync)

    def _is_token_expiring_soon(self, token_data: Dict) -> bool:
        """Check if token expires within threshold minutes."""
        expiry_str = token_data.get("expiry")
        if not expiry_str:
            return True  # No expiry, assume needs refresh

        # Parse ISO format: "2026-01-17T05:45:21.559020+00:00"
        expiry = datetime.fromisoformat(expiry_str)
        now = datetime.now(timezone.utc)
        time_until_expiry = expiry - now

        threshold = timedelta(minutes=self.expiry_threshold_minutes)
        return time_until_expiry <= threshold

    async def _trigger_token_refresh_workflow(self):
        """Triggers GitHub Actions workflow to refresh the token."""
        url = (
            f"https://api.github.com/repos/{self.github_repo_owner}/"
            f"{self.github_repo_name}/actions/workflows/{self.github_workflow_file}/dispatches"
        )

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        payload = {"ref": self.github_default_branch}

        def _trigger_sync():
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 204:
                return True
            else:
                raise Exception(
                    f"Failed to trigger workflow: {response.status_code} - {response.text}"
                )

        return await asyncio.to_thread(_trigger_sync)

    async def _wait_for_token_refresh(
        self, old_token_value: str, timeout: int = 60
    ) -> Dict:
        """Poll GitHub repo until token value changes or timeout."""
        print(f"⏳ Waiting for token refresh (timeout: {timeout}s)...")
        start_time = time.time()
        poll_count = 0

        while time.time() - start_time < timeout:
            await asyncio.sleep(2)  # Poll every 2 seconds
            poll_count += 1
            elapsed = int(time.time() - start_time)

            try:
                new_token_data = await self._fetch_token_from_github()
                new_token_value = new_token_data.get("token")

                if new_token_value and new_token_value != old_token_value:
                    print(f"✅ Token refreshed successfully after {elapsed}s!")
                    return new_token_data
                else:
                    # Show progress every 10 seconds
                    if poll_count % 5 == 0:
                        print(f"   Still waiting... ({elapsed}s elapsed)")
            except Exception as e:
                print(f"⚠️  Error polling token: {e}")

        raise TimeoutError(
            f"Token refresh did not complete within {timeout} seconds. The workflow may still be running - check GitHub Actions."
        )

    def _get_minutes_until_expiry(self, token_data: Dict) -> int:
        """Get minutes until token expires."""
        expiry_str = token_data.get("expiry")
        if not expiry_str:
            return 0

        expiry = datetime.fromisoformat(expiry_str)
        now = datetime.now(timezone.utc)
        time_until_expiry = expiry - now
        return int(time_until_expiry.total_seconds() / 60)

    async def validate_and_refresh_token(self):
        """
        Startup check: Fetch token, check expiry, trigger refresh if needed.
        Smart waiting: Only blocks if token is critically close to expiry (<5 mins).
        Otherwise triggers refresh and proceeds immediately.
        """
        print("🔍 Validating Google OAuth token...")

        # Fetch current token
        token_data = await self._fetch_token_from_github()
        self._current_token_data = token_data

        minutes_left = self._get_minutes_until_expiry(token_data)
        print(f"   Token expires in {minutes_left} minutes")

        # Check if token is expiring soon
        if self._is_token_expiring_soon(token_data):
            old_token = token_data.get("token")
            print(
                f"⚠️  Token expires within {self.expiry_threshold_minutes} minutes. Triggering refresh..."
            )

            # Trigger GitHub Actions workflow
            await self._trigger_token_refresh_workflow()

            # Only wait if token is critically close to expiry
            if minutes_left > 5:
                print(
                    f"✅ Refresh triggered. Token still valid for {minutes_left} minutes - proceeding immediately."
                )
                print(f"   Refresh will complete in background.")
            else:
                # Token critically close to expiry - must wait
                print(
                    f"⚠️  Token critically close to expiry ({minutes_left} mins). Waiting for refresh..."
                )
                try:
                    token_data = await self._wait_for_token_refresh(
                        old_token, timeout=self.refresh_poll_timeout
                    )
                    self._current_token_data = token_data
                    print(f"✅ Token refreshed successfully")
                except TimeoutError as e:
                    raise Exception(
                        f"Token refresh timed out and token expires in {minutes_left} minutes. Cannot proceed safely."
                    )
        else:
            print("✅ Token is valid and not expiring soon")

        return token_data

    async def validate_token_async(self):
        """
        Non-blocking startup check: Fetch token, trigger refresh if needed, but DON'T wait.
        This allows the agent to start immediately while refresh happens in background.
        """
        print("🔍 Checking Google OAuth token...")

        # Fetch current token
        token_data = await self._fetch_token_from_github()
        self._current_token_data = token_data

        minutes_left = self._get_minutes_until_expiry(token_data)
        print(f"   Token expires in {minutes_left} minutes")

        # Check if token is expiring soon
        if self._is_token_expiring_soon(token_data):
            self._old_token_for_refresh = token_data.get("token")
            print(
                f"⚠️  Token expires within {self.expiry_threshold_minutes} minutes. Triggering refresh (non-blocking)..."
            )

            # Trigger GitHub Actions workflow but DON'T wait
            await self._trigger_token_refresh_workflow()
            self._refresh_triggered_at = time.time()

            print(
                "✅ Refresh triggered in background. Agent will continue immediately."
            )
            print(
                f"   (Refresh will be verified when Drive is needed, typically in ~10 minutes)"
            )
        else:
            print("✅ Token valid, no refresh needed")

        return token_data

    async def _wait_for_refresh_completion(self):
        """
        Smart refresh verification: Only wait if token is critically close to expiry.
        If token still has time left, proceed immediately and let refresh complete in background.
        """
        if not self._refresh_triggered_at or not self._old_token_for_refresh:
            return  # No refresh in progress

        elapsed = int(time.time() - self._refresh_triggered_at)

        # Check current token validity FIRST before waiting
        current_token_data = await self._fetch_token_from_github()
        minutes_left = self._get_minutes_until_expiry(current_token_data)

        # If token still has >5 mins, proceed immediately without waiting
        if minutes_left > 5:
            print(
                f"🔄 Token refresh in progress ({elapsed}s ago), but current token still valid for {minutes_left} minutes"
            )
            print(f"✅ Proceeding immediately. Refresh will complete in background.")
            self._current_token_data = current_token_data
            # Keep refresh tracking in case we need it later
            return

        # Token is critically close to expiry - must wait for refresh
        print(
            f"⚠️  Token only valid for {minutes_left} minutes. Waiting for refresh to complete..."
        )
        remaining_timeout = max(5, self.refresh_poll_timeout - elapsed)

        try:
            token_data = await self._wait_for_token_refresh(
                self._old_token_for_refresh, timeout=remaining_timeout
            )
            self._current_token_data = token_data
            print(f"✅ Token refreshed successfully")

            # Clear refresh tracking
            self._refresh_triggered_at = None
            self._old_token_for_refresh = None

        except TimeoutError as e:
            # Refresh timed out and token is critically close to expiry
            raise Exception(
                f"Token refresh incomplete and token expires in {minutes_left} minutes. Cannot proceed safely."
            )

    async def _authenticate(self):
        """Authenticates using OAuth 2.0 from GitHub-hosted token."""
        if self._initialized and self.drive_service:
            return

        def build_service():
            # Use already-fetched token data from validate_and_refresh_token()
            if not self._current_token_data:
                raise RuntimeError(
                    "Token not loaded. Call validate_and_refresh_token() before using GoogleDriveTool"
                )

            # Create credentials from token data
            creds = Credentials(
                token=self._current_token_data.get("token"),
                refresh_token=self._current_token_data.get("refresh_token"),
                token_uri=self._current_token_data.get("token_uri"),
                client_id=self._current_token_data.get("client_id"),
                client_secret=self._current_token_data.get("client_secret"),
                scopes=self._current_token_data.get("scopes"),
            )

            # If token expired, refresh it locally
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    print("🔄 Token expired, refreshing locally...")
                    creds.refresh(Request())
                else:
                    raise Exception("Token is invalid and cannot be refreshed")

            return build("drive", "v3", credentials=creds)

        self.drive_service = await asyncio.to_thread(build_service)
        self._initialized = True

    async def _ensure_service(self):
        if not self.drive_service:
            # Auto-fetch token if not already loaded
            if not self._current_token_data:
                print("🔐 Initializing Google Drive authentication...")
                await self.validate_token_async()

            # If refresh was triggered earlier, wait for it to complete now
            if self._refresh_triggered_at:
                await self._wait_for_refresh_completion()

            await self._authenticate()

    async def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Creates a folder in Google Drive.
        Returns the folder ID.
        """
        await self._ensure_service()

        # Use parent_id from param, or fall back to env variable
        if not parent_id:
            parent_id = os.getenv("GOOGLE_DRIVE_PARENT_ID")

        def _create_sync():
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                file_metadata["parents"] = [parent_id]

            file = (
                self.drive_service.files()
                .create(body=file_metadata, fields="id")
                .execute()
            )
            return file.get("id")

        return await asyncio.to_thread(_create_sync)

    async def upload_files(self, file_paths: List[str], folder_id: str) -> str:
        """
        Uploads files to the specified Drive folder.
        Returns a generic link to the folder.
        """
        await self._ensure_service()

        uploaded = []
        skipped = []
        upload_errors = []

        def _upload_sync(f_path):
            file_name = os.path.basename(f_path)
            try:
                file_metadata = {"name": file_name, "parents": [folder_id]}
                media = MediaFileUpload(f_path, resumable=True)
                file = (
                    self.drive_service.files()
                    .create(body=file_metadata, media_body=media, fields="id")
                    .execute()
                )
                print(f"✅ Uploaded: {file_name} (ID: {file.get('id')})")
                return file_name
            except Exception as e:
                print(f"❌ Failed to upload {file_name}: {str(e)}")
                upload_errors.append(f"{file_name}: {str(e)}")
                return None

        for file_path in file_paths:
            if os.path.exists(file_path):
                name = await asyncio.to_thread(_upload_sync, file_path)
                if name:
                    uploaded.append(name)
            else:
                print(f"⚠️  File not found, SKIPPED: {file_path}")
                skipped.append(file_path)

        if skipped:
            print(
                f"❌ UPLOAD WARNING: {len(skipped)} files were NOT uploaded (don't exist):"
            )
            for s in skipped:
                print(f"   - {s}")

        if upload_errors:
            print(f"❌ UPLOAD ERRORS: {len(upload_errors)} files failed:")
            for e in upload_errors:
                print(f"   - {e}")

        print(
            f"📤 Upload summary: {len(uploaded)} uploaded, {len(skipped)} skipped, {len(upload_errors)} errors"
        )

        return f"https://drive.google.com/drive/folders/{folder_id}"

    async def list_folder_files(self, folder_id: str) -> List[str]:
        """
        Lists all files in a specific Drive folder.
        Returns a list of file names.
        """
        await self._ensure_service()

        def _list_sync():
            results = (
                self.drive_service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="files(name)",
                )
                .execute()
            )
            files = results.get("files", [])
            return [file["name"] for file in files]

        return await asyncio.to_thread(_list_sync)

    async def send_email(self, to_email: str, subject: str, body: str) -> str:
        """
        Sends an email using SMTP with App Password.
        """
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM", smtp_username)

        if not smtp_username or not smtp_password:
            return "Email not sent: SMTP credentials not configured"

        def _send_sync():
            message = MIMEMultipart()
            message["From"] = smtp_from
            message["To"] = to_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

            return f"Email sent successfully to {to_email}"

        result = await asyncio.to_thread(_send_sync)
        return result
