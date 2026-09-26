import os
import sys
import argparse
from datetime import datetime

# Pastikan workspace root masuk ke sys.path
sys.path.insert(0, "/home/ubuntu")

from Loker.config.settings import settings
from Loker.core.models import JobPost, JobCategory
from Loker.services.blogger_service import blogger_service


def create_sample_job() -> JobPost:
    return JobPost(
        id="job-sample-remote-01",
        title="Senior Fullstack Python & React Developer",
        company="PT Teknologi Maju Nusantara",
        category=JobCategory.IT,
        tags=["Python", "FastAPI", "React", "WFH", "Remote", "LowonganKerja"],
        description="Membangun platform aplikasi web performa tinggi dengan arsitektur microservices dan API modern. Fleksibilitas kerja 100% Remote / WFH dari mana saja.",
        requirements=[
            "Pengalaman minimal 3 tahun dengan Python (FastAPI/Django)",
            "Mahir React.js, TypeScript, dan State Management",
            "Memahami RESTful API, Docker, dan CI/CD pipeline",
            "Komunikatif dan terbiasa bekerja mandiri secara remote"
        ],
        salary_range="Rp 15.000.000 - Rp 22.000.000",
        contact_email="karir@teknologimaju.id",
        contact_whatsapp="081298765432",
        source_post_id="sample_ig_post_001",
        source_url="https://instagram.com/p/sample_post_001",
        flyer_image_url="https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800",
        posted_at=datetime.utcnow()
    )


def main():
    parser = argparse.ArgumentParser(description="Generator & Publisher Sample Post Blogspot")
    parser.add_argument("--token", type=str, default=None, help="Google OAuth Bearer Access Token untuk direct live publish")
    args = parser.parse_args()

    job = create_sample_job()
    payload = blogger_service.create_post_payload(job)

    # 1. Simpan HTML preview
    preview_path = "/home/ubuntu/Loker/storage/sample_post_preview.html"
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(payload["content"])

    print("=" * 65)
    print("SAMPLE POST BLOGGER BERHASIL DIBUAT")
    print("=" * 65)
    print(f"Target Blog ID : {settings.BLOGGER_BLOG_ID}")
    print(f"Judul Post     : {payload['title']}")
    print(f"Labels / Tags  : {payload['labels']}")
    print(f"Preview File   : {preview_path}")
    print("-" * 65)

    if not args.token:
        print("[STATUS: DRY RUN / PREVIEW]")
        print("Konten HTML telah digenerate dan tersimpan di file preview.")
        print("Untuk mem-publish LIVE ke Blogspot secara langsung via API:")
        print("python Loker/scripts/test_blogger_post.py --token <GOOGLE_OAUTH_ACCESS_TOKEN>")
        print("=" * 65)
        return

    # 2. Live Publish jika token diberikan
    print(f"Mencoba mem-publish secara live ke Blogspot...")
    res = blogger_service.publish_post(job, access_token=args.token)
    if res.get("success"):
        post_data = res.get("post_data", {})
        print("✅ BERHASIL DIPUBLISH SECARA LIVE KE BLOGSPOT!")
        print(f"Post ID   : {post_data.get('id')}")
        print(f"URL Post  : {post_data.get('url')}")
    else:
        print(f"❌ Gagal mem-publish: {res.get('error')}")
    print("=" * 65)


if __name__ == "__main__":
    main()
