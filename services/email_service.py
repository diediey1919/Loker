import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional
from ..config.settings import settings


class EmailService:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD

    def is_configured(self) -> bool:
        return bool(self.user and self.password and not self.password.startswith("<PENDING"))

    def send_application_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
        attachment_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "SMTP credentials are pending or unconfigured."
            }

        msg = MIMEMultipart()
        msg["From"] = self.user
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))

        if attachment_path and os.path.isfile(attachment_path):
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=attachment_filename or os.path.basename(attachment_path))
                    part["Content-Disposition"] = f'attachment; filename="{attachment_filename or os.path.basename(attachment_path)}"'
                    msg.attach(part)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to attach CV file: {e}"
                }

        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


email_service = EmailService()
