import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from pydantic import BaseModel

from ..config.settings import settings
from ..core.models import (
    JobPost,
    JobCategory,
    TemplateType,
    ApplicationRequest,
    ApplicationResult,
    MidtransTransactionPayload,
)
from ..core.privacy import privacy_manager
from ..services.git_storage import git_storage_service
from ..services.template_generator import TemplateGeneratorService
from ..services.whatsapp_service import whatsapp_service
from ..services.email_service import email_service
from ..services.midtrans_service import midtrans_service

app = FastAPI(
    title="Loker API Service",
    description="Platform otomatisasi kurasi lowongan WFH dan pengiriman aplikasi cerdas",
    version="1.0.0"
)


class ApplyPayload(BaseModel):
    applicant_name: str
    applicant_email: str
    applicant_phone: Optional[str] = None
    portfolio_url: Optional[str] = None
    target_job_id: str
    template_type: TemplateType = TemplateType.FORMAL
    cv_temp_path: str
    private_mode: bool = False
    send_whatsapp: bool = False


class PaymentWebhookPayload(BaseModel):
    order_id: str
    status_code: str
    gross_amount: str
    signature_key: str
    transaction_status: str
    customer_email: Optional[str] = None


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Loker Automated Job Platform",
        "github": settings.GITHUB_REPO_NAME,
        "blogger_ready": settings.is_blogger_ready(),
        "whatsapp_ready": settings.is_whatsapp_ready(),
        "smtp_ready": settings.is_smtp_ready(),
        "midtrans_ready": settings.is_midtrans_ready(),
    }


@app.get("/api/jobs")
def get_jobs(category: Optional[JobCategory] = None):
    files = git_storage_service.list_jobs()
    results = []
    for f in files:
        job = git_storage_service.load_job(f)
        if job and job.is_active:
            if category is None or job.category == category:
                results.append(job)
    return {"total": len(results), "jobs": results}


@app.get("/api/jobs/{job_id}")
def get_job_by_id(job_id: str):
    files = git_storage_service.list_jobs()
    for f in files:
        job = git_storage_service.load_job(f)
        if job and job.id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan")


