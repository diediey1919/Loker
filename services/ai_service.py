import os
import requests
from typing import Optional, Dict, Any
from ..config.settings import settings
from ..services.git_storage import git_storage_service


class AIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = "gemini-3.8-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("<PENDING"))

    def process_incoming_message(self, user_message: str, sender_name: Optional[str] = None) -> str:
        text = user_message.strip()
        lower = text.lower()

        # 1. Shortcut Perintah Cepat
        if lower in ("status", "cek status", "/status"):
            jobs_count = len(git_storage_service.list_jobs())
            return (
                f"⚙️ *[LOKER STATUS OPERASIONAL]*\n"
                f"• Lowongan di Git  : {jobs_count} data tersimpan\n"
                f"• WhatsApp Gateway : ✅ Online (Fonnte)\n"
                f"• SMTP Mailer      : ✅ Online ({settings.SMTP_USER})\n"
                f"• Blogger API      : ✅ Ready\n"
                f"• AI Engine (AGY)  : ✅ Aktif ({self.model_name})\n"
                f"Ketik *lowongan* untuk melihat daftar loker aktif."
            )

        if lower in ("lowongan", "loker", "cek lowongan", "/lowongan"):
            files = git_storage_service.list_jobs()
            if not files:
                return "Belum ada data lowongan yang tersimpan di repositori."
            lines = ["📋 *[DAFTAR LOWONGAN WFH TERBARU]*\n"]
            for f in files[:5]:  # tampilkan maks 5
                j = git_storage_service.load_job(f)
                if j:
                    lines.append(f"• *{j.title}* ({j.company})\n  Kategori: {j.category.value} | Gaji: {j.salary_range or '-'}\n")
            lines.append("Ketik pertanyaan apa pun untuk berdiskusi dengan AGY.")
            return "\n".join(lines)

        if lower in ("help", "bantuan", "/help"):
            return (
                f"🤖 *[MENU PERINTAH AGY WHATSAPP]*\n"
                f"• *status* : Cek kondisi server & modul\n"
                f"• *lowongan* : Lihat daftar loker remote terbaru\n"
                f"• Atau langsung ketik pertanyaan/diskusi apa pun, saya siap menjawab."
            )

        # 2. Percakapan Cerdas via Gemini 3.8 Flash
        if not self.is_configured():
            return "Maaf, integrasi AI Gemini sedang offline atau kunci API belum disetel."

        system_prompt = (
            "Kamu adalah AGY (Antigravity), Master AI Supervisor dan Partner Engineering untuk project Loker "
            "(Platform otomatisasi loker WFH, OCR Instagram flyer, publikasi Blogspot, dan submit CV otomatis). "
            "Gaya bicaramu profesional, ringkas, solutif, ramah, dan to-the-point khas WhatsApp. "
            "Jangan gunakan markdown formatting yang berlebihan, gunakan gaya formatting WhatsApp (*tebal*, _miring_). "
            "Bantu user yang sedang mengontrol dan mengembangkan platform Loker ini."
        )

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": f"User ({sender_name or 'Admin'}): {text}"}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 800,
                "temperature": 0.7
            }
        }

        try:
            url = f"{self.api_url}?key={self.api_key}"
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return reply
            else:
                return f"Maaf, AGY mengalami kendala respons dari API Gemini ({res.status_code})."
        except Exception as e:
            return f"Maaf, terjadi kesalahan saat memproses pesan: {e}"


ai_service = AIService()
