from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Job:
    """Data class to represent a job listing."""
    title: Optional[str] = None
    content: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    job_sector: Optional[List[str]] = None
    job_type: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    field_of_study: Optional[List[str]] = None
    career_level: Optional[str] = None
    job_apply_type: Optional[str] = None
    experience: Optional[str] = None
    job_apply_url: Optional[str] = None
    posted_time: Optional[str] = None
    salary: Optional[str] = None
    skills: Optional[List[str]] = None
    expiry: Optional[str] = None

