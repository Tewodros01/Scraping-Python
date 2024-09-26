import sys
import os

# Append 'src' directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
from model.job_model import Job
from typing import List
from normalizations.sector_identifier import SectorID
from normalizations.jobType import JobType
from normalizations.experience import Experience

# Set the maximum retries for HTTP requests
MAX_RETRIES = 3
INITIAL_BACKOFF_DELAY = 1  # Initial backoff delay of 1 second
BASE_URL = "https://www.bayt.com/en/"


# Job and SubSector class definitions
class JobListing:
    def __init__(self, job_title=None, job_description=None, company_name=None, location=None,
                 experience=None, posting_date=None, easyApply=None, jobLocation=None,
                 job_type=None, companyIndustry=None, jobRole=None, employmentType=None,
                 monthlySalaryRange=None, numberOfVacancies=None, skillsRequired=None,
                 detailUrl=None):
        self.job_title = job_title
        self.job_description = job_description
        self.company_name = company_name
        self.location = location
        self.experience = experience
        self.posting_date = posting_date
        self.easyApply = easyApply
        self.jobLocation = jobLocation
        self.job_type = job_type
        self.companyIndustry = companyIndustry
        self.jobRole = jobRole
        self.employmentType = employmentType
        self.monthlySalaryRange = monthlySalaryRange
        self.numberOfVacancies = numberOfVacancies
        self.skillsRequired = skillsRequired
        self.detailUrl = detailUrl

