from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import logging
import csv
from typing import List
from model.job_model import Job  # Assuming JobModel is the dataclass you defined for the job structure

from model.job_model import Job
from normalizations.sector_identifier import SectorID
from normalizations.jobType import JobType
from normalizations.experience import Experience

# Initialize logging
logging.basicConfig(level=logging.INFO)

def setup_driver() -> webdriver.Chrome:
    """Set up the Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-gpu")
    # Uncomment the line below to run headless
    options.add_argument('--headless') 
    driver = webdriver.Chrome(options=options)
    return driver

@dataclass
class JobDetail:
    """Data class to represent detailed job information."""
    qualifications: str = ""  
    responsibilities: str = ""
    experience: str = ""
    work_from: str = ""
    description: str = ""

@dataclass
class JobListing:
    """Data class to represent a job listing."""
    title: str
    company: str
    location: str
    job_type: str
    posted_time: str
    salary: str
    job_link: str
    qualifications: str = ""  
    responsibilities: str = ""
    experience: str = ""
    work_from: str = ""
    description: str = ""

def scrape_job_detail_in_new_tab(job_url: str, driver: webdriver.Chrome) -> JobDetail:
    """Scrape detailed job information from a job detail page in a new tab."""
    original_window = driver.current_window_handle
    driver.execute_script("window.open('');")
    new_window = [window for window in driver.window_handles if window != original_window][0]
    driver.switch_to.window(new_window)

    try:
        driver.get(job_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "offerBody")))
        logging.info(f"Scraping details for job: {job_url}")

        # Scrape details
        qualifications = driver.find_element(By.XPATH, "//div[@class='leading-5']").text.strip()
        responsibilities = ' '.join([li.text.strip() for li in driver.find_elements(By.XPATH, "//ul[@class='list-disc ps-4']/li")])
        experience = driver.find_element(By.XPATH, "//span[contains(text(),'Experience')]/following-sibling::div//span").text.strip()
        work_from = driver.find_element(By.XPATH, "//div[contains(@class, 'offer_info')]//div[contains(@class, 'text-start')]").text.strip()
        description = driver.find_element(By.CSS_SELECTOR, "div#offerDescription").text.strip()

        return JobDetail(qualifications, responsibilities, experience, work_from, description)

    except Exception as e:
        logging.error(f"Error scraping job details for {job_url}: {e}")
        return JobDetail()

    finally:
        driver.close()
        driver.switch_to.window(original_window)

def scrape_current_page_jobs(driver: webdriver.Chrome) -> List[JobListing]:
    """Scrape job listings currently displayed on the page."""
    job_listings = []
    try:
        job_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.box-shadow.hover\\:box-shadow-lg.text-primary"))
        )

        for job in job_elements:
            try:
                job_link_element = job.find_element(By.CSS_SELECTOR, "a[title]")
                job_link = job_link_element.get_attribute("href")
                title = job_link_element.get_attribute("title").strip()

                company = job.find_element(By.CSS_SELECTOR, "div[id='offer-header'] img").get_attribute("alt").replace("Logo for ", "").strip()
                posted_time = job.find_element(By.CSS_SELECTOR, "span.text-dark-gray").text.strip()
                job_type = job.find_element(By.XPATH, ".//li[1]/span").text.strip()
                salary = job.find_elements(By.XPATH, ".//li[2]")[0].text.strip() if job.find_elements(By.XPATH, ".//li[2]") else 'N/A'
                location = job.find_element(By.XPATH, ".//li[contains(@class, 'location_icons_container')]//span").text.strip()

                # Scrape detailed job information in a new tab
                detail = scrape_job_detail_in_new_tab(job_link, driver)
                
                job_listing = JobListing(
                    title=title, company=company, location=location, job_type=job_type, 
                    posted_time=posted_time, salary=salary, job_link=job_link,
                    qualifications=detail.qualifications, responsibilities=detail.responsibilities, 
                    experience=detail.experience, work_from=detail.work_from, description=detail.description
                )
                job_listings.append(job_listing)
                logging.info(f"Scraped Job: {title} at {company}")

            except StaleElementReferenceException:
                logging.warning("Stale element reference. Re-locating elements.")
                continue
            except Exception as e:
                logging.error(f"Error extracting job details: {e}")

    except Exception as e:
        logging.error(f"An error occurred while scraping jobs on the current page: {e}")

    return job_listings

def scrape_jobs(driver: webdriver.Chrome, url: str) -> List[JobListing]:
    """Scrape job listings from the given URL."""
    job_listings = []
    try:
       driver.get(url)
       logging.info(f"Accessing URL: {url}")

       job_listings.extend(scrape_current_page_jobs(driver))

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load on {url}: {e}")
    except Exception as e:
        logging.error(f"An error occurred on {url}: {e}")

    # Remove duplicates by converting to a set of tuples and back to a list of JobListing
    job_listings = list({(job.title, job.company, job.location, job.job_type, job.posted_time, job.salary, job.job_link): job for job in job_listings}.values())

    return job_listings

def save_jobs_to_csv(job_listings: List[JobListing]):
    """Save all job data to a single CSV file."""
    filename = 'jobgether_jobs_all_jobs.csv'
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Company', 'Location', 'Job Type', 'Posted Time', 'Salary', 'Job Link', 'Qualifications', 'Responsibilities', 'Experience', 'Work From', 'Description'])
        for job in job_listings:
            writer.writerow([job.title, job.company, job.location, job.job_type, job.posted_time, job.salary, job.job_link, job.qualifications, job.responsibilities, job.experience, job.work_from, job.description])
    logging.info(f"Saved {len(job_listings)} jobs to {filename}")


def scrape_jobgether_jobs(progress_callback=None) -> List[Job]:
    """Scrape job listings from Jobgether and return a list of JobModel instances."""
    job_listings = []
    try:
        # Set up WebDriver
        driver = setup_driver()

        # List of URLs to scrape
        urls = [
            "https://jobgether.com/remote-jobs/development",
            "https://jobgether.com/remote-jobs/sales"
        ]

        total_urls = len(urls)
        for url_index, url in enumerate(urls):
            # Scrape jobs from the current URL
            scraped_jobs = scrape_jobs(driver, url)

            # Convert scraped JobListing to JobModel
            for job in scraped_jobs:
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
                job_model = Job(
                    title=job.title,
                    company=job.company,
                    job_type=predicted_jobType,
                    location=job.location,
                    content=job.description,
                    job_apply_url=job.job_link,
                    job_sector=predicted_sector,
                    experience=predicted_experience,
                    career_level=predicted_career_level,
                    posted_time=job.posted_time,
                    salary=job.salary,
                    qualifications=[job.qualifications] if job.qualifications else None,
                    skills=[job.responsibilities] if job.responsibilities else None,
                )
                job_listings.append(job_model)

            # Update the progress bar
            if progress_callback:
                progress = (url_index + 1) / total_urls
                progress_callback(progress)

        # Save job listings to a CSV file (optional, can be commented if not needed)
        save_jobs_to_csv(scraped_jobs)

        # Close the WebDriver
        driver.quit()

    except Exception as e:
        logging.error(f"An error occurred while scraping jobs: {e}")

    return job_listings


if __name__ == "__main__":
    # Scrape job listings with a progress callback
    job_listings = scrape_jobgether_jobs(progress_callback=lambda p: logging.info(f"Progress: {p * 100:.2f}%"))

    # Save job listings to a CSV file
    save_jobs_to_csv(job_listings)

    # Print the scraped job listings
    for job in job_listings:
        print(f"Title: {job.title}, Company: {job.company}, Location: {job.location}, Description: {job.description}")
