from fastapi.testclient import TestClient
from unittest.mock import patch
from Loker.api.server import app

client = TestClient(app)


def test_whatsapp_webhook_unauthorized_sender():
    payload = {
        "sender": "081299999999",  # Bukan nomor admin
        "message": "Halo bot",
        "name": "Orang Asing"
    }
    res = client.post("/api/whatsapp/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ignored"
    assert "not authorized" in data["reason"]


def test_whatsapp_webhook_admin_status_command():
    with patch("Loker.services.whatsapp_service.whatsapp_service.send_message") as mock_send:
        mock_send.return_value = {"success": True}

        payload = {
            "sender": "082230315125",
            "message": "status",
            "name": "Admin"
        }
        res = client.post("/api/whatsapp/webhook", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["reply_sent"] is True

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert call_args[0] == "082230315125"
        assert "STATUS OPERASIONAL" in call_args[1]


def test_whatsapp_webhook_admin_lowongan_command():
    with patch("Loker.services.whatsapp_service.whatsapp_service.send_message") as mock_send:
        mock_send.return_value = {"success": True}

        payload = {
            "sender": "6282230315125",  # Format 62
            "message": "lowongan",
            "name": "Admin"
        }
        res = client.post("/api/whatsapp/webhook", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert "DAFTAR LOWONGAN" in call_args[1]
