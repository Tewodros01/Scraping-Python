import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from telethon.sync import TelegramClient
from datetime import datetime, timedelta
from scrapers.telegram_scraper.ScraperProcessor import ScraperProcessor as pr
from scrapers.telegram_scraper.file_manager import FileManager as fm
from model.job_model import Job



class Scrapper:
    api_id = 10467750
    api_hash = "762fa8c3c5cce64e383769e9692bdb07"
    groups = ["kebenajobs", "freelance_ethio"]
    phone = "+251948613528"

    yesterday = datetime.now() - timedelta(days=1)

    json_job_data = []

    @classmethod
    def get_jobs(cls, group):
        with TelegramClient(cls.phone, cls.api_id, cls.api_hash) as client:
            for msg in client.iter_messages(
                entity=group, offset_date=cls.yesterday, reverse=True
            ):
                if msg.text:
                    data = pr.clean_message(msg.text)
                    lines = list(filter(None, data.splitlines()))
                    title = [title for title in lines[0].split("Job Title: ") if title]
                    job_title = title[0] if len(title) >= 1 else ""

                    if pr.is_english(job_title):
                        sector, job_type = pr.job_type_sector(lines, job_title)
                        career_level, exp = pr.get_experience(lines)
                        email = pr.get_email(data)
                        url = pr.get_url(data, msg)

                        cls.json_job_data.append(
                            Job(
                                title=job_title,
                                content=pr.get_description(lines),
                                location=pr.get_location(lines),
                                email=email,
                                company=pr.get_company(lines),
                                job_sector=[sector],
                                job_type=[job_type],
                                qualifications=[pr.get_qualification(lines)],
                                field_of_study=None,
                                career_level=career_level,
                                job_apply_type=pr.get_apply_type(email, url),
                                experience=exp,
                                job_apply_url=url,
                                posted_time=datetime.today().strftime("%Y-%m-%d"),
                                salary=pr.get_salary(lines),
                                skills=pr.get_skills(lines),
                                expiry=pr.get_deadline(lines),
                            )
                        )

        # fm.save_file(pr.to_json(cls.json_job_data))
        print(pr.to_json(cls.json_job_data))
        return cls.json_job_data
