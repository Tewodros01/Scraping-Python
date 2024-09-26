from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
from typing import List

# Initialize logging
logging.basicConfig(level=logging.INFO)

def setup_driver() -> webdriver.Chrome:
    """Set up the Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-gpu")
    # options.add_argument('--headless')  # Uncomment to run in headless mode
    driver = webdriver.Chrome(options=options)
    return driver

@dataclass
class JobListing:
    """Data class to represent a job listing."""
    title: str
    company: str
    tags: List[str]
    posted_time: str
    job_link: str

def scrape_current_page_jobs(driver: webdriver.Chrome) -> List[JobListing]:
    """Scrape job listings currently displayed on the page."""
    job_listings = []
    try:
        # Find all job listing elements
        job_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-mark-visited-links-target='container']")

        for job in job_elements:
            try:
                # Extract job title, company, and link
                title_element = job.find_element(By.CSS_SELECTOR, "a[data-mark-visited-links-target='anchor'] div.truncate")
                title = title_element.text.strip()

                # Adjusting selector to ensure company name is extracted properly
                company_element = job.find_element(By.XPATH, ".//div[@class='flex items-center gap-2']/a[1]")
                company = company_element.text.strip()

                job_link = job.find_element(By.CSS_SELECTOR, "a[data-mark-visited-links-target='anchor']").get_attribute("href")

                # Extract tags
                tag_elements = job.find_elements(By.CSS_SELECTOR, "div[data-post-template-target='tags'] a.tag")
                tags = [tag.text.strip() for tag in tag_elements]

                # Extract posted time
                posted_time_element = job.find_element(By.CSS_SELECTOR, "time[data-post-template-target='timestamp']")
                posted_time = posted_time_element.text.strip()

                # Create JobListing object and add to the list
                job_listing = JobListing(
                    title=title,
                    company=company,
                    tags=tags,
                    posted_time=posted_time,
                    job_link=job_link
                )
                job_listings.append(job_listing)
                logging.info(f"Scraped Job: {title} at {company}")

            except Exception as e:
                logging.error(f"Error extracting job details: {e}")

    except Exception as e:
        logging.error(f"An error occurred while scraping jobs on the current page: {e}")

    return job_listings

def scrape_jobs(driver: webdriver.Chrome, urls: List[str]) -> List[JobListing]:
    """Scrape job listings from multiple URLs."""
    job_listings = []
    for url in urls:
        try:
            driver.get(url)
            logging.info(f"Accessing URL: {url}")

            # Scrape jobs from the current page
            job_listings.extend(scrape_current_page_jobs(driver))

        except TimeoutException as e:
            logging.error(f"Timeout while waiting for elements to load on {url}: {e}")
        except Exception as e:
            logging.error(f"An error occurred on {url}: {e}")

    # Remove duplicates by converting to a set of tuples and back to a list of JobListing
    job_listings = list({(job.title, job.company, tuple(job.tags), job.posted_time, job.job_link): job for job in job_listings}.values())

    return job_listings

if __name__ == "__main__":
    # Set up WebDriver
    driver = setup_driver()
    
    # List of URLs to scrape
    urls = [
        "https://startup.jobs/remote-jobs?remote=true",
        "https://startup.jobs/remote-jobs?remote=true&page=2",
        "https://startup.jobs/remote-jobs?remote=true&page=3",
        "https://startup.jobs/remote-jobs?remote=true&page=4",
        "https://startup.jobs/remote-jobs?remote=true&page=5"
    ]

    # Scrape job listings
    job_listings = scrape_jobs(driver, urls)

    # Print the scraped job listings
    for job in job_listings:
        print(f"Title: {job.title}, Company: {job.company}, Tags: {', '.join(job.tags)}, Posted Time: {job.posted_time}, Link: {job.job_link}")

    # Close the WebDriver
    driver.quit()
