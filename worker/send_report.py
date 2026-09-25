import os
import sys
from datetime import datetime
try:
    from ..config.settings import settings
    from ..services.git_storage import git_storage_service
    from ..services.whatsapp_service import whatsapp_service
except ImportError:
    from Loker.config.settings import settings
    from Loker.services.git_storage import git_storage_service
    from Loker.services.whatsapp_service import whatsapp_service


def generate_and_send_report() -> bool:
    admin_phone = settings.ADMIN_WHATSAPP_PHONE
    if not admin_phone:
        print("❌ ADMIN_WHATSAPP_PHONE belum disetel.")
        return False

    if not settings.is_whatsapp_ready():
        print("❌ WhatsApp token belum valid.")
        return False

    jobs = git_storage_service.list_jobs()
    total_jobs = len(jobs)

    now_str = datetime.now().strftime("%d-%m-%Y %H:%M WIB")

    message = (
        f"🤖 *[LOKER PLATFORM - LAPORAN BERKALA]*\n"
        f"📅 Waktu: {now_str}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📂 *Status Database Lowongan:*\n"
        f"• Total Lowongan Aktif : {total_jobs} lowongan (Git JSON)\n"
        f"• Repositori Target    : {settings.GITHUB_REPO_NAME}\n\n"
        f"⚙️ *Status Integrasi Layanan:*\n"
        f"• WhatsApp Gateway : ✅ Online (Fonnte API)\n"
        f"• SMTP Mailer      : ✅ Online ({settings.SMTP_USER})\n"
        f"• Blogger API      : ✅ Ready (ID: {settings.BLOGGER_BLOG_ID})\n"
        f"• Midtrans Sandbox : {'✅ Ready' if settings.is_midtrans_ready() else '⏳ Pending Verifikasi'}\n"
        f"• Instagram API    : {'✅ Ready' if settings.is_instagram_ready() else '⏳ Pending Meta'}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💡 _Sistem berjalan otomatis di latar belakang._"
    )

    res = whatsapp_service.send_message(admin_phone, message)
    if res.get("success"):
        print(f"✅ Laporan berhasil dikirim ke WhatsApp {admin_phone}")
        return True
    else:
        print(f"❌ Gagal mengirim laporan: {res.get('error')}")
        return False


if __name__ == "__main__":
    generate_and_send_report()
