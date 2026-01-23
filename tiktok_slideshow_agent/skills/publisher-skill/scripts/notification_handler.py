"""
Notification Handler - Non-blocking email/SMS notifications for publishing workflow.
Handles SMTP delivery with retry logic and multi-recipient support.
"""

import asyncio
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any


class NotificationHandler:
    """Handles email notifications with non-blocking SMTP operations."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.max_retries = 3
        self.retry_delay = 2.0

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        smtp_config: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email to multiple recipients with retry logic.
        Returns delivery status for each recipient.
        """
        if not smtp_config:
            smtp_config = self._get_smtp_config()

        if not smtp_config.get("server") or not smtp_config.get("username"):
            return {
                "status": "error",
                "message": "SMTP configuration incomplete",
                "results": {},
            }

        results = {}

        # Send to each recipient
        for email in to_emails:
            result = await self._send_single_email(email, subject, body, smtp_config)
            results[email] = result

        successful_sends = sum(1 for r in results.values() if r["status"] == "success")

        return {
            "status": "completed",
            "total_recipients": len(to_emails),
            "successful_sends": successful_sends,
            "results": results,
        }

    async def _send_single_email(
        self, to_email: str, subject: str, body: str, smtp_config: Dict[str, str]
    ) -> Dict[str, Any]:
        """Send email to a single recipient with retries."""
        for attempt in range(self.max_retries):
            try:
                result = await self._attempt_email_send(
                    to_email, subject, body, smtp_config
                )

                if result["status"] == "success":
                    return result

                # If failed and not the last attempt, wait before retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))

            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {"status": "error", "error": str(e), "attempts": attempt + 1}

                await asyncio.sleep(self.retry_delay)

        return {
            "status": "error",
            "error": "Max retries exceeded",
            "attempts": self.max_retries,
        }

    async def _attempt_email_send(
        self, to_email: str, subject: str, body: str, smtp_config: Dict[str, str]
    ) -> Dict[str, Any]:
        """Attempt to send a single email."""

        def _send_sync():
            # Create message
            message = MIMEMultipart()
            message["From"] = smtp_config.get("from", smtp_config["username"])
            message["To"] = to_email
            message["Subject"] = subject

            # Add body
            message.attach(MIMEText(body, "plain"))

            # Send via SMTP
            server = smtplib.SMTP(
                smtp_config["server"], int(smtp_config.get("port", "587"))
            )

            try:
                server.starttls()
                server.login(smtp_config["username"], smtp_config["password"])
                server.send_message(message)
                return {"status": "success", "message": f"Email sent to {to_email}"}
            finally:
                server.quit()

        try:
            # Run SMTP operation in thread pool to avoid blocking
            result = await asyncio.wait_for(
                asyncio.to_thread(_send_sync), timeout=self.timeout_seconds
            )
            return result

        except asyncio.TimeoutError:
            raise Exception("SMTP operation timed out")
        except Exception as e:
            raise Exception(f"SMTP error: {str(e)}")

    def _get_smtp_config(self) -> Dict[str, str]:
        """Get SMTP configuration from environment variables."""
        return {
            "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "port": os.getenv("SMTP_PORT", "587"),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "from": os.getenv("SMTP_FROM", ""),
        }


async def send_notification_non_blocking(
    subject: str,
    content: str,
    recipients: Optional[List[str]] = None,
    smtp_config: Optional[Dict[str, str]] = None,
) -> str:
    """
    Main entry point for sending notifications.
    Automatically includes admin email if configured.
    """
    handler = NotificationHandler()

    # Always include admin email
    admin_email = os.getenv("EMAIL_TO")
    all_recipients = []

    if admin_email:
        all_recipients.append(admin_email)

    # Add additional recipients if provided
    if recipients:
        for email in recipients:
            if email and email != admin_email:
                all_recipients.append(email)

    if not all_recipients:
        return "❌ ERROR: No recipients configured. Set EMAIL_TO environment variable."

    # Send notifications
    result = await handler.send_email(all_recipients, subject, content, smtp_config)

    if result["status"] == "completed":
        success_count = result["successful_sends"]
        total_count = result["total_recipients"]
        return f"✅ Email sent to {success_count}/{total_count} recipients"
    else:
        return f"❌ Email sending failed: {result.get('message', 'Unknown error')}"


async def get_admin_emails() -> List[str]:
    """Get configured admin email addresses."""
    admin_email = os.getenv("EMAIL_TO")
    return [admin_email] if admin_email else []
