import os
import json
from datetime import datetime
from typing import Optional, List
from ..core.models import JobPost


class GitStorageService:
    def __init__(self, base_data_dir: Optional[str] = None):
        if base_data_dir:
            self.data_dir = base_data_dir
        else:
            self.data_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "jobs"
            )
        os.makedirs(self.data_dir, exist_ok=True)

    def save_job(self, job: JobPost) -> str:
        date_folder = job.posted_at.strftime("%Y-%m-%d")
        target_dir = os.path.join(self.data_dir, date_folder)
        os.makedirs(target_dir, exist_ok=True)

        filename = f"{job.id}.json"
        target_path = os.path.join(target_dir, filename)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(job.model_dump_json(indent=2))

        return target_path

    def load_job(self, file_path: str) -> Optional[JobPost]:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return JobPost.model_validate(data)

    def list_jobs(self, date_str: Optional[str] = None) -> List[str]:
        if date_str:
            target_dir = os.path.join(self.data_dir, date_str)
            if not os.path.isdir(target_dir):
                return []
            return [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(".json")]

        all_files = []
        for root, _, files in os.walk(self.data_dir):
            for f in files:
                if f.endswith(".json"):
                    all_files.append(os.path.join(root, f))
        return sorted(all_files)


git_storage_service = GitStorageService()
