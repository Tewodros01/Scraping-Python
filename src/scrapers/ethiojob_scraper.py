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
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time

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
    # Uncomment the following line to run in headless mode (without opening a browser window)
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver

def extract_info(parent, label: str) -> Optional[str]:
    """Extract specific job information from the parent element."""
    if parent:
        elem = parent.find(text=lambda x: label in x)
        return elem.split(label)[-1].strip() if elem else None
    return None

def scrape_job_by_sector(sector: JobSector, driver: webdriver.Chrome) -> None:
    """Scrape job listings from a sector detail page and add them to the sector."""
    try:
        driver.get(sector.url)
        logging.info(f"Accessing sector URL: {sector.url}")

        # Wait for the page to fully load
        WebDriverWait(driver, 120).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(10)  # Additional wait to handle splash screen or dynamic loading elements
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-2.mui-style-isbt42'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_cards = soup.select('.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation1.jss2.mui-style-aoeo82')

        for card in job_cards:
            try:
                # Extract job title
                job_title_elem = card.select_one('p.MuiTypography-root.MuiTypography-body1.MuiTypography-alignLeft.mui-style-sz2p1p')
                title = job_title_elem.get_text(strip=True) if job_title_elem else None

                # Extract company name
                company_elem = card.select_one('p.MuiTypography-root a')
                company = company_elem.get_text(strip=True) if company_elem else None

                # Extract location
                location_elem = card.select_one('.MuiSvgIcon-root[data-testid="LocationCityIcon"] + p')
                location = location_elem.get_text(strip=True) if location_elem else None

                # Extract posted time
                posted_time_elem = card.select_one('p.MuiTypography-root.MuiTypography-body1.mui-style-1vlcel7[style*="font-size: 12px; color: rgb(0, 0, 0); text-transform: none;"]')
                posted_time = posted_time_elem.get_text(strip=True) if posted_time_elem else None

                # Extract job detail URL
                job_url_elem = card.select_one('a[href^="/jobs/"]')
                job_apply_url = job_url_elem['href'] if job_url_elem else None
                if job_apply_url and not job_apply_url.startswith("http"):
                    job_apply_url = "https://ethiojobs.net" + job_apply_url

                # Extract job expiry (Deadline)
                deadline_elements = card.select('p.MuiTypography-root.MuiTypography-body1.mui-style-17n0xwk')
                expiry = None
                for elem in deadline_elements:
                    if "Deadline" in elem.get_text(strip=True):
                        expiry = elem.get_text(strip=True).replace("Deadline : ", "")
                        break

                # Scrape detailed job information from the job detail page
                job_details = scrape_job_detail(job_apply_url, driver) if job_apply_url else JobModel()

                # Create a JobModel instance with all extracted details
                job = JobModel(
                    title=title,
                    company=company,
                    location=location,
                    posted_time=posted_time,
                    job_apply_url=job_apply_url,
                    expiry=expiry,
                    content=job_details.content,
                    job_sector=job_details.job_sector,
                    job_type=job_details.job_type,
                    qualifications=job_details.qualifications,
                    field_of_study=job_details.field_of_study,
                    career_level=job_details.career_level,
                    job_apply_type=job_details.job_apply_type,
                    experience=job_details.experience,
                    salary=job_details.salary,
                    skills=job_details.skills
                )

                # Append the job to the sector's job list
                sector.job_list.append(job)

            except (StaleElementReferenceException, NoSuchElementException) as e:
                logging.error(f"Error while parsing job card: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while scraping job card: {e}")

        logging.info(f"Scraped {len(sector.job_list)} jobs from {sector.url}.")

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
    except Exception as e:
        logging.error(f"An error occurred while accessing the sector page: {e}")

