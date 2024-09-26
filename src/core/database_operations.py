from flask_sqlalchemy import SQLAlchemy
from fuzzywuzzy import fuzz
from dataclasses import asdict
from typing import Optional, List

# Initialize SQLAlchemy
db = SQLAlchemy()

# Updated SQLAlchemy Job model
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    job_sector = db.Column(db.Text, nullable=True)  # Storing as text for list representation
    job_type = db.Column(db.Text, nullable=True)  # Storing as text for list representation
    qualifications = db.Column(db.Text, nullable=True)  # Storing as text for list representation
    field_of_study = db.Column(db.Text, nullable=True)  # Storing as text for list representation
    career_level = db.Column(db.String(100), nullable=True)
    job_apply_type = db.Column(db.String(100), nullable=True)
    experience = db.Column(db.String(100), nullable=True)
    job_apply_url = db.Column(db.String(200), nullable=True)
    posted_time = db.Column(db.String(100), nullable=True)
    salary = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.Text, nullable=True)  # Storing as text for list representation
    expiry = db.Column(db.String(100), nullable=True)

# Updated function to save a job dataclass instance to the database
def save_job_to_db(job_info):
    """
    Save a job to the database using the provided job_info dataclass.
    """
    job_dict = asdict(job_info)  # Convert dataclass to dictionary
    job_dict['job_sector'] = ', '.join(job_info.job_sector) if job_info.job_sector else None
    job_dict['job_type'] = ', '.join(job_info.job_type) if job_info.job_type else None
    job_dict['qualifications'] = ', '.join(job_info.qualifications) if job_info.qualifications else None
    job_dict['field_of_study'] = ', '.join(job_info.field_of_study) if job_info.field_of_study else None
    job_dict['skills'] = ', '.join(job_info.skills) if job_info.skills else None

    # Remove 'id' from the dictionary to prevent conflicts with auto-increment
    job_dict.pop('id', None)
    
    # Create Job instance
    job = Job(**job_dict)
    
    # Save job to the database
    db.session.add(job)
    db.session.commit()
    print(f"Job '{job.title}' at '{job.company}' saved to database")

# Updated function to check if a job exists in the database based on certain criteria
def job_exists(job_info, threshold=90):
    def normalize_value(value):
        return value.strip().lower() if value else ''

    # Normalize job info values
    normalized_title = normalize_value(job_info.title)
    normalized_content = normalize_value(job_info.content)
    normalized_company = normalize_value(job_info.company)
    normalized_posted_time = normalize_value(job_info.posted_time)
    normalized_expiry = normalize_value(job_info.expiry)

    # Query existing jobs from the database
    existing_jobs = db.session.query(Job).all()

    # Compare each job in the database with the provided job info
    for job in existing_jobs:
        title_match = fuzz.ratio(normalized_title, normalize_value(job.title))
        content_match = fuzz.ratio(normalized_content, normalize_value(job.content))
        company_match = fuzz.ratio(normalized_company, normalize_value(job.company))
        posted_time_match = fuzz.ratio(normalized_posted_time, normalize_value(job.posted_time))
        expiry_match = fuzz.ratio(normalized_expiry, normalize_value(job.expiry))

        if title_match >= threshold and content_match >= threshold and company_match >= threshold and posted_time_match >= threshold and expiry_match >= threshold:
            return True

    return False
