import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
from model.job_model import Job
from typing import List

# Your bot token and channel ID
BOT_TOKEN = '7885001915:AAFIetBMBBy59qPuXxXUxii75Ph8BC6iXf4'
CHANNEL_ID = '-1001703052454'

def send_job_listings_to_channel(job_list: List[Job]):
    # Function to format a single job listing in a professional way
    def format_job(job: Job) -> str:
        formatted_job = f"<b>Job Title:</b> {job.title or 'N/A'}\n"
        formatted_job += f"<b>Company:</b> {job.company or 'N/A'}\n"
        formatted_job += f"<b>Location:</b> {job.location or 'N/A'}\n"
        formatted_job += f"<b>Sector:</b> {', '.join(job.job_sector) if job.job_sector else 'N/A'}\n"
        formatted_job += f"<b>Job Type:</b> {', '.join(job.job_type) if job.job_type else 'N/A'}\n"
        formatted_job += f"<b>Qualifications:</b> {', '.join(job.qualifications) if job.qualifications else 'N/A'}\n"
        formatted_job += f"<b>Experience:</b> {job.experience or 'N/A'}\n"
        formatted_job += f"<b>Career Level:</b> {job.career_level or 'N/A'}\n"
        formatted_job += f"<b>Skills:</b> {', '.join(job.skills) if job.skills else 'N/A'}\n"
        formatted_job += f"<b>Salary:</b> {job.salary or 'N/A'}\n"
        formatted_job += f"<b>Posted On:</b> {job.posted_time or 'N/A'}\n"
        formatted_job += f"<b>Expiry Date:</b> {job.expiry or 'N/A'}\n"
        formatted_job += f"<b>Apply Here:</b> <a href='{job.job_apply_url or '#'}'>Application Link</a>\n"
        if job.email:
            formatted_job += f"<b>Contact Email:</b> {job.email}\n"
        if job.content:
            formatted_job += f"<b>Job Description:</b> {job.content}\n"
        return formatted_job

    # Loop through each job and send it as a message
    for job in job_list:
        message = format_job(job)
        send_message_to_channel(message)

def send_message_to_channel(message: str):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    params = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'HTML'  # Allows HTML formatting in the message
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print("Failed to send message:", response.text)

# Example usage with sample data
if __name__ == "__main__":
    sample_jobs = [
        Job(
            title="Software Engineer",
            content="Develop software applications in Python and JavaScript.",
            location="Addis Ababa",
            company="Tech Corp",
            email="contact@techcorp.com",
            job_sector=["Engineering", "Technology"],
            job_type=["Full-time"],
            qualifications=["Bachelor's Degree"],
            field_of_study=["Computer Science"],
            career_level="Mid-level",
            job_apply_type="External",
            experience="2+ Years",
            job_apply_url="https://example.com/apply",
            posted_time="2024-09-26",
            salary="Competitive",
            skills=["Python", "JavaScript", "Django"],
            expiry="2024-10-15"
        ),
        Job(
            title="Project Manager",
            content="Oversee project operations and ensure timely delivery.",
            location="Remote",
            company="Global Projects Ltd.",
            job_sector=["Management"],
            job_type=["Contract"],
            qualifications=["Bachelor's Degree", "PMP Certification"],
            career_level="Senior",
            experience="5+ Years",
            job_apply_url="https://example.com/apply",
            posted_time="2024-09-26",
            salary="Monthly",
            skills=["Project Management", "Leadership"],
            expiry="2024-10-10"
        )
    ]

    send_job_listings_to_channel(sample_jobs)
