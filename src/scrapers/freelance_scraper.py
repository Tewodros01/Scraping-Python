import csv
from typing import List, Optional, Dict
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
    average_bid: Optional[str] = None
    bids: Optional[str] = None
    job_apply_url: Optional[str] = None
    budget: Optional[str] = None
    posted_time: Optional[str] = None
    payment_method: Optional[str] = None
    job_tags: Optional[List[str]] = None

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

def scrape_job_info(job_card):
    """Extract job information from a single job card element."""
    title_element = job_card.find('a', class_='JobSearchCard-primary-heading-link')
    title = title_element.text.strip() if title_element else None
    job_apply_url = "https://www.freelancer.com" + title_element['href'] if title_element and 'href' in title_element.attrs else None
    
    description_element = job_card.find('p', class_='JobSearchCard-primary-description')
    content = description_element.text.strip() if description_element else None
    
    skills_elements = job_card.find_all('a', class_='JobSearchCard-primary-tagsLink')
    job_sector = [skill.text.strip() for skill in skills_elements] if skills_elements else None
    
    days_left_element = job_card.find('span', class_='JobSearchCard-primary-heading-days')
    expiry = days_left_element.text.strip() if days_left_element else None
    
    avg_bid_element = job_card.find('div', class_='JobSearchCard-secondary-price')
    average_bid = avg_bid_element.text.strip().split(' ')[0] if avg_bid_element else None
    
    bids_element = job_card.find('div', class_='JobSearchCard-secondary-entry')
    bids = bids_element.text.strip() if bids_element else None

    return JobModel(
        expiry=expiry,
        title=title,
        content=content,
        job_sector=job_sector,
        average_bid=average_bid,
        bids=bids,
        job_apply_url=job_apply_url
    )

def scrape_detailed_job_info(driver, job):
    """Scrape detailed information from the job detail page with error handling."""
    try:
        driver.get(job.job_apply_url)
        
        # Wait for the job detail page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Project-heading"))
        )
        
        # Extract job details
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Check for the first type of job detail page structure
        if soup.find('h1', class_='PageProjectViewLogout-projectInfo-title'):
            job = extract_first_job_detail_structure(soup, job)
        # Check for the second type of job detail page structure
        elif soup.find('h1', class_='ng-star-inserted'):
            job = extract_second_job_detail_structure(soup, job)
        
    except TimeoutException:
        logging.warning(f"Timeout while loading job details for URL: {job.job_apply_url}")
    
    except Exception as e:
        logging.error(f"Error scraping detailed job info for URL: {job.job_apply_url} - {str(e)}")
    
    return job

def extract_first_job_detail_structure(soup, job):
    """Extract details for the first type of job detail page structure."""
    # Extract Job Title
    title_element = soup.find('h1', class_='PageProjectViewLogout-projectInfo-title')
    job.title = title_element.text.strip() if title_element else job.title
    
    # Extract Job Description
    content_element = soup.find('div', class_='PageProjectViewLogout-detail')
    job.content = content_element.get_text(separator=' ').strip() if content_element else job.content
    
    # Extract Posted Time
    posted_time_element = soup.find('span', class_='PageProjectViewLogout-projectInfo-label-deliveryInfo-relativeTime')
    job.posted_time = posted_time_element.text.strip() if posted_time_element else None
    
    # Extract Payment Method
    payment_method_element = soup.find('span', class_='PageProjectViewLogout-projectInfo-label-deliveryInfo-payment')
    job.payment_method = payment_method_element.text.strip() if payment_method_element else None
    
    # Extract Budget
    budget_element = soup.find('p', class_='PageProjectViewLogout-projectInfo-byLine')
    job.budget = budget_element.text.strip() if budget_element else None

    # Extract Job Tags
    tags_elements = soup.find_all('a', class_='PageProjectViewLogout-detail-tags-link--highlight')
    job.job_tags = [tag.text.strip() for tag in tags_elements] if tags_elements else None

    # Extract Email
    email_element = soup.find('input', {'type': 'email'})
    job.email = email_element.get('value', None) if email_element else None

    # Extract Location
    location_element = soup.find('span', class_='PageProjectViewLogout-detail-summary-item', string="Remote project")
    job.location = location_element.text.strip() if location_element else None

    return job

def extract_second_job_detail_structure(soup, job):
    """Extract details for the second type of job detail page structure."""
    # Extract Job Title
    title_element = soup.find('h1', class_='ng-star-inserted')
    job.title = title_element.text.strip() if title_element else job.title
    
    # Extract Job Description
    content_element = soup.find('fl-text', class_='Project-description')
    job.content = content_element.get_text(separator=' ').strip() if content_element else job.content
    
    # Extract Posted Time
    posted_time_element = soup.find('fl-relative-time')
    job.posted_time = posted_time_element.get_text(separator=' ').strip() if posted_time_element else None
    
    # Extract Payment Method
    payment_method_element = soup.find('div', class_='Project-heading-title').find_next('div')
    job.payment_method = payment_method_element.text.strip() if payment_method_element else None
    
    # Extract Budget
    budget_element = soup.find('h2', {'data-color': 'foreground'})
    job.budget = budget_element.text.strip() if budget_element else None

    # Extract Job Tags
    tags_elements = soup.find_all('fl-link', {'data-tag-type': 'clickable'})
    job.job_tags = [tag.get_text(separator=' ').strip() for tag in tags_elements] if tags_elements else None

    # Extract Location
    location_element = soup.find('fl-text', string="Remote project")
    job.location = location_element.text.strip() if location_element else None

    return job