def scrape_job_detail(job_url: str, driver: webdriver.Chrome) -> JobModel:
    """Scrape detailed job information from a job detail page."""
    try:
        # Open the job detail page
        driver.get(job_url)
        logging.info(f"Accessing job URL: {job_url}")

        # Set window size to ensure all content is visible
        driver.set_window_size(1920, 1080)

        # Wait until the job details are fully loaded
        WebDriverWait(driver, 120).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )

        # Additional wait time for dynamic elements to load
        time.sleep(5)

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract the job title
        title_element = soup.select_one('p.MuiTypography-root[style*="font-size: 24px;"]')
        if not title_element:
            title_element = soup.find('h1')  # Alternative selector
        title = title_element.get_text(strip=True) if title_element else None

        # Extract the location
        location_element = soup.select_one('p.MuiTypography-root[style*="font-size: 18px;"]')
        if not location_element:
            location_element = soup.find('p', class_='MuiTypography-body1')  # Alternative selector
        location = location_element.get_text(strip=True) if location_element else None

        # Extract the company name
        company_element = soup.select_one('img[alt]')
        company = company_element['alt'] if company_element else None

        # Extract job sector correctly, filtering out unnecessary sectors
        job_sector_elements = soup.select('.MuiChip-root .MuiChip-label')
        job_sector = list({elem.get_text(strip=True) for elem in job_sector_elements if "Jobs in" not in elem.get_text() and "Jobs for" not in elem.get_text()})

        # Extract content (job description)
        content_element = soup.select_one('div[style*="margin-top: 20%;"]')
        if not content_element:
            content_element = soup.find('div', class_='job-description')  # Alternative selector
        content = content_element.get_text(strip=True) if content_element else None

        # Extract expiry date
        expiry_element = soup.select_one('li:contains("Deadline:") .MuiTypography-body1')
        expiry = expiry_element.get_text(strip=True).replace('Deadline: ', '') if expiry_element else None

        # Extract career level
        career_level_element = soup.select_one('li:contains("Career Level :") .MuiTypography-body1')
        career_level = career_level_element.get_text(strip=True).replace('Career Level :', '') if career_level_element else None

        # Extract job type (employment type)
        job_type_element = soup.select_one('li:contains("Employment Type :") .MuiTypography-body1')
        job_type = job_type_element.get_text(strip=True).replace('Employment Type :', '') if job_type_element else None

        # Extract experience
        experience_element = soup.select_one('li:contains("Work Experience :") .MuiTypography-body1')
        experience = experience_element.get_text(strip=True).replace('Work Experience :', '') if experience_element else None

        # Extract qualifications
        qualifications_elements = soup.select('div[style*="margin-top: 20%;"] li')
        qualifications = [elem.get_text(strip=True) for elem in qualifications_elements if 'Degree' in elem.get_text()]

        # Extract field of study
        field_of_study_elements = soup.select('div[style*="margin-top: 20%;"] li')
        field_of_study = [elem.get_text(strip=True) for elem in field_of_study_elements if 'Field' in elem.get_text()]

        # Extract required skills
        skills_section = soup.select_one('div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.mui-style-1tyjws8')

        # Now, select the ul element inside that specific section
        if skills_section:
            skills_list = skills_section.select_one('div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.mui-style-wswhdp ul.MuiList-root.MuiList-padding.mui-style-etmovu')

            # Ensure the ul element exists before finding li elements
            if skills_list:
                # Extract each skill using the li element under the ul
                skills_elements = skills_list.select('li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.mui-style-tik4nx')

                # Extract text safely from each 'li' element if the 'span' exists
                skills = [elem.select_one('div.MuiListItemText-root span.MuiTypography-root.MuiTypography-body1.MuiListItemText-primary.mui-style-1b4jcyw').get_text(strip=True)
                          for elem in skills_elements if elem.select_one('div.MuiListItemText-root span.MuiTypography-root.MuiTypography-body1.MuiListItemText-primary.mui-style-1b4jcyw')]
            else:
                skills = []
        else:
            skills = []

        # skills_elements = soup.select('ul.MuiList-root li .MuiListItemText-root .MuiTypography-root')
        # skills = [elem.get_text(strip=True) for elem in skills_elements]

        # Extract job application URL
        job_apply_url_element = soup.select_one('a[href*="forms.office.com"]')
        job_apply_url = job_apply_url_element['href'] if job_apply_url_element else None

        # Extract posted time
        posted_time_element = soup.select_one('div.MuiGrid-root.MuiGrid-item.p-2 > p')
        posted_time = posted_time_element.get_text(strip=True) if posted_time_element else None

        # Extract salary (if available)
        salary_element = soup.find('li', string=lambda text: text and 'Salary :' in text)
        salary = salary_element.get_text(strip=True).replace('Salary :', '') if salary_element else None
        
        # Extract "How to Apply" section
        how_to_apply_section = soup.select_one('p.MuiTypography-root.MuiTypography-body1.MuiTypography-alignLeft.mui-style-pdximt')
        
        if how_to_apply_section:
            # Look for 'p' tags within the parent container
            how_to_apply_texts = how_to_apply_section.find_all('p', recursive=False)

            # Combine all paragraphs into a single string
            how_to_apply = ' '.join([p.get_text(strip=True) for p in how_to_apply_texts if p.get_text(strip=True)])
        else:
            how_to_apply = None
        print("How to apply", how_to_apply_texts)

        # Create JobModel object with all extracted details
        job_detail = JobModel(
            expiry=expiry,
            title=title,
            content=content,
            location=location,
            company=company,
            email=None,  # Assuming no direct extraction is required
            job_sector=job_sector,
            job_type=job_type,
            qualifications=qualifications,
            field_of_study=field_of_study,
            career_level=career_level,
            job_apply_type=None,  # Assuming this is not provided directly
            experience=experience,
            job_apply_url=job_apply_url,
            posted_time=posted_time,
            salary=salary,
            skills=skills
        )

        logging.info(f"Scraped job details from {job_url}.")
        return job_detail

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
    except Exception as e:
        logging.error(f"An error occurred while scraping job details: {e}")

    # Return an empty JobModel if an error occurs
    return JobModel()

