import os
import hashlib
from fastapi.testclient import TestClient
from Loker.api.server import app
from Loker.config.settings import settings
from Loker.core.privacy import privacy_manager

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["blogger_ready"] is True
    assert data["whatsapp_ready"] is True


def test_get_jobs_endpoint():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "jobs" in data


def test_upload_cv_and_apply_flow(tmp_path):
    email = "tester_api@example.com"
    dummy_pdf = b"%PDF-1.4 dummy pdf content for testing"

    # 1. Upload CV
    upload_res = client.post(
        "/api/upload/cv",
        data={"email": email},
        files={"file": ("my_resume.pdf", dummy_pdf, "application/pdf")}
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    cv_path = upload_data["cv_temp_path"]
    assert os.path.exists(cv_path)

    # 2. Cek status user awal (0 applies, 3 remaining)
    status_res = client.get(f"/api/user/status?email={email}")
    assert status_res.status_code == 200
    assert status_res.json()["remaining_free_applies"] == 3

    # 3. Apply ke lowongan yang ada
    jobs = client.get("/api/jobs").json()["jobs"]
    if len(jobs) > 0:
        target_job_id = jobs[0]["id"]
        apply_payload = {
            "applicant_name": "Tester API",
            "applicant_email": email,
            "applicant_phone": "081999888777",
            "portfolio_url": "https://tester.dev",
            "target_job_id": target_job_id,
            "template_type": "formal",
            "cv_temp_path": cv_path,
            "private_mode": False,
            "send_whatsapp": False
        }
        apply_res = client.post("/api/jobs/apply", json=apply_payload)
        assert apply_res.status_code == 200
        assert apply_res.json()["success"] is True

        # Sisa kuota berkurang jadi 2
        status_after = client.get(f"/api/user/status?email={email}").json()
        assert status_after["applied_count"] == 1
        assert status_after["remaining_free_applies"] == 2

    # 4. Hapus data mandiri
    del_res = client.post("/api/user/delete-data", data={"email": email})
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_midtrans_webhook_signature_validation():
    order_id = "ORDER-TEST-WEBHOOK-01"
    status_code = "200"
    gross_amount = "49000.00"
    server_key = settings.MIDTRANS_SERVER_KEY or "dummy_key"

    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    valid_sig = hashlib.sha512(raw.encode("utf-8")).hexdigest()

    # Signature valid
    res_valid = client.post(
        "/api/payment/webhook",
        json={
            "order_id": order_id,
            "status_code": status_code,
            "gross_amount": gross_amount,
            "signature_key": valid_sig,
            "transaction_status": "settlement",
            "customer_email": "payer@example.com"
        }
    )
    # Jika server key pending, midtrans_service.verify_signature mengembalikan False
    if settings.is_midtrans_ready():
        assert res_valid.status_code == 200
    else:
        assert res_valid.status_code == 403

    # Signature palsu wajib ditolak HTTP 403
    res_fake = client.post(
        "/api/payment/webhook",
        json={
            "order_id": order_id,
            "status_code": status_code,
            "gross_amount": gross_amount,
            "signature_key": "fake_signature_hash_123",
            "transaction_status": "settlement",
            "customer_email": "payer@example.com"
        }
    )
    assert res_fake.status_code == 403
