import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
from typing import List, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import logging

from model.job_model import Job
from normalizations.sector_identifier import SectorID
from normalizations.jobType import JobType
from normalizations.experience import Experience
# Initialize logging
logging.basicConfig(level=logging.INFO)


@dataclass
class JobSector:
    """Data class to store job sector information."""
    name: str
    url: str
    job_list: List['JobModel']


@dataclass
class JobModel:
    """Data class to represent a job listing."""
    expiry: Optional[str] = None
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


def setup_driver() -> webdriver.Chrome:
    """Set up the Selenium WebDriver using a context manager."""
    options = webdriver.ChromeOptions()
    # Uncomment to run in headless mode
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver


def scrape_job_sector(url: str, driver: webdriver.Chrome) -> List[JobSector]:
    """Scrape job sector names and URLs from the given webpage URL."""
    job_sectors = []
    try:
        driver.get(url)
        logging.info(f"Accessing URL: {url}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.catelist"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        sectors = soup.select('ul.catelist li a')

        for sector in sectors:
            name = sector.get_text(strip=True)
            link = sector['href']
            job_sectors.append(JobSector(name=name, url=link, job_list=[]))

        logging.info(f"Scraped {len(job_sectors)} sectors from {url}.")

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return job_sectors


def scrape_job_by_sector(sector: JobSector, driver: webdriver.Chrome) -> None:
    """Scrape job listings from a sector detail page and add them to the sector."""
    try:
        driver.get(sector.url)
        logging.info(f"Accessing sector URL: {sector.url}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.list-ul"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        jobs = soup.select('div.list-li > a')

        for job in jobs:
            title = job.select_one('h2').get_text(strip=True)
            location_info = job.select_one('div.location')
            posted_time = location_info.find_all('span')[0].get_text(strip=True)
            location = location_info.find_all('span')[1].get_text(strip=True)
            content = job.select_one('p').get_text(strip=True)
            job_apply_url = job['href']

            # Scrape detailed job information
            detail = scrape_job_detail(job_apply_url, driver)

            # Append detailed job data to sector
            sector.job_list.append(JobModel(
                title=title,
                location=location,
                content=content,
                posted_time=posted_time,
                job_apply_url=job_apply_url,
                company=detail.company,
                job_type=detail.job_type,
                qualifications=detail.qualifications,
                experience=detail.experience,
                salary=detail.salary,
                skills=detail.skills
            ))

        logging.info(f"Scraped {len(sector.job_list)} jobs from {sector.url}.")

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


def scrape_job_detail(job_url: str, driver: webdriver.Chrome) -> JobModel:
    """Scrape detailed job information from a job detail page."""
    try:
        driver.get(job_url)
        logging.info(f"Accessing job URL: {job_url}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-box"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        company = soup.select_one('div.row.text-muted a').get_text(strip=True) if soup.select_one('div.row.text-muted a') else None
        info_parent = soup.find('div', style=lambda x: x and 'line-height' in x)

        # Extract job details
        job_type = extract_info(info_parent, 'Job Type:')
        qualifications = extract_info(info_parent, 'Education:')
        experience = extract_info(info_parent, 'Experience:')
        salary_elem = info_parent.find(text=lambda x: 'Salary:' in x)
        salary = salary_elem.parent.get_text(strip=True).replace('Salary:', '').strip() if salary_elem else None
        content_elem = soup.select_one('h2 + p')
        content = content_elem.get_text(strip=True) if content_elem else None
        skills = [skill.get_text(strip=True) for skill in soup.select('ul.skillslist li a')] if soup.select('ul.skillslist li a') else []

        # Create JobModel object
        job = JobModel(
            company=company,
            content=content,
            job_type=[job_type] if job_type else None,
            qualifications=[qualifications] if qualifications else None,
            experience=experience,
            salary=salary,
            skills=skills
        )

        logging.info(f"Scraped job details from {job_url}.")
        return job

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return JobModel()


def extract_info(parent, label: str) -> Optional[str]:
    """Extract specific job information from the parent element."""
    elem = parent.find(text=lambda x: label in x)
    return elem.split(label)[-1].strip() if elem else None


def save_jobs_to_csv(all_sectors: List[JobSector]):
    """Save all job data from all sectors to a single CSV file."""
    filename = 'gulf_jobs_all_sectors.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'sector', 'expiry', 'title', 'content', 'location', 'company', 'email',
            'job_sector', 'job_type', 'qualifications', 'field_of_study',
            'career_level', 'job_apply_type', 'experience', 'job_apply_url',
            'posted_time', 'salary', 'skills'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for sector in all_sectors:
            for job in sector.job_list:
                
                # Predict the sector using the saved model
                print('Job title to predict ', job.title)
                predicted_sector = SectorID.findSector(job.title)
            
                # Predict the experience using the saved model
                print('Job Experience and career_level to predict' ,job.experience)
                predicted_career_level,predicted_experience = Experience.getExperience(job.experience)
                
                # Predict the job type using the saved model
                # Check if job_type is a list and predict each type
                predicted_jobType = [
                    JobType.predictJobType(job_type) for job_type in job.job_type
                ] if job.job_type else None

                # Convert list to string for CSV storage
                predicted_jobType_str = ', '.join(predicted_jobType) if predicted_jobType else None

                # Convert list to string for CSV storage

                writer.writerow({
                    'sector': predicted_sector,
                    'expiry': job.expiry,
                    'title': job.title,
                    'content': job.content,
                    'location': job.location,
                    'company': job.company,
                    'email': job.email,
                    'job_sector': ', '.join(job.job_sector) if job.job_sector else None,
                    'job_type': predicted_jobType_str,
                    'qualifications': ', '.join(job.qualifications) if job.qualifications else None,
                    'field_of_study': ', '.join(job.field_of_study) if job.field_of_study else None,
                    'career_level': job.career_level,
                    'job_apply_type': job.job_apply_type,
                    'experience': predicted_experience,
                    'career_level': predicted_career_level,
                    'job_apply_url': job.job_apply_url,
                    'posted_time': job.posted_time,
                    'salary': job.salary,
                    'skills': ', '.join(job.skills) if job.skills else None
                })

    logging.info(f"Saved jobs from all sectors to {filename}.")


def scrape_gulf_jobs(progress_callback=None) -> List[Job]:
    """Scrape job listings from Gulf Job and return a list of job details."""
    all_job_sectors = []
    logging.info("Starting job scraping...")

    driver = setup_driver()
    url = 'https://www.gulfjobs.com/jobs-by-industry'  # Replace with the actual URL

    job_sectors = scrape_job_sector(url, driver)
    all_job_sectors.extend(job_sectors)

    total_sectors = len(all_job_sectors[:1])  # Adjust based on your limit or requirement
    for sector_index, sector in enumerate(all_job_sectors[:1]):
        scrape_job_by_sector(sector, driver)

        # Update the progress bar
        if progress_callback:
            progress = (sector_index + 1) / total_sectors
            progress_callback(progress)

    # save_jobs_to_csv(all_job_sectors)
    driver.quit()

    # Collect job details into the list
    all_job_listings = []
    for sector in all_job_sectors:
        for job in sector.job_list:
          # Predict the sector using the saved model
          print('Job title to predict ', job.title)
          predicted_sector = SectorID.findSector(job.title)
      
          # Predict the experience using the saved model
          print('Job Experience and career_level to predict' ,job.experience)
          predicted_career_level,predicted_experience = Experience.getExperience(job.experience)
          
          # Predict the job type using the saved model
          # Check if job_type is a list and predict each type
          predicted_jobType = [
              JobType.predictJobType(job_type) for job_type in job.job_type
          ] if job.job_type else None

          job_model = Job(
              title=job.title,
              company=job.company,
              location=job.location,
              content=job.content,
              job_sector=predicted_sector,
              experience=predicted_experience,
              career_level=predicted_career_level,
              job_type=predicted_jobType,
              posted_time=job.posted_time,
              expiry=job.expiry,
              job_apply_url=job.job_apply_url
          )
          all_job_listings.append(job_model)

    return all_job_listings


