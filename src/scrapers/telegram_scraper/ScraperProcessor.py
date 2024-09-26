import re
import sys
import os
import json
from typing import Union, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from normalizations.sector_identifier import SectorID
from normalizations.jobType import JobType
from normalizations.experience import Experience

import warnings

warnings.filterwarnings("ignore")


class ScraperProcessor:
    symbols_to_remove = "*#"
    url_pattern = r"(https?://[^\s]+)"
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    hashtag_pattern = r"#\w+"
    bullet_pattern = r"•\s*"

    @classmethod
    def remove_none(cls, items):
        if len(items) > 0:
            return [item for item in items if item is not None]

        return items

    @classmethod
    def clean_text(cls, texts: Union[str, List[str]]) -> Union[str, List[str]]:
        if not texts:
            return texts

        if isinstance(texts, str):
            texts = [texts]

        if len(cls.remove_none(texts)) == 0:
            return texts

        cleaned_texts = []

        for text in texts:

            try:
                # Decode Unicode characters
                text = text.encode("utf-8").decode("unicode_escape")
            except UnicodeDecodeError:
                # Handle the error: fallback to the original text or log it
                # print(f"UnicodeDecodeError: Could not decode text: {text}")
                cleaned_texts.append(text)  # Append original text if decoding fails
                continue  # Skip to the next text

            # Keep only English letters, numbers, and common punctuation
            cleaned_text = re.sub(r'[^A-Za-z0-9\s.,;\'"?!-]', "", text)
            # Replace multiple spaces with a single space
            cleaned_text = re.sub(r"\s+", " ", cleaned_text)
            cleaned_text = cleaned_text.strip()
            cleaned_texts.append(cleaned_text)

        # Return a list of cleaned texts
        return cleaned_texts if len(cleaned_texts) > 1 else cleaned_texts

    @classmethod
    def clean_message(cls, message_text):
        cleaned_text = re.sub(cls.hashtag_pattern, "", message_text)
        cleaned_text = re.sub(cls.bullet_pattern, "", cleaned_text)
        cleaned_text = cleaned_text.strip()

        return cls.remove_symbols(cleaned_text)

    @classmethod
    def is_english(cls, text: str) -> bool:
        return not bool(
            re.search(
                r'[^a-zA-Z0-9\s.,!?\'"@#\$%\^&\*\(\)_\+\-=\[\]{};:<>\/\\|`~]', text
            )
        )

    @classmethod
    def get_email(cls, text):
        return re.findall(cls.email_pattern, text)

    @classmethod
    def get_url(cls, text, msg):
        url = re.findall(cls.url_pattern, text)
        if len(url) == 0:
            return cls.get_bot_url(msg)

        return url

    @classmethod
    def get_bot_url(cls, message):
        url = []
        if message.buttons:
            for button_row in message.buttons:
                for button in button_row:
                    if button.url:
                        url.append(button.url)
        return url

    @classmethod
    def remove_symbols(cls, text: str) -> str:
        if text is None:
            return ""

        return text.translate(str.maketrans("", "", cls.symbols_to_remove))

    @classmethod
    def extract_years_range(csl, data: list) -> list:
        patterns = [
            re.compile(r"\d+ to \d+ years"),
            re.compile(r"\d+-\d+ years"),
            re.compile(r"\d+ years"),
            re.compile(r"\d+ year"),
        ]

        results = []

        for item in data:
            for pattern in patterns:
                if match := pattern.search(item):
                    results.append(match.group())
                    break
            if len(results) > 0:
                break

        return " ".join(results)

    @classmethod
    def get_experience(cls, data):
        exp = cls.extract_years_range(data)
        if len(exp) > 0:
            return Experience.getExperience(exp)  # return career_level, experience
        return None, None

    @classmethod
    def job_type_sector(cls, data, title):
        job_type = [job_type for job_type in data[1].split("Job Type: ") if job_type]
        job_type = job_type[0] if len(job_type) >= 1 else ""

        sector = SectorID.findSector(title)
        job_type = JobType.predictJobType(job_type)

        return sector, job_type

    @classmethod
    def concatenate_from_to(
        cls, items: list, start_substring: str, end_substrings: list, is_list=False
    ) -> str:
        start_index = None
        end_index = None
        start_string = None

        for i, item in enumerate(items):
            if start_substring in item.lower() and start_index is None:
                start_index = i
                start_string = item
        if start_index is None:
            return None, None

        for i, item in enumerate(items[start_index:], start=start_index):
            if any(end_substring in item.lower() for end_substring in end_substrings):
                end_index = i
                break

        if start_index is None or end_index is None:
            return None, None

        if is_list:
            return items[start_index + 1 : end_index]

        return " ".join(items[start_index:end_index]), start_string

    @classmethod
    def get_description(cls, data):
        desc, end = cls.concatenate_from_to(
            data,
            "description",
            [
                "requirements:",
                "requirements and skills:",
                "qualifications:",
                "how to apply",
                "____________",
            ],
        )
        desc = desc.replace(end, "") if end else desc
        desc = desc.replace("Description: ", "") if desc else desc
        return cls.clean_text(desc)

    @classmethod
    def get_location(cls, data):
        location = [
            location.replace("Work Location: ", "")
            for location in data
            if "work location" in location.lower()
        ]

        return location[0] if len(location) > 0 else ""

    @classmethod
    def get_company(cls, data):

        company, start = cls.concatenate_from_to(
            data,
            "___________",
            [
                "verified",
                "jobs posted",
            ],
        )

        company = company.replace(start, "") if start else company

        if not company:
            company = [
                company.replace("Private Client", "")
                for company in data
                if "Private Client" in company.lower()
            ]

            company = company[0] if len(company) > 0 else ""

        return company

    @classmethod
    def get_qualification(cls, data):
        qualification = [
            qualification.replace("Education Qualification: ", "")
            for qualification in data
            if "education qualification" in qualification.lower()
        ]

        return qualification[0] if len(qualification) > 0 else ""

    @classmethod
    def get_salary(cls, data):
        salary = [
            salary.replace("Salary/Compensation: ", "")
            for salary in data
            if "salary/compensation" in salary.lower()
        ]

        return salary[0] if len(salary) > 0 else ""

    @classmethod
    def get_deadline(cls, data):
        deadline = [
            deadline.replace("Deadline: ", "")
            for deadline in data
            if "deadline" in deadline.lower()
        ]

        return deadline[0] if len(deadline) > 0 else ""

    @classmethod
    def get_skills(cls, data):
        skills = cls.remove_none(
            cls.concatenate_from_to(
                data,
                "required skills",
                [
                    "how to apply",
                    "____________",
                ],
                True,
            )
        )

        if len(skills) == 0:
            skills = cls.remove_none(
                cls.concatenate_from_to(
                    data,
                    "requirements and skills",
                    [
                        "how to apply",
                        "____________",
                    ],
                    True,
                )
            )

        if len(skills) == 0:
            skills = cls.remove_none(
                cls.concatenate_from_to(
                    data,
                    "requirements:",
                    [
                        "how to apply",
                        "____________",
                    ],
                    True,
                )
            )

        if len(skills) == 0:
            skills = cls.remove_none(
                cls.concatenate_from_to(
                    data,
                    "job requirements:",
                    [
                        "how to apply",
                        "____________",
                    ],
                    True,
                )
            )

            # print(skills)

        return cls.clean_text(skills)

    @classmethod
    def to_dictionary(cls, dataclass_obj):
        return {key: value for key, value in dataclass_obj.__dict__.items()}

    @classmethod
    def to_json(cls, jobs):
        jobs_dict = [cls.to_dictionary(user) for user in jobs]

        return json.dumps(jobs_dict, indent=4)

    @classmethod
    def get_apply_type(cls, email, url):
        if email and url:
            return "Both"
        elif email:
            return "Email"

        return "External"