def save_jobs_to_csv(all_sectors: List[JobSector]):
    """Save all job data from all sectors to a single CSV file."""
    filename = 'ethiojobs_all_sectors.csv'
    
    # Define the fieldnames based on the JobModel dataclass attributes
    fieldnames = [
        'expiry', 'title', 'content', 'location', 'company', 'email',
        'job_sector', 'job_type', 'qualifications', 'field_of_study',
        'career_level', 'job_apply_type', 'experience', 'job_apply_url',
        'posted_time', 'salary', 'skills'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row
        
        for sector in all_sectors:
            for job in sector.job_list:
                # Convert job data into a dictionary
                job_data = {
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
                    'posted_time': job.posted_time,
                    'salary': job.salary,
                    'skills': ', '.join(job.skills) if job.skills else None
                }
                
                # Write the job data to the CSV file
                writer.writerow(job_data)
    
    logging.info(f"Saved jobs from all sectors to {filename}.")

def scrape_ethio_jobs(progress_callback=None) -> List[Job]:
    """Scrape job listings from ethijob and return a list of JobModel instances."""
    job_listings = []
    all_job_sectors = []
    logging.info("Starting job scraping by category URLs...")

    driver = setup_driver()

    # Iterate over predefined sectors and their URLs
    predefinedSectors = [
        "Accounting and Finance",
        "Admin, Secretarial and Clerical",
        "Business and Administration",
        "Business Development",
        "Communications Media Journalism",
        "Consultancy and Training",
        "Customer Service",
        "Economics",
        "Education",
        "Engineering",
        "Environment and Natural Resource",
        "FMCG and Manufacturing",
        "Health Care",
        "Hotel and Hospitality",
        "Human Resource and Recruitment",
        "IT Computer Science and Engineering",
        "Legal"
        # Add more sectors here...
    ]

    category_urls = [
        "https://ethiojobs.net/jobs?search=Accounting+and+Finance&page=1",
        # "https://ethiojobs.net/jobs?search=Admin%2C+Secretarial%2C+and+Clerical&page=1",
        # "https://ethiojobs.net/jobs?search=Business+and+Administration&page=1",
        # "https://ethiojobs.net/jobs?search=Business+Development&page=1",
        # "https://ethiojobs.net/jobs?search=Communications%2C+Media+and+Journalism&page=1",
        # "https://ethiojobs.net/jobs?search=Consultancy+and+Training&page=1",
        # "https://ethiojobs.net/jobs?search=Customer+Service&page=1",
        # "https://ethiojobs.net/jobs?search=Development+and+Project+Management&page=1",
        # "https://ethiojobs.net/jobs?search=Economics&page=1",
        # "https://ethiojobs.net/jobs?search=Education&page=1",
        # "https://ethiojobs.net/jobs?search=Engineering&page=1",
        # "https://ethiojobs.net/jobs?search=Environment+and+Natural+Resource&page=1",
        # "https://ethiojobs.net/jobs?search=FMCG+and+Manufacturing&page=1",
        # "https://ethiojobs.net/jobs?search=Health+Care&page=1",
        # "https://ethiojobs.net/jobs?search=Hotel+and+Hospitality&page=1",
        # "https://ethiojobs.net/jobs?search=Human+Resource+and+Recruitment&page=1",
        # "https://ethiojobs.net/jobs?search=IT%2C+Computer+Science+and+Software+Engineering&page=1",
        # "https://ethiojobs.net/jobs?search=Legal&page=1"
        # Add more category url here...
    ]

    total_sectors = len(predefinedSectors)
    for sector_index, (sector_name, category_url) in enumerate(zip(predefinedSectors, category_urls)):
        logging.info(f"Scraping jobs for sector: {sector_name} from URL: {category_url}")

        # Update the progress bar
        if progress_callback:
            progress = (sector_index + 1) / total_sectors
            progress_callback(progress)

        # Initialize a JobSector object for each sector
        job_sector = JobSector(name=sector_name, url=category_url, job_list=[])

        # Scrape jobs for the sector and populate job_list in JobSector
        scrape_job_by_sector(job_sector, driver)

        # Append the populated JobSector to the list
        all_job_sectors.append(job_sector)

    # Save the scraped job data to a CSV file
    save_jobs_to_csv(all_job_sectors)

    # Quit the WebDriver
    driver.quit()

    # Collect job details into the list
    all_job_listings = []
    for sector in all_job_sectors:
        for job in sector.job_list:
            # Predict the sector using the saved model
            print('Job title to predict ', job.title)
            predicted_sector = [SectorID.findSector(job.title)]
        
            # Predict the experience using the saved model
            print('Job Experience and career_level to predict' ,job.experience)
            predicted_career_level,predicted_experience = Experience.getExperience(job.experience)
            
            # Predict the job type using the saved model
            # Check if job_type is a list and predict each type
            predicted_jobType = [JobType.predictJobType(job.job_type)]

            # Convert list to string for CSV storage
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

    logging.info("Job scraping completed and saved to CSV.")
    return all_job_listings

