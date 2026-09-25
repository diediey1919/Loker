from typing import Dict
from ..core.models import TemplateType, GeneratedMessage, JobPost, ApplicationRequest


class TemplateGeneratorService:
    @staticmethod
    def generate_all_templates(job: JobPost, app: ApplicationRequest) -> Dict[TemplateType, GeneratedMessage]:
        return {
            TemplateType.FORMAL: TemplateGeneratorService.generate_formal(job, app),
            TemplateType.SANTAI: TemplateGeneratorService.generate_santai(job, app),
            TemplateType.SINGKAT: TemplateGeneratorService.generate_singkat(job, app),
            TemplateType.KREATIF: TemplateGeneratorService.generate_kreatif(job, app),
            TemplateType.FOLLOW_UP: TemplateGeneratorService.generate_follow_up(job, app),
        }

    @staticmethod
    def generate_formal(job: JobPost, app: ApplicationRequest) -> GeneratedMessage:
        subject = f"Lamaran Pekerjaan: {job.title} - {app.applicant_name}"
        body = (
            f"Yth. Tim Rekrutmen {job.company},\n\n"
            f"Perkenalkan, saya {app.applicant_name}. Melalui pesan ini, saya bermaksud untuk mengajukan lamaran "
            f"pekerjaan untuk posisi {job.title} yang dipublikasikan oleh {job.company}.\n\n"
            f"Dengan latar belakang keahlian dan komitmen kerja profesional yang saya miliki, saya yakin dapat "
            f"memberikan kontribusi optimal secara remote untuk tim Anda. Terlampir saya sertakan CV dan tautan "
            f"portofolio saya:\n"
            f"Portofolio: {app.portfolio_url or '-'}\n\n"
            f"Besar harapan saya untuk memperoleh kesempatan wawancara guna membahas kualifikasi saya lebih lanjut.\n\n"
            f"Hormat saya,\n"
            f"{app.applicant_name}\n"
            f"Email: {app.applicant_email}\n"
            f"Kontak: {app.applicant_phone or '-'}"
        )
        return GeneratedMessage(template_type=TemplateType.FORMAL, subject=subject, body=body)

    @staticmethod
    def generate_santai(job: JobPost, app: ApplicationRequest) -> GeneratedMessage:
        subject = f"Halo Tim {job.company}! Tertarik bergabung untuk posisi {job.title}"
        body = (
            f"Halo tim {job.company},\n\n"
            f"Saya {app.applicant_name}, sangat antusias melihat informasi lowongan untuk posisi {job.title}. "
            f"Saya terbiasa bekerja secara remote dan memiliki pengalaman yang relevan untuk kebutuhan proyek ini.\n\n"
            f"Biar lebih jelas, teman-teman bisa cek ringkasan CV yang saya lampirkan beserta portofolio saya di:\n"
            f"{app.portfolio_url or '(CV terlampir)'}\n\n"
            f"Kira-kira kapan ada waktu luang untuk ngobrol santai seputar ekspektasi posisi ini?\n\n"
            f"Salam hangat,\n"
            f"{app.applicant_name}\n"
            f"{app.applicant_email}"
        )
        return GeneratedMessage(template_type=TemplateType.SANTAI, subject=subject, body=body)

    @staticmethod
    def generate_singkat(job: JobPost, app: ApplicationRequest) -> GeneratedMessage:
        subject = f"Aplikasi {job.title} - {app.applicant_name}"
        body = (
            f"Halo Rekruter {job.company},\n\n"
            f"Saya {app.applicant_name}, melamar untuk posisi {job.title} (Remote).\n"
            f"- Kualifikasi: Sesuai deskripsi kebutuhan peran\n"
            f"- Portofolio: {app.portfolio_url or '-'}\n"
            f"- CV: Terlampir\n\n"
            f"Siap berdiskusi kapan pun dibutuhkan via email ini atau WhatsApp {app.applicant_phone or '-'}.\n\n"
            f"Terima kasih,\n"
            f"{app.applicant_name}"
        )
        return GeneratedMessage(template_type=TemplateType.SINGKAT, subject=subject, body=body)

    @staticmethod
    def generate_kreatif(job: JobPost, app: ApplicationRequest) -> GeneratedMessage:
        subject = f"Siap Membantu {job.company} Bertumbuh sebagai {job.title} 🚀"
        body = (
            f"Halo {job.company},\n\n"
            f"Mencari kandidat {job.title} yang mandiri, adaptif terhadap kultur WFH, dan berorientasi hasil? "
            f"Saya {app.applicant_name}, siap membawa dampak nyata ke dalam tim Anda.\n\n"
            f"Karya dan rekam jejak saya dapat ditinjau langsung di:\n"
            f"👉 Portofolio: {app.portfolio_url or '(Terlampir pada CV)'}\n\n"
            f"Mari berkolaborasi dan wujudkan target kuartal ini bersama. Saya tunggu kabar baiknya!\n\n"
            f"Salam kreatif,\n"
            f"{app.applicant_name}"
        )
        return GeneratedMessage(template_type=TemplateType.KREATIF, subject=subject, body=body)

    @staticmethod
    def generate_follow_up(job: JobPost, app: ApplicationRequest) -> GeneratedMessage:
        subject = f"Follow-up Lamaran: {job.title} - {app.applicant_name}"
        body = (
            f"Yth. Tim Rekrutmen {job.company},\n\n"
            f"Semoga pesan ini menjumpai Anda dalam keadaan baik. Saya {app.applicant_name}, ingin menindaklanjuti "
            f"lamaran yang telah saya kirimkan sebelumnya untuk posisi {job.title}.\n\n"
            f"Saya tetap sangat antusias untuk berkontribusi bagi {job.company}. Mohon informasikan apabila tim "
            f"memerlukan dokumen pendukung tambahan dari pihak saya.\n\n"
            f"Terima kasih banyak atas waktu dan perhatiannya.\n\n"
            f"Hormat saya,\n"
            f"{app.applicant_name}\n"
            f"{app.applicant_email}"
        )
        return GeneratedMessage(template_type=TemplateType.FOLLOW_UP, subject=subject, body=body)
