import os
import time
from datetime import datetime, timedelta
import pytest

from Loker.core.privacy import PrivacyManager
from Loker.core.models import JobPost, JobCategory, TemplateType
from Loker.services.midtrans_service import MidtransService
from Loker.worker.scheduler import HermesScheduler


def test_free_tier_and_lifetime_upgrade(tmp_path):
    pm = PrivacyManager(storage_dir=str(tmp_path / "cv"))
    email = "kandidat@example.com"

    # Awalnya 0 apply -> can apply
    assert pm.can_user_apply(email) is True

    # 1st apply
    pm.record_apply(email, "IT")
    assert pm.can_user_apply(email) is True

    # 2nd apply
    pm.record_apply(email, "IT")
    assert pm.can_user_apply(email) is True

    # 3rd apply
    pm.record_apply(email, "Desain")
    # Setelah 3x -> kuota habis
    assert pm.can_user_apply(email) is False

    # Upgrade ke Pro Lifetime via Midtrans
    pm.upgrade_to_pro_lifetime(email)
    assert pm.can_user_apply(email) is True

    # Melamar ke-4 tetap diizinkan
    pm.record_apply(email, "Admin")
    assert pm.can_user_apply(email) is True


def test_private_mode_instant_cv_purge(tmp_path):
    pm = PrivacyManager(storage_dir=str(tmp_path / "cv"))
    email = "private_user@example.com"
    content = b"PDF DUMMY CV CONTENT"
    cv_path = pm.save_temp_cv(email, "my_cv.pdf", content)

    assert os.path.exists(cv_path)

    # Ketika Private Mode = False -> berkas dipertahankan
    pm.handle_post_apply_privacy(cv_path, private_mode=False)
    assert os.path.exists(cv_path)

    # Ketika Private Mode = True -> berkas langsung musnah
    is_purged = pm.handle_post_apply_privacy(cv_path, private_mode=True)
    assert is_purged is True
    assert not os.path.exists(cv_path)


def test_auto_purge_expired_cv_30_days(tmp_path):
    pm = PrivacyManager(storage_dir=str(tmp_path / "cv"), max_retention_days=30)
    email = "old_user@example.com"

    # Berkas baru
    new_cv = pm.save_temp_cv(email, "new_cv.pdf", b"new content")
    # Berkas usang (diset mtime 35 hari lalu)
    old_cv = pm.save_temp_cv(email, "old_cv.pdf", b"old content")
    thirty_five_days_ago = time.time() - (35 * 86400)
    os.utime(old_cv, (thirty_five_days_ago, thirty_five_days_ago))

    purged = pm.purge_expired_cvs()
    assert purged == 1
    assert not os.path.exists(old_cv)
    assert os.path.exists(new_cv)


def test_right_to_be_forgotten(tmp_path):
    pm = PrivacyManager(storage_dir=str(tmp_path / "cv"))
    email = "forget_me@example.com"
    cv1 = pm.save_temp_cv(email, "cv1.pdf", b"test1")
    cv2 = pm.save_temp_cv(email, "cv2.pdf", b"test2")
    pm.record_apply(email, "IT")

    assert os.path.exists(cv1)
    assert os.path.exists(cv2)

    res = pm.purge_user_data(email)
    assert res["success"] is True
    assert res["deleted_cv_count"] == 2
    assert not os.path.exists(cv1)
    assert not os.path.exists(cv2)

    # State akun kembali bersih
    user_state = pm.get_user_state(email)
    assert user_state["apply_count"] == 0


def test_hermes_scheduler_retry_mechanism():
    scheduler = HermesScheduler(interval_hours=6)
    call_count = 0

    def faulty_action():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary network glitch")
        return "SUCCESS"

    result = scheduler.execute_with_retry("TestRetry", faulty_action, max_retries=3)
    assert result == "SUCCESS"
    assert call_count == 3
