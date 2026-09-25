import hashlib
from datetime import datetime, date
from typing import Dict, Set, Optional, Any


class JobDeduplicator:
    def __init__(self):
        # Menyimpan mapping: post_id -> (content_hash, last_posted_date)
        self._seen_posts: Dict[str, Dict[str, Any]] = {}
        self._processed_hashes: Set[str] = set()

    @staticmethod
    def compute_content_hash(title: str, company: str, description: str) -> str:
        normalized = f"{title.strip().lower()}|{company.strip().lower()}|{description.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def should_process(
        self,
        source_post_id: str,
        title: str,
        company: str,
        description: str,
        post_timestamp: Optional[datetime] = None
    ) -> bool:
        content_hash = self.compute_content_hash(title, company, description)
        current_date = (post_timestamp or datetime.utcnow()).date()

        # 1. Jika post ID belum pernah terlihat dan hash konten belum ada -> PROSES
        if source_post_id not in self._seen_posts and content_hash not in self._processed_hashes:
            self._register(source_post_id, content_hash, current_date)
            return True

        # 2. Jika post ID sudah pernah ada
        record = self._seen_posts.get(source_post_id)
        if record:
            prev_date = record.get("date")
            prev_hash = record.get("hash")

            # Jika konten berubah atau diposting ulang pada hari yang berbeda/hari ini dengan pembaruan
            if content_hash != prev_hash or current_date > prev_date:
                self._register(source_post_id, content_hash, current_date)
                return True
            return False

        # 3. Konten identik pernah ada di post lain hari ini -> LEWATKAN (Duplikat)
        if content_hash in self._processed_hashes:
            return False

        return True

    def _register(self, post_id: str, content_hash: str, post_date: date):
        self._seen_posts[post_id] = {
            "hash": content_hash,
            "date": post_date
        }
        self._processed_hashes.add(content_hash)


job_deduplicator = JobDeduplicator()