def setup_driver() -> webdriver.Chrome:
    """Set up the Selenium WebDriver using a context manager."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-gpu")
    # Uncomment the following line to run in headless mode (without opening a browser window)
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)   
    return driver

# Function to handle HTTP errors
def handle_http_error(error, retries):
    """Handle HTTP errors and retry the request if needed."""
    if isinstance(error, requests.exceptions.RequestException):
        if error.response and error.response.status_code == 429 and retries < MAX_RETRIES:
            backoff_delay = (2 ** retries) * INITIAL_BACKOFF_DELAY
            print(f"Rate limited. Retrying in {backoff_delay} seconds...")
            time.sleep(backoff_delay)
            return True
        elif error.response and error.response.status_code == 404:
            print("404 Not Found Error:", error)
            return False
        else:
            raise error
    return False

# Function to scrape job details from the detail page
def scrape_job_detail(jobDetailUrl, retries=0):
    try:
        response = requests.get(jobDetailUrl)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # Use ':-soup-contains' instead of ':contains'
        return JobListing(
            job_description=soup.select_one("h2.h5:-soup-contains('Job Description')").find_next("div").text.strip() if soup.select_one("h2.h5:-soup-contains('Job Description')") else None,
            skillsRequired=soup.select_one("h2.h5:-soup-contains('Skills')").find_next("div").text.strip() if soup.select_one("h2.h5:-soup-contains('Skills')") else None,
            companyIndustry=soup.select_one("dt:-soup-contains('Company Industry')").find_next("dd").text.strip() if soup.select_one("dt:-soup-contains('Company Industry')") else None,
            employmentType=soup.select_one("dt:-soup-contains('Employment Type')").find_next("dd").text.strip() if soup.select_one("dt:-soup-contains('Employment Type')") else None,
            numberOfVacancies=soup.select_one("dt:-soup-contains('Number of Vacancies')").find_next("dd").text.strip() if soup.select_one("dt:-soup-contains('Number of Vacancies')") else None,
            monthlySalaryRange=soup.select_one(".icon.is-salaries + b").text.strip() if soup.select_one(".icon.is-salaries + b") else None,
            detailUrl=jobDetailUrl,
            job_type=soup.select_one("dt:-soup-contains('Employment Type')").find_next("dd").text.strip() if soup.select_one("dt:-soup-contains('Employment Type')") else None,
        )
    except requests.RequestException as error:
        print("Error fetching or scraping job detail:", error)
        if retries < MAX_RETRIES:
            return scrape_job_detail(jobDetailUrl, retries + 1)
        else:
            return JobListing(detailUrl=jobDetailUrl)

# Function to scrape a single page of remote jobs
def scrape_single_page(driver) -> List[JobListing]:
    """Scrape job listings from the current page."""
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    job_list = []

    for element in soup.select("#results_inner_card li[data-js-job]"):
        # Extract company name and location from the correct nested divs
        company_div = element.select_one("div.t-nowrap.p10l")
        company_name = company_div.select_one("div.t-nowrap span.t-default").text.strip() if company_div and company_div.select_one("div.t-nowrap span.t-default") else ""
        job_location = company_div.select_one("div.t-mute").text.strip() if company_div and company_div.select_one("div.t-mute") else ""

        # Create the JobListing object
        job = JobListing(
            job_title=element.select_one("h2 a").text.strip() if element.select_one("h2 a") else "",
            company_name=company_name,
            jobLocation=job_location,
            job_description=element.select_one(".m10t.t-small").text.strip() if element.select_one(".m10t.t-small") else "",
            experience=element.select_one("ul.list li[data-automation-id='id_careerlevel']").text.strip() if element.select_one("ul.list li[data-automation-id='id_careerlevel']") else "",
            posting_date=element.select_one("[data-automation-id='job-active-date']").text.strip() if element.select_one("[data-automation-id='job-active-date']") else "",
            easyApply="Easy apply" in element.select_one("a.btn.is-small").text if element.select_one("a.btn.is-small") else False,
            detailUrl=urljoin(BASE_URL, element.select_one("h2 a").get("href")) if element.select_one("h2 a") else ""
        )

        print(f"Company name: {job.company_name}, Location: {job.jobLocation}")

        # Fetch detailed information only if detail URL is present
        if job.detailUrl:
            detail_data = scrape_job_detail(job.detailUrl)
            if detail_data:
                # Update only necessary fields from detail page
                job.job_description = detail_data.job_description or job.job_description
                job.skillsRequired = detail_data.skillsRequired or job.skillsRequired
                job.companyIndustry = detail_data.companyIndustry or job.companyIndustry
                job.employmentType = detail_data.employmentType or job.employmentType
                job.numberOfVacancies = detail_data.numberOfVacancies or job.numberOfVacancies
                job.monthlySalaryRange = detail_data.monthlySalaryRange or job.monthlySalaryRange
                job.job_type = detail_data.job_type

        job_list.append(job)

    return job_list

# Function to handle pagination and scrape all job listings
def scrape_remote_jobs_with_pagination(driver) -> List[JobListing]:
    """Scrape all remote jobs, handling pagination."""
    all_jobs = []
    current_page = 1

    while True:
        print(f"Scraping page {current_page}...")
        jobs = scrape_single_page(driver)
        all_jobs.extend(jobs)

        # Check for the 'Next' button and navigate to the next page
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "li.pagination-next a")
            if next_button.is_displayed() and next_button.is_enabled():
                driver.execute_script("arguments[0].click();", next_button)  # Click using JavaScript to avoid interception issues
                WebDriverWait(driver, 20).until(EC.staleness_of(driver.find_element(By.CSS_SELECTOR, "#results_inner_card li[data-js-job]")))
                current_page += 1
            else:
                break
        except Exception as e:
            print(f"Error navigating to the next page: {e}")
            break

    return all_jobs

# Main function to scrape Bayt jobs
def scrape_bayt_jobs(progress_callback=None) -> List[JobListing]:
    """
    Scrapes job listings from Bayt and returns a list of job details.
    Args:
        progress_callback (function): A callback function to update the progress bar.
    Returns:
        list: A list of JobListing objects containing job details.
    """
    driver = None
    try:
        driver = setup_driver()
        driver.get("https://www.bayt.com/en/international/jobs/?filters%5Bjb_last_modification_date_interval%5D%5B%5D=3&filters%5Bremote_working_type%5D%5B%5D=1")
        
        # Scrape all jobs with pagination
        scraped_jobs = scrape_remote_jobs_with_pagination(driver)
        
        # Update progress if callback is provided
        if progress_callback:
            progress_callback(len(scraped_jobs))

        # Final data processing and transformation
        final_job_listings = []
        for job in scraped_jobs:
            predicted_sector = SectorID.findSector(job.job_title)
            predicted_career_level, predicted_experience = Experience.getExperience(job.experience)
            predicted_job_type = [JobType.predictJobType(job.job_type)]

            job_model = Job(
                title=job.job_title,
                company=job.company_name,
                job_type=predicted_job_type,
                job_sector=[predicted_sector],
                location=job.jobLocation,
                content=job.job_description,
                experience=predicted_experience,
                career_level=predicted_career_level,
                posted_time=job.posting_date,
                job_apply_url=job.detailUrl
            )
            final_job_listings.append(job_model)

        return final_job_listings

    except Exception as ex:
        print(f"An error occurred: {ex}")
        return []

    finally:
        if driver:
            driver.quit()

# Example usage (Uncomment if needed)
# if __name__ == "__main__":
#     jobs = scrape_bayt_jobs()
#     for job in jobs:
#         print(job.__dict__)
