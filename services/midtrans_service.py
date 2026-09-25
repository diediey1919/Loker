import base64
import hashlib
from typing import Dict, Any, Optional
import requests
from ..config.settings import settings
from ..core.models import MidtransTransactionPayload


class MidtransService:
    def __init__(
        self,
        server_key: Optional[str] = None,
        client_key: Optional[str] = None,
        is_production: Optional[bool] = None
    ):
        self.server_key = server_key or settings.MIDTRANS_SERVER_KEY
        self.client_key = client_key or settings.MIDTRANS_CLIENT_KEY
        self.is_production = is_production if is_production is not None else settings.MIDTRANS_IS_PRODUCTION
        
        if self.is_production:
            self.snap_url = "https://app.midtrans.com/snap/v1/transactions"
        else:
            self.snap_url = "https://app.sandbox.midtrans.com/snap/v1/transactions"

    def is_configured(self) -> bool:
        return bool(self.server_key and not self.server_key.startswith("<PENDING"))

    def _get_auth_header(self) -> Dict[str, str]:
        encoded_key = base64.b64encode(f"{self.server_key}:".encode("utf-8")).decode("utf-8")
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_key}"
        }

    def create_lifetime_transaction(self, payload: MidtransTransactionPayload) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "Midtrans Server Key is still pending verification."
            }

        body = {
            "transaction_details": {
                "order_id": payload.order_id,
                "gross_amount": payload.gross_amount
            },
            "item_details": [
                {
                    "id": "PRO-LIFETIME",
                    "price": payload.gross_amount,
                    "quantity": 1,
                    "name": "Loker Pro Lifetime Access"
                }
            ],
            "customer_details": {
                "first_name": payload.customer_name,
                "email": payload.customer_email,
                "phone": payload.customer_phone or ""
            }
        }

        try:
            res = requests.post(self.snap_url, headers=self._get_auth_header(), json=body, timeout=15)
            res.raise_for_status()
            data = res.json()
            return {
                "success": True,
                "token": data.get("token"),
                "redirect_url": data.get("redirect_url")
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def verify_signature(self, order_id: str, status_code: str, gross_amount: str, signature_key: str) -> bool:
        if not self.is_configured():
            return False
        raw_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"
        expected_hash = hashlib.sha512(raw_string.encode("utf-8")).hexdigest()
        return expected_hash.lower() == signature_key.lower()


midtrans_service = MidtransService()
