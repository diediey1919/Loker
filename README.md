# Loker — Platform Otomatis Lowongan Kerja Remote

Platform cerdas untuk kurasi lowongan kerja WFH/Remote dari Instagram flyer, ekstraksi OCR, publikasi otomatis ke Blogger (Blogspot), penyimpanan terstruktur di Git JSON, serta fitur Quick Apply otomatis dengan 5 variasi pesan lamaran.

## Arsitektur Modular

```text
Loker/
├── config/             # Environment & settings loader (.env validator)
├── core/               # Pydantic data models (JobPost, Application, UserTier, Payments)
├── services/           # Modul bisnis terisolasi:
│   ├── blogger_service.py      # Publikasi otomatis HTML lowongan ke Blogger API
│   ├── whatsapp_service.py     # Gateway notifikasi via Fonnte API
│   ├── email_service.py        # Pengiriman lamaran/CV via SMTP Gmail App Password
│   ├── midtrans_service.py     # Transaksi Pro Lifetime Rp 49.000 (Snap Gateway)
│   ├── template_generator.py   # Generator pesan lamaran (5 format variasi)
│   ├── job_deduplicator.py     # Anti-duplikasi cerdas & interval 6-12 jam
│   └── git_storage.py          # Penyimpanan snapshot data JSON berbasis tanggal
├── tests/              # Test suite unit & integrasi
└── data/               # Penyimpanan job JSON lokal (data/jobs/YYYY-MM-DD/)
```

## Fitur Utama

1. **5-Template Application Generator**:
   - `Formal`: Struktur bahasa formal dan sopan untuk korporat/instansi.
   - `Santai`: Pendekatan hangat untuk startup/agensi kreatif.
   - `Singkat`: Ringkas, *to the point*, fokus portofolio & CV.
   - `Kreatif`: Narasi *engaging* dengan penekanan dampak hasil kerja.
   - `Follow-up`: Penegasan komitmen untuk kandidat yang menindaklanjuti lamaran.

2. **Deduplikasi Cerdas**:
   - Menyaring konten flyer/caption agar tidak di-ingest berulang kali.
   - Mengizinkan pemrosesan ulang hanya bila terdapat repost pembaruan di hari baru.

3. **Skema Monetisasi**:
   - **Free Plan**: Maksimal 3x pengiriman aplikasi CV.
   - **Pro Tier**: Rp 49.000 (Lifetime Access) terintegrasi Midtrans Snap.

4. **Keamanan & Privasi**:
   - Berkas `.env` diproteksi ketat dan diabaikan oleh Git.
   - Template `.env.example` disediakan tanpa membocorkan kredensial.
   - CV pelamar disimpan sementara dengan retensi maksimal 30 hari.

## Menjalankan Unit Test

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Jadwal Otomasi & Reporting

- **Laporan Sistem ke WhatsApp**: Dijalankan otomatis setiap 24 jam sekali (pukul 08:00 WIB) via Fonnte Gateway.
- **Log Pelaporan**: Tersimpan di `logs/whatsapp_report.log`.

