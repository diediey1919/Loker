import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set


class PrivacyManager:
    """
    Mengelola siklus hidup data pelamar:
    - Retensi CV maksimal 30 hari (auto-purge)
    - Mode Privat: langsung menghapus CV setelah lamaran dikirim
    - Hak penghapusan data mandiri (Right to be Forgotten)
    - Tracking kuota Free Plan (maks 3x) vs Pro Lifetime (unlimited)
    """

    def __init__(self, storage_dir: Optional[str] = None, max_retention_days: int = 30):
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            self.storage_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "storage",
                "cv"
            )
        os.makedirs(self.storage_dir, exist_ok=True)
        self.max_retention_days = max_retention_days

        # Memory store: user_email -> { "apply_count": int, "tier": "free"|"pro_lifetime", "favorite_categories": [] }
        self._user_state: Dict[str, Dict[str, Any]] = {}

    def get_user_state(self, email: str) -> Dict[str, Any]:
        normalized = email.strip().lower()
        if normalized not in self._user_state:
            self._user_state[normalized] = {
                "apply_count": 0,
                "tier": "free",
                "favorite_categories": [],
                "created_at": datetime.utcnow().isoformat()
            }
        return self._user_state[normalized]

    def upgrade_to_pro_lifetime(self, email: str) -> bool:
        user = self.get_user_state(email)
        user["tier"] = "pro_lifetime"
        return True

    def can_user_apply(self, email: str) -> bool:
        user = self.get_user_state(email)
        if user["tier"] == "pro_lifetime":
            return True
        return user["apply_count"] < 3

    def record_apply(self, email: str, category: Optional[str] = None):
        user = self.get_user_state(email)
        user["apply_count"] += 1
        if category and category not in user["favorite_categories"]:
            user["favorite_categories"].append(category)

    def save_temp_cv(self, email: str, filename: str, file_bytes: bytes) -> str:
        safe_email = email.replace("@", "_at_").replace(".", "_")
        timestamp = int(time.time())
        safe_name = f"{safe_email}_{timestamp}_{filename}"
        target_path = os.path.join(self.storage_dir, safe_name)
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return target_path

    def purge_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except OSError:
            pass
        return False

    def handle_post_apply_privacy(self, file_path: str, private_mode: bool) -> bool:
        """Jika pengguna mengaktifkan Private Mode, CV segera dimusnahkan."""
        if private_mode:
            return self.purge_file(file_path)
        return False

    def purge_expired_cvs(self) -> int:
        """Membersihkan file CV yang usianya melebihi 30 hari."""
        cutoff_seconds = time.time() - (self.max_retention_days * 86400)
        purged_count = 0
        if not os.path.exists(self.storage_dir):
            return 0

        for fname in os.listdir(self.storage_dir):
            full_path = os.path.join(self.storage_dir, fname)
            if os.path.isfile(full_path):
                if os.path.getmtime(full_path) < cutoff_seconds:
                    if self.purge_file(full_path):
                        purged_count += 1
        return purged_count

    def purge_user_data(self, email: str) -> Dict[str, Any]:
        """Menghapus total semua riwayat & berkas CV milik pengguna tertentu."""
        safe_email = email.replace("@", "_at_").replace(".", "_")
        deleted_files = 0
        if os.path.exists(self.storage_dir):
            for fname in os.listdir(self.storage_dir):
                if fname.startswith(safe_email):
                    full_path = os.path.join(self.storage_dir, fname)
                    if self.purge_file(full_path):
                        deleted_files += 1

        normalized = email.strip().lower()
        if normalized in self._user_state:
            del self._user_state[normalized]

        return {
            "success": True,
            "deleted_cv_count": deleted_files,
            "user_records_erased": True
        }


privacy_manager = PrivacyManager()
