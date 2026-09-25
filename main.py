import argparse
import sys
import os
import json
from datetime import datetime
from Loker.config.settings import settings
from Loker.core.models import (
    JobPost,
    JobCategory,
    TemplateType,
    ApplicationRequest,
    ApplicationResult,
)
from Loker.services.template_generator import TemplateGeneratorService
from Loker.services.job_deduplicator import job_deduplicator
from Loker.services.git_storage import git_storage_service
from Loker.services.blogger_service import blogger_service
from Loker.services.whatsapp_service import whatsapp_service
from Loker.services.email_service import email_service


def show_status():
    print("=" * 60)
    print("STATUS KESIAPAN KREDENSIAL & MODUL LOKER")
    print("=" * 60)
    print(f"GitHub Auth Type    : {settings.GITHUB_AUTH_TYPE} (SSH Key Active)")
    print(f"Blogger Configured  : {'✅ SIAP' if settings.is_blogger_ready() else '❌ BELUM LENGKAP'}")
    print(f"WhatsApp Gateway    : {'✅ SIAP (Fonnte Token Aktif)' if settings.is_whatsapp_ready() else '❌ BELUM KONFIGURASI'}")
    print(f"SMTP Mailer         : {'✅ SIAP (Gmail App Password Aktif)' if settings.is_smtp_ready() else '❌ BELUM KONFIGURASI'}")
    print(f"Midtrans Gateway    : {'✅ SIAP' if settings.is_midtrans_ready() else '⏳ PENDING (Verifikasi KTP)'}")
    print(f"Instagram Graph API : {'✅ SIAP' if settings.is_instagram_ready() else '⏳ PENDING (Verifikasi Meta)'}")
    print(f"Google OAuth        : {'✅ SIAP' if settings.is_google_oauth_ready() else '⏳ PENDING (Domain / Redirect URI)'}")
    print("=" * 60)


def ingest_sample():
    print("\n[1/4] Menginisialisasi sample data lowongan WFH Instagram...")
    sample_jobs = [
        JobPost(
            id="job-sample-wfh-01",
            title="Senior Fullstack Python & React Engineer",
            company="PT Solusi Digital Inovasi",
            category=JobCategory.IT,
            tags=["Python", "FastAPI", "React", "WFH", "Remote"],
            description="Dicari Senior Fullstack Engineer yang berpengalaman membangun arsitektur API mandiri dan SPA. 100% Remote / WFH.",
            requirements=[
                "Pengalaman minimal 3 tahun dengan Python / FastAPI",
                "Fasih menggunakan React.js dan TypeScript",
                "Terbiasa dengan Git dan remote collaboration"
            ],
            contact_email="recruitment@solusidigital.id",
            contact_whatsapp="081234567890",
            salary_range="Rp 12.000.000 - Rp 18.000.000",
            source_post_id="ig_sample_post_1001",
            source_url="https://instagram.com/p/sample1001",
            flyer_image_url="https://images.unsplash.com/photo-1522071820081-009f0129c71c",
            posted_at=datetime.utcnow()
        ),
        JobPost(
            id="job-sample-wfh-02",
            title="UI/UX & Graphic Designer WFH",
            company="Kolektif Studio Nusantara",
            category=JobCategory.DESAIN,
            tags=["UI/UX", "Figma", "DesignSystem", "RemoteWorkID"],
            description="Mencari desainer produk digital untuk pembuatan design system dan materi promosi media sosial.",
            requirements=[
                "Mahir Figma, Adobe Illustrator, atau Photoshop",
                "Portofolio UI/UX yang dapat diverifikasi",
                "Mampu bekerja mandiri dengan target mingguan"
            ],
            contact_email="halo@kolektifstudio.com",
            salary_range="Rp 7.000.000 - Rp 10.000.000",
            source_post_id="ig_sample_post_1002",
            source_url="https://instagram.com/p/sample1002",
            posted_at=datetime.utcnow()
        )
    ]

    for job in sample_jobs:
        print(f"\n--- Memproses Lowongan: {job.title} ---")
        
        # 1. Cek Deduplikasi
        should_process = job_deduplicator.should_process(
            source_post_id=job.source_post_id,
            title=job.title,
            company=job.company or "",
            description=job.description,
            post_timestamp=job.posted_at
        )
        if not should_process:
            print(f"⚠️ [Deduplikasi] Post {job.source_post_id} terdeteksi sebagai duplikat. Dilewati.")
            continue

        print(f"✔ [Deduplikasi Lolos] Konten unik terverifikasi.")

        # 2. Simpan ke Git JSON Storage
        saved_file = git_storage_service.save_job(job)
        print(f"✔ [Storage] Data lowongan disimpan ke: {saved_file}")

        # 3. Format postingan Blogspot
        payload = blogger_service.create_post_payload(job)
        print(f"✔ [Blogger Renderer] Judul Blog: \"{payload['title']}\"")
        print(f"✔ [Blogger Labels] {payload['labels']}")

    print("\n✅ Proses Ingest Sample Selesai.")


