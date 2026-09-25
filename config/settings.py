import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    # GitHub Configuration
    GITHUB_REPO_NAME: str = "https://github.com/diediey1919/Loker"
    GITHUB_AUTH_TYPE: str = "ssh"
    GITHUB_TOKEN: Optional[str] = None

    # Blogger API
    BLOGGER_BLOG_ID: Optional[str] = None
    BLOGGER_CLIENT_ID: Optional[str] = None
    BLOGGER_CLIENT_SECRET: Optional[str] = None

    # Instagram Official API
    IG_ACCESS_TOKEN: Optional[str] = None
    IG_USER_ID: Optional[str] = None
    IG_APP_ID: Optional[str] = None
    IG_APP_SECRET: Optional[str] = None

    # Midtrans Payment Gateway
    MIDTRANS_SERVER_KEY: Optional[str] = None
    MIDTRANS_CLIENT_KEY: Optional[str] = None
    MIDTRANS_IS_PRODUCTION: bool = False

    # Google OAuth Login
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: Optional[str] = None

    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # WhatsApp Gateway (Fonnte API)
    WA_GATEWAY_ENDPOINT: str = "https://api.fonnte.com/send"
    WA_API_TOKEN: Optional[str] = None
    ADMIN_WHATSAPP_PHONE: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_blogger_ready(self) -> bool:
        return bool(self.BLOGGER_BLOG_ID and self.BLOGGER_CLIENT_ID and self.BLOGGER_CLIENT_SECRET)

    def is_whatsapp_ready(self) -> bool:
        return bool(self.WA_API_TOKEN and not self.WA_API_TOKEN.startswith("<PENDING"))

    def is_smtp_ready(self) -> bool:
        return bool(self.SMTP_USER and self.SMTP_PASSWORD and not self.SMTP_PASSWORD.startswith("<PENDING"))

    def is_midtrans_ready(self) -> bool:
        return bool(self.MIDTRANS_SERVER_KEY and not self.MIDTRANS_SERVER_KEY.startswith("<PENDING"))

    def is_instagram_ready(self) -> bool:
        return bool(self.IG_ACCESS_TOKEN and not self.IG_ACCESS_TOKEN.startswith("<PENDING"))

    def is_google_oauth_ready(self) -> bool:
        return bool(
            self.GOOGLE_OAUTH_CLIENT_ID
            and self.GOOGLE_OAUTH_CLIENT_SECRET
            and self.GOOGLE_OAUTH_REDIRECT_URI
            and not self.GOOGLE_OAUTH_REDIRECT_URI.startswith("<PENDING")
        )


settings = AppSettings()
