import os
import shutil
from datetime import datetime, date, timedelta
from Loker.config.settings import settings
from Loker.core.models import (
    JobPost,
    JobCategory,
    TemplateType,
    ApplicationRequest,
    MidtransTransactionPayload,
)
from Loker.services.template_generator import TemplateGeneratorService
from Loker.services.blogger_service import blogger_service
from Loker.services.job_deduplicator import JobDeduplicator
from Loker.services.git_storage import GitStorageService
from Loker.services.midtrans_service import MidtransService
from Loker.services.whatsapp_service import whatsapp_service
from Loker.services.email_service import email_service


def test_settings_loaded():
    assert settings.GITHUB_AUTH_TYPE == "ssh"
    assert settings.BLOGGER_BLOG_ID == "6596171284243525524"
    assert settings.is_whatsapp_ready() is True
    assert settings.is_smtp_ready() is True
    # Credentials that are marked pending should evaluate to False
    assert settings.is_instagram_ready() is False
    assert settings.is_midtrans_ready() is False
    assert settings.is_google_oauth_ready() is False


def test_template_generator_all_variations():
    job = JobPost(
        id="job-001",
        title="Frontend React Developer",
        company="Tech Nusantara",
        category=JobCategory.IT,
        description="Membangun dashboard interaktif WFH",
        requirements=["React", "TypeScript", "Tailwind CSS"],
        source_post_id="post_12345"
    )
    app = ApplicationRequest(
        applicant_name="Budi Santoso",
        applicant_email="budi@example.com",
        applicant_phone="08123456789",
        portfolio_url="https://github.com/budi",
        target_job_id="job-001",
        template_type=TemplateType.FORMAL,
        cv_filename="cv_budi.pdf",
        cv_temp_path="/tmp/cv_budi.pdf"
    )

    templates = TemplateGeneratorService.generate_all_templates(job, app)
    assert len(templates) == 5
    assert TemplateType.FORMAL in templates
    assert TemplateType.SANTAI in templates
    assert TemplateType.SINGKAT in templates
    assert TemplateType.KREATIF in templates
    assert TemplateType.FOLLOW_UP in templates

    formal_msg = templates[TemplateType.FORMAL]
    assert "Yth. Tim Rekrutmen Tech Nusantara" in formal_msg.body
    assert "Budi Santoso" in formal_msg.body

    kreatif_msg = templates[TemplateType.KREATIF]
    assert "🚀" in kreatif_msg.subject


def test_blogger_service_rendering():
    job = JobPost(
        id="job-002",
        title="UI/UX Designer",
        company="Studio Desain Kreatif",
        category=JobCategory.DESAIN,
        tags=["Figma", "DesignSystem"],
        description="Mendesain wireframe dan flow aplikasi mobile.",
        requirements=["Figma", "Design Sprint"],
        source_post_id="post_uiux_999"
    )

    html = blogger_service.render_job_html(job)
    assert "Studio Desain Kreatif" in html
    assert "UI/UX Designer" in html
    assert "Figma" in html

    payload = blogger_service.create_post_payload(job)
    assert "[Lowongan Remote] UI/UX Designer - Studio Desain Kreatif" in payload["title"]
    assert "Desain" in payload["labels"]


def test_job_deduplicator():
    dedup = JobDeduplicator()
    post_id = "ig_post_888"
    title = "Content Writer WFH"
    company = "Media Digital"
    desc = "Menulis artikel SEO 1000 kata"

    now = datetime(2026, 9, 25, 10, 0, 0)
    # First encounter -> should process
    assert dedup.should_process(post_id, title, company, desc, now) is True

    # Same post ID and same content on same day -> duplicate
    assert dedup.should_process(post_id, title, company, desc, now) is False

    # Different post ID with identical content on same day -> duplicate
    assert dedup.should_process("ig_post_999", title, company, desc, now) is False

    # Reposted on next day -> should process
    next_day = now + timedelta(days=1)
    assert dedup.should_process(post_id, title, company, desc, next_day) is True


def test_git_storage_lifecycle(tmp_path):
    test_dir = str(tmp_path / "jobs")
    storage = GitStorageService(base_data_dir=test_dir)

    job = JobPost(
        id="job-test-777",
        title="Backend Python Engineer",
        company="Startup Kilat",
        category=JobCategory.IT,
        description="FastAPI & PostgreSQL remote work",
        source_post_id="ig_test_777"
    )

    saved_path = storage.save_job(job)
    assert os.path.exists(saved_path)

    loaded_job = storage.load_job(saved_path)
    assert loaded_job is not None
    assert loaded_job.id == "job-test-777"
    assert loaded_job.title == "Backend Python Engineer"


def test_midtrans_signature_verification():
    service = MidtransService(server_key="SB-Mid-server-TEST12345", is_production=False)
    order_id = "ORDER-20260925-01"
    status_code = "200"
    gross_amount = "49000.00"

    import hashlib
    raw = f"{order_id}{status_code}{gross_amount}SB-Mid-server-TEST12345"
    valid_sig = hashlib.sha512(raw.encode("utf-8")).hexdigest()

    assert service.verify_signature(order_id, status_code, gross_amount, valid_sig) is True
    assert service.verify_signature(order_id, status_code, gross_amount, "invalid_sig") is False
