import sys
import os
import customtkinter as ctk

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
from model.job_model import Job
from typing import List


class JobListing:
    """
    A class to represent a job listing.
    """
    def __init__(self, title, company, location, description, posted_date, job_type, on_site_required, scraped_time, job_apply_url):
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.posted_date = posted_date
        self.job_type = job_type
        self.on_site_required = on_site_required
        self.scraped_time = scraped_time
        self.job_apply_url = job_apply_url

    def __repr__(self):
        return f"Job(title='{self.title}', company='{self.company}', location='{self.location}', posted_date='{self.posted_date}', job_type='{self.job_type}', on_site_required='{self.on_site_required}', scraped_time='{self.scraped_time}', job_apply_url='{self.job_apply_url}')"


def setup_driver() -> webdriver.Chrome:
    """Set up the Selenium WebDriver using a context manager."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--incognito")
    # Uncomment the following line to run in headless mode (without opening a browser window)
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver


def scrape_job_details(driver, modal_url):
    """
    Scrapes job details from the currently open modal.
    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        modal_url (str): The URL of the modal being scraped.
    Returns:
        dict: A dictionary containing job details.
    """
    job_detail = {}
    try:
        # Wait for modal content to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.JobDetailContent-jobDetailContainer-LyM')))
        modal_html = driver.page_source
        modal_soup = BeautifulSoup(modal_html, 'html.parser')

        # Scraping the job details
        job_detail['title'] = modal_soup.select_one('.JobDetailContent-headerTitle-rlk').text.strip() if modal_soup.select_one('.JobDetailContent-headerTitle-rlk') else 'N/A'
        job_detail['company'] = modal_soup.select_one('.JobDetailContent-companyNameLink-EUx').text.split('opens')[0].strip() if modal_soup.select_one('.JobDetailContent-companyNameLink-EUx') else 'N/A'
        job_detail['location'] = modal_soup.select_one('.JobDetailContent-companyEmDash-Hkf').next_sibling.strip() if modal_soup.select_one('.JobDetailContent-companyEmDash-Hkf') else 'N/A'
        job_detail['description'] = modal_soup.select_one('.JobDetailContent-jobContent-Nga').text.strip() if modal_soup.select_one('.JobDetailContent-jobContent-Nga') else 'N/A'

        # Scraping additional details
        details = modal_soup.select('.JobDetailContent-detailItem-nks')
        for detail in details:
            title = detail.select_one('.JobDetailContent-detailTitle-MCn').text.strip()
            text = detail.select_one('.JobDetailContent-detailText-Fmk').text.strip()
            job_detail[title] = text

        # Assign default values if they don't exist
        job_detail.setdefault('Job Type', 'N/A')
        job_detail.setdefault('Job Location', 'N/A')
        job_detail.setdefault('On Site Required', 'N/A')
        job_detail.setdefault('Job Posted', 'N/A')
        job_detail['job_apply_url'] = modal_url  # Assign the current modal URL as job apply URL

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error scraping job details: {e}")
    
    return job_detail


def scrape_behance_jobs(progress_callback=None) -> List[Job]:
    """
    Scrapes job listings from Behance until reaching target_job_count or end of page.
    Args:
        target_job_count (int): Number of jobs to scrape before stopping.
        progress_callback (function): A callback function to update the progress bar.
    Returns:
        list: A list of JobListing objects containing job details.
    """
    driver = setup_driver()
    url = "https://www.behance.net/joblist?tracking_source=nav20"
    driver.get(url)
    time.sleep(5)  # Wait for the page to load completely

    job_listings = []
    job_cards = driver.find_elements(By.CSS_SELECTOR, '.JobCard-jobCard-mzZ')
    target_job_count=200
    total_jobs_scraped = 0
    last_job_count = 0

    while total_jobs_scraped < target_job_count:
        # Scroll down to load more jobs
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for the new jobs to load

        # Get updated list of job cards
        job_cards = driver.find_elements(By.CSS_SELECTOR, '.JobCard-jobCard-mzZ')
        current_job_count = len(job_cards)
        
        # If no new jobs are loaded, break the loop
        if current_job_count == last_job_count:
            print("No more jobs to load, ending scroll.")
            break
        
        last_job_count = current_job_count
        print(f"Total job cards found: {current_job_count}")

        for index in range(total_jobs_scraped, current_job_count):
            card = job_cards[index]

            # Extract company name from job card
            try:
                company_name = card.find_element(By.CSS_SELECTOR, '.JobCard-company-GQS').text.strip()
            except NoSuchElementException:
                company_name = 'N/A'
            
            # Scroll into view and click the job card
            driver.execute_script("arguments[0].scrollIntoView(true);", card)
            time.sleep(1)

            retries = 3
            for attempt in range(retries):
                try:
                    link = card.find_element(By.CSS_SELECTOR, '.JobCard-jobCardLink-Ywm')
                    driver.execute_script("arguments[0].click();", link)
                    break
                except (StaleElementReferenceException, NoSuchElementException) as e:
                    print(f"Retry {attempt + 1} clicking card due to error: {e}")
                    time.sleep(1)
            else:
                print(f"Failed to click card after {retries} retries.")
                continue

            # Wait for the modal to appear
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.JobDetailContent-jobDetailContainer-LyM')))
            except TimeoutException:
                print(f"Error waiting for modal: Modal did not appear.")
                continue

            # Get current URL as job apply URL
            modal_url = driver.current_url

            # Scrape job details from the modal
            job_details = scrape_job_details(driver, modal_url)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
            job_listings.append(
                JobListing(
                    title=job_details['title'],
                    company=company_name,  # Use company name extracted from job card
                    location=job_details['location'],
                    description=job_details['description'],
                    posted_date=job_details['Job Posted'],
                    job_type=job_details['Job Type'],
                    on_site_required=job_details['On Site Required'],
                    scraped_time=current_time,
                    job_apply_url=job_details['job_apply_url']  # Add apply URL from modal
                )
            )
            total_jobs_scraped += 1

            # Update the progress bar
            if progress_callback:
                progress = total_jobs_scraped / target_job_count
                progress_callback(progress)

            # Close the modal
            try:
                close_button = driver.find_element(By.CSS_SELECTOR, '.UniversalPopup-closeModule-RuD')
                driver.execute_script("arguments[0].click();", close_button)
            except NoSuchElementException as e:
                print(f"Error closing modal: {e}")
                continue

            # Wait for the modal to close
            try:
                WebDriverWait(driver, 10).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.JobDetailContent-jobDetailContainer-LyM'))
                )
            except TimeoutException:
                print(f"Error waiting for modal to close.")
                continue

            # Add a short wait to ensure stability
            time.sleep(1)

    driver.quit()

    # Collect job details into the list
    all_job_listings = []
    for job in job_listings:
        job_model = Job(
            title=job.title,
            content=job.description,
            posted_time=job.posted_date,
            company=job.company,
            job_type=job.job_type,
            location=job.location,
            job_apply_url=job.job_apply_url
        )
        print("Job Model:", job_model)
        all_job_listings.append(job_model)

    return all_job_listings