def scrape_jobs(url):
    """Scrape job listings from the provided URL and return them as a list of JobModel objects."""
    driver = setup_driver()
    driver.get(url)

    # Wait for the job listings to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "project-list"))
    )

    # Get the page source and parse it with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    job_cards = soup.find_all('div', class_='JobSearchCard-item')
    
    # Extract information from each job card
    jobs = [scrape_job_info(job_card) for job_card in job_cards]
    
    # Scrape detailed information from each job's detail page
    for job in jobs:
        if job.job_apply_url:
            job = scrape_detailed_job_info(driver, job)
    
    driver.quit()
    return jobs

def save_jobs_to_csv(jobs, filename='scraped_jobs_for_wordpress.csv'):
    """Save job data to a CSV file for use in WordPress."""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'expiry', 'title', 'content', 'location', 'company', 'email', 
                'job_sector', 'job_type', 'qualifications', 'field_of_study', 
                'career_level', 'job_apply_type', 'experience', 'job_apply_url',
                'budget', 'posted_time', 'payment_method', 'job_tags'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    'expiry': job.expiry,
                    'title': job.title,
                    'content': job.content,
                    'location': job.location,
                    'company': job.company,
                    'email': job.email,
                    'job_sector': ', '.join(job.job_sector) if job.job_sector else None,
                    'job_type': ', '.join(job.job_type) if job.job_type else None,
                    'qualifications': ', '.join(job.qualifications) if job.qualifications else None,
                    'field_of_study': ', '.join(job.field_of_study) if job.field_of_study else None,
                    'career_level': job.career_level,
                    'job_apply_type': job.job_apply_type,
                    'experience': job.experience,
                    'job_apply_url': job.job_apply_url,
                    'budget': job.budget,
                    'posted_time': job.posted_time,
                    'payment_method': job.payment_method,
                    'job_tags': ', '.join(job.job_tags) if job.job_tags else None
                })
        logging.info(f"Jobs successfully saved to {filename}.")
    except Exception as e:
        logging.error(f"Failed to save jobs to CSV: {str(e)}")

def scrape_freelance_jobs(progress_callback=None) -> List[Job]:
    """Scrape job listings from Freelancer and return a list of job details."""
    
    # List of URLs to scrape
    urls = [
        "https://www.freelancer.com/jobs/logo-design",
        "https://www.freelancer.com/jobs/graphic-design",
        "https://www.freelancer.com/jobs/data-entry",
        "https://www.freelancer.com/jobs/mobile-phone",
        "https://www.freelancer.com/jobs/internet-marketing",
        "https://www.freelancer.com/jobs/software-development",
        "https://www.freelancer.com/jobs/internet-marketing",
        "https://www.freelancer.com/jobs/writing",
        ""
        # "https://www.freelancer.com/jobs/php"
    ]

    all_jobs = []

    logging.info("Starting job scraping for multiple URLs...")
    
    # Set up the driver once
    driver = setup_driver()
    
    total_urls = len(urls)  # Total number of URLs to scrape

    # Loop through URLs and scrape jobs
    for url_index, url in enumerate(urls):
        logging.info(f"Scraping {url}...")
        jobs = scrape_jobs(url)
        all_jobs.extend(jobs)
        
        # Update the progress bar
        if progress_callback:
            progress = (url_index + 1) / total_urls
            progress_callback(progress)

    # Clean up the driver
    driver.quit()
    
    # Save jobs to CSV for WordPress
    save_jobs_to_csv(all_jobs)
    logging.info("Scraping complete. Jobs saved to 'scraped_jobs_for_wordpress.csv'.")

    # Collect job details into the list to return
    all_job_listings = []
    for job in all_jobs:
      # Predict the sector using the saved model
      print('Job title to predict ', job.title)
      predicted_sector = SectorID.findSector(job.title)
  
      # Predict the experience using the saved model
      # print('Job Experience and career_level to predict' ,job.experience)
      # predicted_career_level,predicted_experience = Experience.getExperience(job.experience)
      
      # Predict the job type using the saved model
      # Check if job_type is a list and predict each type
      predicted_jobType = [JobType.predictJobType(job.job_type)]

      job_model = Job(
          email="privatefreelancer@sebatsolutions.com",
          title=job.title,
          company=job.company,
          location=job.location,
          content=job.content,
          job_sector=predicted_sector,
          experience=job.experience,
          job_type=predicted_jobType,
          posted_time=job.posted_time,
          expiry=job.expiry,
          job_apply_url=job.job_apply_url
      )
      all_job_listings.append(job_model)

    return all_job_listings