def list_jobs():
    files = git_storage_service.list_jobs()
    print(f"\nTotal lowongan tersimpan: {len(files)}")
    print("-" * 60)
    for f in files:
        job = git_storage_service.load_job(f)
        if job:
            print(f"• [{job.id}] {job.title} | {job.company} | Kategori: {job.category.value} | Gaji: {job.salary_range or '-'}")
            print(f"  File: {f}")
    print("-" * 60)


def apply_sample(job_id: str, template_choice: str = "formal", dispatch_wa: bool = False):
    files = git_storage_service.list_jobs()
    target_job = None
    for f in files:
        j = git_storage_service.load_job(f)
        if j and j.id == job_id:
            target_job = j
            break

    if not target_job:
        print(f"❌ Lowongan dengan ID '{job_id}' tidak ditemukan.")
        return

    # Sample data pelamar
    applicant = ApplicationRequest(
        applicant_name="Muhammad Farhan",
        applicant_email="farhan.dev@example.com",
        applicant_phone="085123456789",
        portfolio_url="https://github.com/farhan-engineer",
        target_job_id=target_job.id,
        template_type=TemplateType(template_choice.lower()),
        cv_filename="CV_Muhammad_Farhan_2026.pdf",
        cv_temp_path="/tmp/CV_Muhammad_Farhan_2026.pdf"
    )

    print("\n" + "=" * 60)
    print(f"SIMULASI APLIKASI LAMARAN: {target_job.title}")
    print("=" * 60)
    print(f"Pelamar : {applicant.applicant_name} ({applicant.applicant_email})")
    print(f"Kontak  : {applicant.applicant_phone}")
    print(f"Tujuan  : {target_job.company} ({target_job.contact_email or '-'})")
    print("-" * 60)

    # Generate 5 Template
    all_templates = TemplateGeneratorService.generate_all_templates(target_job, applicant)
    print(f"✔ Berhasil mengenerate 5 variasi pesan lamaran.")

    chosen_template = all_templates.get(applicant.template_type)
    if not chosen_template:
        chosen_template = all_templates[TemplateType.FORMAL]

    print(f"\n[Template Terpilih: {chosen_template.template_type.value.upper()}]")
    print(f"Subject : {chosen_template.subject}")
    print("Body    :")
    print(chosen_template.body)
    print("-" * 60)

    # Simulasi Pengiriman Email
    print("\n[Simulasi Dispatch Lamaran]")
    print(f"1. Email ke {target_job.contact_email}:")
    print(f"   Menggunakan SMTP Gmail ({settings.SMTP_USER}) dengan lampiran {applicant.cv_filename} (Mode Simulasi / Safe Test)")
    
    # Pengiriman Notifikasi WhatsApp via Fonnte jika diminta
    if dispatch_wa:
        if settings.is_whatsapp_ready():
            wa_notif = (
                f"Halo {applicant.applicant_name}, lamaran Anda untuk posisi *{target_job.title}* di *{target_job.company}* "
                f"telah berhasil dikirimkan via sistem Loker. Semoga sukses!"
            )
            print(f"2. Mengirimkan konfirmasi via WhatsApp ke {applicant.applicant_phone}...")
            res = whatsapp_service.send_message(applicant.applicant_phone, wa_notif)
            print(f"   Hasil WhatsApp Gateway: {res}")
        else:
            print("2. WhatsApp Gateway belum dikonfigurasi.")
    else:
        print("2. Notifikasi WhatsApp: dilewati (gunakan flag --send-wa untuk mengaktifkan).")

    print("\n✅ Simulasi Dispatch Lamaran Berhasil.")


def main():
    parser = argparse.ArgumentParser(description="CLI Runner Sistem Loker")
    subparsers = parser.add_subparsers(dest="command", help="Perintah yang tersedia")

    # Command: status
    subparsers.add_parser("status", help="Cek status kredensial dan kesiapan modul")

    # Command: ingest-sample
    subparsers.add_parser("ingest-sample", help="Ingest sample lowongan kerja, deduplikasi, dan simpan ke Git JSON")

    # Command: list-jobs
    subparsers.add_parser("list-jobs", help="Daftar lowongan kerja yang tersimpan di repositori")

    # Command: apply-sample
    apply_parser = subparsers.add_parser("apply-sample", help="Simulasi pelamar mengajukan CV ke lowongan")
    apply_parser.add_argument("--job-id", type=str, default="job-sample-wfh-01", help="ID lowongan kerja sasaran")
    apply_parser.add_argument(
        "--template",
        type=str,
        choices=["formal", "santai", "singkat", "kreatif", "follow_up"],
        default="formal",
        help="Pilihan salah satu dari 5 template pesan lamaran"
    )
    apply_parser.add_argument("--send-wa", action="store_true", help="Kirim notifikasi via live WhatsApp Gateway")

    args = parser.parse_args()

    if args.command == "status":
        show_status()
    elif args.command == "ingest-sample":
        ingest_sample()
    elif args.command == "list-jobs":
        list_jobs()
    elif args.command == "apply-sample":
        apply_sample(job_id=args.job_id, template_choice=args.template, dispatch_wa=args.send_wa)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
