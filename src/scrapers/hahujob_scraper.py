import sys
import os
import csv
from typing import List, Optional, Dict
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import time

from datetime import datetime

from normalizations.sector_identifier import SectorID
from normalizations.jobType import JobType
from normalizations.experience import Experience
from model.job_model import Job
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
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    application_deadline: Optional[str] = None
    description: Optional[str] = None
    positions: Optional[str] = None
    apply_url: Optional[str] = None

def setup_driver() -> webdriver.Chrome:
    """Set up the Selenium WebDriver using a context manager."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-gpu")
    # Uncomment the following line to run in headless mode (without opening a browser window)
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_job_sector(url: str, driver: webdriver.Chrome) -> List[JobSector]:
    """Scrape job sector names and URLs from the given webpage URL."""
    job_sectors = []
    try:
        driver.get(url)
        logging.info(f"Accessing URL: {url}")

        time.sleep(5)  # Allow the page to load

        # Scrape the desired data
        sectors = driver.find_elements(By.CSS_SELECTOR, 'section#sectors div.grid > div')

        for sector in sectors:
            try:
                link_element = sector.find_element(By.TAG_NAME, 'a')
                title_element = sector.find_element(By.CSS_SELECTOR, 'div.text-center > p.font-body')
                open_positions_element = sector.find_element(By.CSS_SELECTOR, 'div.text-secondary > p')

                title = title_element.text.strip()
                open_positions = open_positions_element.text.strip()
                link = link_element.get_attribute('href').strip()

                logging.info(f"Sector: {title}, Open Positions: {open_positions}, Link: {link}")

                job_sectors.append(JobSector(name=title, url=link, job_list=[]))
            except Exception as e:
                logging.error(f"Error extracting sector details: {e}")

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
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.grid.grid-cols-1 > div"))
        )

        # Scrape the desired data
        jobs = driver.find_elements(By.CSS_SELECTOR, 'div.grid.grid-cols-1 > div')

        for job_index, job in enumerate(jobs):
            try:
                title_element = job.find_element(By.CSS_SELECTOR, 'div.text-center.md\\:text-start > h3')
                company_element = job.find_element(By.CSS_SELECTOR, 'div.flex.flex-col.items-center.justify-start > p')
                location_element = job.find_element(By.XPATH, ".//div[contains(@title, 'Location')]/p")
                experience_element = job.find_element(By.XPATH, ".//div[contains(@title, 'Years of Experience')]/p")
                type_element = job.find_element(By.XPATH, ".//div[contains(@title, 'Job Type')]/p")
                positions_element = job.find_element(By.XPATH, ".//div[contains(@title, 'Number of Positions')]/p")

                title = title_element.text.strip()
                company = company_element.text.strip()
                location = location_element.text.strip()
                experience = experience_element.text.strip()
                job_type = type_element.text.strip()
                positions = positions_element.text.strip()

                # Scrape detailed job information with the job's index
                detail = scrape_job_detail(sector.url, job_index)
                logging.info(f"Job detail: {detail}")

                # Append detailed job data to sector
                sector.job_list.append(JobModel(
                    title=title,
                    location=location,
                    posted_date=detail.posted_date, 
                    positions=positions,
                    apply_url=detail.apply_url,
                    company=company,
                    job_type=job_type,
                    experience=experience,
                    application_deadline=detail.application_deadline,
                    description=detail.description,
                ))

            except Exception as e:
                logging.error(f"Error extracting job details: {e}")

        logging.info(f"Scraped {len(sector.job_list)} jobs from {sector.url}.")

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
    except Exception as e:
        logging.error(f"An error occurred while scraping sector URL {sector.url}: {e}")
    finally:
        logging.info(f"Finished processing sector URL: {sector.url}")

def scrape_job_detail(sector_url: str, job_index: int) -> JobModel:
    """Scrape detailed job information from a job detail page by clicking the job card."""
    driver = setup_driver()
    try:
        driver.get(sector_url)
        logging.info(f"Accessing sector URL: {sector_url} for job detail scraping")

        # Wait until the list of jobs is visible
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.grid.grid-cols-1 > div"))
        )

        # Find the job card by index and click on it to open job details
        jobs = driver.find_elements(By.CSS_SELECTOR, 'div.grid.grid-cols-1 > div')
        if len(jobs) <= job_index:
            logging.error(f"Job index {job_index} is out of range. Only found {len(jobs)} jobs.")
            return JobModel()
        
        job = jobs[job_index]
        driver.execute_script("arguments[0].scrollIntoView(true);", job)

        try:
            # Click the 'Read More' button to view job details
            read_more_button = job.find_element(By.XPATH, ".//button[contains(., 'Read More')]")
            driver.execute_script("arguments[0].click();", read_more_button)
            logging.info(f"Clicked 'Read More' for job index {job_index}")
        except Exception as e:
            logging.error(f"Error clicking 'Read More' button: {e}")
            driver.save_screenshot('read_more_error.png')
            return JobModel()

        # Take a screenshot after clicking 'Read More'
        driver.save_screenshot('after_read_more_click.png')

        # Wait for the entire job detail section to load
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.relative.bg-secondary-8"))
        )

        # Wait for all elements of the job detail page to load
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.mt-2.pt-4"))
        )

        # Initialize job detail fields
        company = None
        experience = None
        job_type = None
        application_deadline = None
        description = None

        # Extract job details using more specific and verified selectors
        try:
            company_elem = driver.find_element(By.CSS_SELECTOR, "p.text-secondary-6")
            company = company_elem.text.strip()
            logging.info(f"Extracted company: {company}")
        except Exception as e:
            logging.error(f"Error extracting company: {e}")

        try:
            experience_elem = driver.find_element(By.XPATH, ".//div[@title='Years of Experience']//p")
            experience = experience_elem.text.strip()
            logging.info(f"Extracted experience: {experience}")
        except Exception as e:
            logging.error(f"Error extracting experience: {e}")

        try:
            job_type_elem = driver.find_element(By.XPATH, ".//div[@title='Job Type']//p")
            job_type = job_type_elem.text.strip()
            logging.info(f"Extracted job type: {job_type}")
        except Exception as e:
            logging.error(f"Error extracting job type: {e}")

        try:
            application_deadline_elem = driver.find_element(By.XPATH, ".//p[@title='Expiration Date']")
            application_deadline = application_deadline_elem.text.strip()
            logging.info(f"Extracted application deadline: {application_deadline}")
        except Exception as e:
            logging.error(f"Error extracting application deadline: {e}")
        try:
            posted_date_element = driver.find_element(By.XPATH, ".//p[@title='Posted Date']")
            posted_date = posted_date_element.text.strip()
            logging.info(f"Extracted posted date: {posted_date}")
        except Exception as e:
            logging.error(f"Error extracting posted date: {e}")
        # Wait for the job description element to be present and visible
        try:
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#job_description"))
            )
            description_elem = driver.find_element(By.CSS_SELECTOR, "#job_description")
            description = description_elem.text.strip()
            logging.info(f"Extracted job description.")
        except Exception as e:
            logging.error(f"Error extracting job description: {e}")

        # Create JobModel object
        job = JobModel(
            company=company,
            experience=experience,
            job_type=job_type,
            application_deadline=application_deadline,
            description=description,
            posted_date=posted_date,
            apply_url=driver.current_url  # The current URL after clicking the "Read More"
        )

        logging.info(f"Scraped job details successfully for job index {job_index}.")
        return job

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
        driver.save_screenshot('timeout_error.png')
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        driver.quit()

    return JobModel()

def save_jobs_to_csv(all_sectors: List[JobSector]):
    """Save all job data from all sectors to a single CSV file."""
    filename = 'hahu_jobs_all_sectors.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'sector', 'title', 'positions', 'company', 'location', 'experience',
            'job_type', 'posted_date', 'application_deadline', 'description', 'apply_url'
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

                writer.writerow({
                    'sector': predicted_sector,
                    'title': job.title,
                    'positions': job.positions,  # Ensure 'positions' is included in fieldnames
                    'company': job.company,
                    'location': job.location,
                    'experience': predicted_experience,
                    'career_levl':predicted_career_level,
                    'job_type': predicted_jobType_str,
                    'posted_date': job.posted_date,
                    'application_deadline': job.application_deadline,
                    'description': job.description,
                    'apply_url': job.apply_url
                })

    logging.info(f"Saved jobs from all sectors to {filename}.")

def scrape_hahu_jobs(progress_callback=None) -> List[Job]:
    """
    Scrapes job listings from Hahu Job, saves them to a CSV file, and returns a list of job details.
    
    Args:
        progress_callback (function): A callback function to update the progress bar.
        
    Returns:
        list: A list of dictionaries containing job details.
    """
    all_job_sectors = []
    logging.info("Starting job scraping...")

    # Set up the Selenium WebDriver
    driver = setup_driver()
    url = 'https://hahu.jobs'  

    # Scrape job sectors
    job_sectors = scrape_job_sector(url, driver)
    all_job_sectors.extend(job_sectors)

    # Limiting to the first 1 sector for testing; remove the limit for full scraping
    total_sectors = len(all_job_sectors[:4])
    for sector_index, sector in enumerate(all_job_sectors[:4]):
        scrape_job_by_sector(sector, driver)
        
        # Update the progress bar
        if progress_callback:
            progress = (sector_index + 1) / total_sectors
            progress_callback(progress)

    # Close the WebDriver after scraping is complete
    driver.quit()
    
     # Collect job details into the list
    all_job_listings = []
    current_date = datetime.now().date()

    for sector in all_job_sectors:
        for job in sector.job_list:
            # Convert the posted_date from string to datetime object
            job_posted_date = datetime.strptime(job.posted_date, '%d/%m/%Y').date()
            
            # Check if the job posted date is today or in the future
            if job_posted_date >= current_date:
                job_model = Job(
                    title=job.title,
                    company=job.company,
                    job_type=job.job_type,
                    location=job.location,
                    content=job.description,
                    experience=job.experience,
                    posted_time=job.posted_date,
                    expiry=job.application_deadline,
                    job_apply_url=job.apply_url
                )
                all_job_listings.append(job_model)
    # Save the scraped job data to a CSV file
    # save_jobs_to_csv(all_job_sectors)
    
    return all_job_listings


