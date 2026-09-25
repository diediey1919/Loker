import time
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..config.settings import settings
from ..core.models import JobPost, JobCategory
from ..core.privacy import privacy_manager
from ..services.job_deduplicator import job_deduplicator
from ..services.git_storage import git_storage_service
from ..services.blogger_service import blogger_service
from ..services.whatsapp_service import whatsapp_service
from ..services.email_service import email_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [HermesWorker] %(message)s")
logger = logging.getLogger("HermesWorker")


class HermesScheduler:
    """
    Hermes Agent Orchestrator:
    - Background task execution per 6-12 jam
    - Ingest Instagram flyer, deduplikasi, simpan JSON Git, render Blogger
    - Failover cache & retry 3x
    - Auto-purge CV kedaluwarsa (> 30 hari)
    - Admin daily alert report via WhatsApp & SMTP
    """

    def __init__(self, interval_hours: int = 6):
        self.interval_seconds = interval_hours * 3600
        self.failover_cache_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "storage",
            "failover_queue.json"
        )
        os.makedirs(os.path.dirname(self.failover_cache_path), exist_ok=True)

    def load_failover_queue(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.failover_cache_path):
            try:
                with open(self.failover_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_failover_queue(self, queue: List[Dict[str, Any]]):
        with open(self.failover_cache_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)

    def execute_with_retry(self, action_name: str, fn, max_retries: int = 3) -> Any:
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Mengeksekusi {action_name} (Percobaan {attempt}/{max_retries})...")
                return fn()
            except Exception as e:
                last_error = e
                logger.warning(f"Gagal pada percobaan {attempt} ({action_name}): {e}")
                time.sleep(2 * attempt)
        raise RuntimeError(f"Aksi {action_name} gagal setelah {max_retries} kali: {last_error}")

    def run_ingest_cycle(self, mock_posts: Optional[List[JobPost]] = None) -> Dict[str, Any]:
        logger.info("Memulai siklus crawling Instagram & ekstraksi lowongan...")
        stats = {
            "processed": 0,
            "deduplicated": 0,
            "saved_to_git": 0,
            "blogger_payloads": 0,
            "cv_purged": 0,
            "errors": []
        }

        # 1. Bersihkan CV usang (> 30 hari)
        stats["cv_purged"] = privacy_manager.purge_expired_cvs()
        logger.info(f"CV usang yang dimusnahkan otomatis: {stats['cv_purged']}")

        # 2. Ambil data postingan
        posts = mock_posts or []
        for post in posts:
            stats["processed"] += 1
            try:
                # Deduplikasi Cerdas
                if not job_deduplicator.should_process(
                    post.source_post_id,
                    post.title,
                    post.company or "",
                    post.description,
                    post.posted_at
                ):
                    stats["deduplicated"] += 1
                    logger.info(f"Post {post.source_post_id} dideduplikasi.")
                    continue

                # Simpan ke Git JSON dengan retry
                def save_action():
                    return git_storage_service.save_job(post)

                saved_file = self.execute_with_retry(f"SaveJob_{post.id}", save_action)
                stats["saved_to_git"] += 1

                # Generate payload Blogger
                blogger_payload = blogger_service.create_post_payload(post)
                stats["blogger_payloads"] += 1

            except Exception as err:
                stats["errors"].append({"post_id": post.id, "error": str(err)})
                # Masukkan ke failover queue jika terjadi gangguan
                q = self.load_failover_queue()
                q.append(post.model_dump())
                self.save_failover_queue(q)

        logger.info(f"Siklus selesai. Stats: {stats}")
        return stats

    def send_admin_daily_report(self, stats: Dict[str, Any], admin_phone: Optional[str] = None):
        summary_msg = (
            f"📊 *Laporan Harian Hermes Worker (Loker)*\n"
            f"• Lowongan Diproses : {stats.get('processed', 0)}\n"
            f"• Duplikat Dilewati : {stats.get('deduplicated', 0)}\n"
            f"• Tersimpan di Git  : {stats.get('saved_to_git', 0)}\n"
            f"• CV Usang Dihapus  : {stats.get('cv_purged', 0)}\n"
            f"• Error Terjadi     : {len(stats.get('errors', []))}\n"
            f"Waktu Eksekusi: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        # Alert via WhatsApp jika nomor admin disetel
        if admin_phone and settings.is_whatsapp_ready():
            whatsapp_service.send_message(admin_phone, summary_msg)

        # Alert via SMTP jika disetel
        if settings.is_smtp_ready() and settings.SMTP_USER:
            email_service.send_application_email(
                to_email=settings.SMTP_USER,
                subject="[Loker System] Ringkasan Harian Hermes Worker",
                body=summary_msg
            )


hermes_scheduler = HermesScheduler()