@app.post("/api/upload/cv")
async def upload_cv(
    email: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith((".pdf", ".doc", ".docx")):
        raise HTTPException(status_code=400, detail="Format file harus PDF atau Word (.doc/.docx)")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 10 MB")

    saved_path = privacy_manager.save_temp_cv(email, file.filename, content)
    return {
        "success": True,
        "filename": file.filename,
        "cv_temp_path": saved_path,
        "retention_policy": "Maksimal 30 hari atau langsung terhapus jika Private Mode aktif"
    }


@app.get("/api/user/status")
def get_user_status(email: str):
    state = privacy_manager.get_user_state(email)
    remaining = "Unlimited" if state["tier"] == "pro_lifetime" else max(0, 3 - state["apply_count"])
    return {
        "email": email,
        "membership_tier": state["tier"],
        "applied_count": state["apply_count"],
        "remaining_free_applies": remaining,
        "favorite_categories": state["favorite_categories"]
    }


@app.post("/api/jobs/apply")
def apply_to_job(payload: ApplyPayload):
    # 1. Pengecekan kuota akses pelamar
    if not privacy_manager.can_user_apply(payload.applicant_email):
        raise HTTPException(
            status_code=403,
            detail="Kuota Free Plan (3x apply) telah habis. Silakan upgrade ke Pro Lifetime seharga Rp 49.000."
        )

    # 2. Cari data lowongan sasaran
    target_job = None
    for f in git_storage_service.list_jobs():
        j = git_storage_service.load_job(f)
        if j and j.id == payload.target_job_id:
            target_job = j
            break

    if not target_job:
        raise HTTPException(status_code=404, detail="Lowongan target tidak ditemukan")

    # 3. Validasi berkas CV
    if not os.path.exists(payload.cv_temp_path):
        raise HTTPException(status_code=400, detail="Berkas CV tidak ditemukan di cache server")

    # 4. Generate 5 template dan ambil template pilihan
    app_request = ApplicationRequest(
        applicant_name=payload.applicant_name,
        applicant_email=payload.applicant_email,
        applicant_phone=payload.applicant_phone,
        portfolio_url=payload.portfolio_url,
        target_job_id=target_job.id,
        template_type=payload.template_type,
        cv_filename=os.path.basename(payload.cv_temp_path),
        cv_temp_path=payload.cv_temp_path
    )
    all_msgs = TemplateGeneratorService.generate_all_templates(target_job, app_request)
    chosen_msg = all_msgs[payload.template_type]

    # 5. Dispatch email ke penyedia lowongan
    dispatch_success = True
    dispatch_error = None
    if target_job.contact_email and settings.is_smtp_ready():
        res = email_service.send_application_email(
            to_email=target_job.contact_email,
            subject=chosen_msg.subject,
            body=chosen_msg.body,
            attachment_path=payload.cv_temp_path,
            attachment_filename=os.path.basename(payload.cv_temp_path)
        )
        if not res.get("success"):
            dispatch_success = False
            dispatch_error = res.get("error")

    # 6. Notifikasi WhatsApp ke pelamar (opsional)
    if payload.send_whatsapp and payload.applicant_phone and settings.is_whatsapp_ready():
        wa_text = (
            f"Halo {payload.applicant_name}, lamaran Anda untuk *{target_job.title}* di *{target_job.company}* "
            f"telah berhasil dikirimkan via Loker. Kami lampirkan salinan pesan yang digunakan."
        )
        whatsapp_service.send_message(payload.applicant_phone, wa_text)

    # 7. Update kuota & catat ketertarikan kategori
    privacy_manager.record_apply(payload.applicant_email, target_job.category.value)

    # 8. Terapkan Private Mode jika aktif
    is_purged = privacy_manager.handle_post_apply_privacy(payload.cv_temp_path, payload.private_mode)

    return {
        "success": dispatch_success,
        "job_id": target_job.id,
        "job_title": target_job.title,
        "company": target_job.company,
        "template_used": payload.template_type.value,
        "message_preview": {
            "subject": chosen_msg.subject,
            "body": chosen_msg.body
        },
        "cv_purged_by_private_mode": is_purged,
        "error": dispatch_error
    }


@app.post("/api/payment/create")
def create_payment(payload: MidtransTransactionPayload):
    res = midtrans_service.create_lifetime_transaction(payload)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error"))
    return res


@app.post("/api/payment/webhook")
def handle_payment_webhook(payload: PaymentWebhookPayload):
    is_valid = midtrans_service.verify_signature(
        order_id=payload.order_id,
        status_code=payload.status_code,
        gross_amount=payload.gross_amount,
        signature_key=payload.signature_key
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail="Signature not authentic")

    if payload.transaction_status in ("capture", "settlement"):
        if payload.customer_email:
            privacy_manager.upgrade_to_pro_lifetime(payload.customer_email)

    return {"status": "ok", "transaction_status": payload.transaction_status}


@app.post("/api/user/delete-data")
def delete_user_data(email: str = Form(...)):
    result = privacy_manager.purge_user_data(email)
    return result


@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook receiver dari Fonnte:
    Menerima chat masuk dari WhatsApp, memproses dengan AI AGY (Gemini 3.8 Flash),
    dan mengirimkan balasan kembali ke WhatsApp pengguna secara otomatis.
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload format: {e}")

    sender = str(data.get("sender", "")).strip()
    message = str(data.get("message", "")).strip()
    name = str(data.get("name", "User")).strip()

    if not sender or not message:
        return {"status": "ignored", "reason": "Empty sender or message"}

    # Filter nomor admin: pastikan pesan hanya diproses jika berasal dari nomor Anda
    admin_phone = (settings.ADMIN_WHATSAPP_PHONE or "").strip()
    clean_sender = sender.replace("+", "").replace("-", "")
    clean_admin = admin_phone.replace("+", "").replace("-", "")

    # Cek kecocokan nomor (bisa berawalan 08 atau 62)
    is_admin = False
    if clean_admin:
        if clean_sender == clean_admin:
            is_admin = True
        elif clean_sender.startswith("62") and clean_admin.startswith("0") and clean_sender[2:] == clean_admin[1:]:
            is_admin = True
        elif clean_sender.startswith("0") and clean_admin.startswith("62") and clean_sender[1:] == clean_admin[2:]:
            is_admin = True

    if not is_admin:
        # Untuk nomor non-admin, bisa diabaikan atau diberi pesan penolakan sopan
        return {"status": "ignored", "reason": "Sender is not authorized admin"}

    # 1. Proses pesan via AI AGY Engine
    from ..services.ai_service import ai_service
    ai_reply = ai_service.process_incoming_message(user_message=message, sender_name=name)

    # 2. Balas langsung ke WhatsApp pengguna via Fonnte Gateway
    whatsapp_service.send_message(sender, ai_reply)

    return {"status": "success", "reply_sent": True, "reply_length": len(ai_reply)}

