import requests
from typing import Dict, Any, Optional
from ..config.settings import settings


class WhatsAppService:
    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None):
        self.endpoint = endpoint or settings.WA_GATEWAY_ENDPOINT
        self.token = token or settings.WA_API_TOKEN

    def is_configured(self) -> bool:
        return bool(self.token and not self.token.startswith("<PENDING"))

    def send_message(self, target_phone: str, message: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "WhatsApp Gateway token is pending or unconfigured."
            }

        headers = {
            "Authorization": self.token
        }
        payload = {
            "target": target_phone,
            "message": message,
            "countryCode": "62"
        }

        try:
            response = requests.post(self.endpoint, headers=headers, data=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "response": data
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }


whatsapp_service = WhatsAppService()
