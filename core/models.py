from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class JobCategory(str, Enum):
    IT = "IT"
    DESAIN = "Desain"
    ADMIN = "Admin"
    PENULISAN = "Penulisan"
    LAINNYA = "Lainnya"


class TemplateType(str, Enum):
    FORMAL = "formal"
    SANTAI = "santai"
    SINGKAT = "singkat"
    KREATIF = "kreatif"
    FOLLOW_UP = "follow_up"


class UserTier(str, Enum):
    FREE = "free"
    PRO_LIFETIME = "pro_lifetime"


class JobPost(BaseModel):
    id: str
    title: str
    company: Optional[str] = "Penyedia Lowongan"
    category: JobCategory = JobCategory.LAINNYA
    tags: List[str] = Field(default_factory=list)
    description: str
    requirements: List[str] = Field(default_factory=list)
    contact_email: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_url: Optional[str] = None
    salary_range: Optional[str] = None
    is_remote: bool = True
    source_platform: str = "Instagram"
    source_post_id: str
    source_url: Optional[str] = None
    flyer_image_url: Optional[str] = None
    raw_ocr_text: Optional[str] = None
    posted_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_repost: bool = False
    is_active: bool = True


class GeneratedMessage(BaseModel):
    template_type: TemplateType
    subject: str
    body: str


class ApplicationRequest(BaseModel):
    applicant_name: str
    applicant_email: str
    applicant_phone: Optional[str] = None
    portfolio_url: Optional[str] = None
    target_job_id: str
    template_type: TemplateType = TemplateType.FORMAL
    cv_filename: str
    cv_temp_path: str
    apply_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ApplicationResult(BaseModel):
    success: bool
    job_id: str
    applicant_email: str
    template_used: TemplateType
    dispatch_channel: str
    message_content: str
    dispatched_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class MidtransTransactionPayload(BaseModel):
    order_id: str
    gross_amount: int = 49000
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
