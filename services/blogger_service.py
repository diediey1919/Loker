import html
from typing import Dict, Any, Optional
import requests
from ..config.settings import settings
from ..core.models import JobPost


class BloggerService:
    def __init__(
        self,
        blog_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.blog_id = blog_id or settings.BLOGGER_BLOG_ID
        self.client_id = client_id or settings.BLOGGER_CLIENT_ID
        self.client_secret = client_secret or settings.BLOGGER_CLIENT_SECRET
        self.base_url = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts" if self.blog_id else ""

    def is_configured(self) -> bool:
        return bool(self.blog_id and self.client_id and self.client_secret)

    def render_job_html(self, job: JobPost) -> str:
        req_items = "".join([f"<li>{html.escape(r)}</li>" for r in job.requirements])
        if not req_items:
            req_items = "<li>Lihat detail deskripsi</li>"

        flyer_img_tag = ""
        if job.flyer_image_url:
            flyer_img_tag = f'<div style="text-align:center;margin-bottom:20px;"><img src="{html.escape(job.flyer_image_url)}" alt="{html.escape(job.title)}" style="max-width:100%;border-radius:8px;"/></div>'

        content = f"""
<div class="loker-post-container" style="font-family:sans-serif;line-height:1.6;color:#333;">
  {flyer_img_tag}
  <h2 style="color:#1a73e8;margin-bottom:8px;">{html.escape(job.title)}</h2>
  <p><strong>Perusahaan:</strong> {html.escape(job.company or '-')}</p>
  <p><strong>Kategori:</strong> <span style="background:#e8f0fe;color:#1967d2;padding:3px 8px;border-radius:4px;">{html.escape(job.category.value)}</span></p>
  <p><strong>Tipe Kerja:</strong> {"Remote / WFH" if job.is_remote else "On-site"}</p>
  <p><strong>Estimasi Gaji:</strong> {html.escape(job.salary_range or 'Kompetitif / Sesuai Pengalaman')}</p>
  
  <hr style="border:0;border-top:1px solid #eee;margin:16px 0;"/>
  
  <h3 style="color:#202124;">Deskripsi Pekerjaan:</h3>
  <p>{html.escape(job.description)}</p>
  
  <h3 style="color:#202124;">Kualifikasi & Persyaratan:</h3>
  <ul>
    {req_items}
  </ul>

  <div style="margin-top:24px;padding:16px;background:#f8f9fa;border-radius:8px;border:1px solid #dadce0;">
    <h4 style="margin-top:0;">Cara Melamar:</h4>
    <p>Gunakan fitur Quick Apply di platform Loker untuk mengenerate surat lamaran profesional dan kirim CV otomatis.</p>
  </div>
</div>
        """
        return content.strip()

    def create_post_payload(self, job: JobPost) -> Dict[str, Any]:
        return {
            "kind": "blogger#post",
            "blog": {"id": self.blog_id},
            "title": f"[Lowongan Remote] {job.title} - {job.company}",
            "content": self.render_job_html(job),
            "labels": [job.category.value, "Remote", "WFH", "Lowongan Kerja"] + job.tags
        }

    def publish_post(self, job: JobPost, access_token: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "Blogger configuration is incomplete."
            }

        url = self.base_url
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = self.create_post_payload(job)

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            res.raise_for_status()
            return {
                "success": True,
                "post_data": res.json()
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }


blogger_service = BloggerService()
