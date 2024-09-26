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

from model.job_model import Job

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
    job_apply_url: Optional[str] = None
    posted_time: Optional[str] = None
    salary: Optional[str] = None
    skills: Optional[List[str]] = None

def setup_driver() -> webdriver.Chrome:
    """Set up a new instance of Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-gpu")
    # Uncomment the following line to run in headless mode (without opening a browser window)
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)   
    return driver

def scrape_job_detail(job_url: str) -> JobModel:
    """Scrape detailed job information from a job detail page using a new driver instance."""
    detail_driver = setup_driver()  # Create a new WebDriver instance for job detail scraping
    try:
        # Open the job detail page in the new driver
        detail_driver.get(job_url)
        logging.info(f"Accessing job URL: {job_url}")

        # Set window size to ensure all content is visible
        detail_driver.set_window_size(1920, 1080)

        # Wait until the job details are fully loaded
        WebDriverWait(detail_driver, 120).until(
            lambda detail_driver: detail_driver.execute_script('return document.readyState') == 'complete'
        )

        # Additional wait time for dynamic elements to load
        time.sleep(5)

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(detail_driver.page_source, 'html.parser')

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

    finally:
        # Close the secondary driver after scraping
        detail_driver.quit()

    # Return an empty JobModel if an error occurs
    return JobModel()

def save_jobs_to_csv(job_listing: List[Job]):
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
      
        for job in job_listing:
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

    logging.info(f"Saved jobs from all jobs to {filename}.")

def scrape_job(driver: webdriver.Chrome, progress_callback=None) -> List[JobModel]:
    """Scrape job listings from a detail page and filter by 'Since Yesterday'."""
    job_list = []
    try:
        driver.get('https://ethiojobs.net/jobs')
        logging.info(f"Accessing sector URL: https://ethiojobs.net/jobs")

        # Wait for the page to fully load
        WebDriverWait(driver, 120).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(10)  # Additional wait to handle splash screen or dynamic loading elements

        try:
            # Locate the sidebar container using its ID
            sidebar_container = driver.find_element(By.ID, 'sidebar')
            logging.info("Located the sidebar container.")

            # Scroll to the sidebar if necessary (helpful in case of any visibility issues)
            driver.execute_script("arguments[0].scrollIntoView(true);", sidebar_container)
            time.sleep(2)  # Small delay to ensure the sidebar is in view

            # Expand the 'Posted Within' section if it is not expanded
            posted_within_section = sidebar_container.find_element(By.XPATH, './/p[contains(text(), "Posted Within")]/ancestor::div[contains(@class, "MuiAccordion-root")]')
            if 'Mui-expanded' not in posted_within_section.get_attribute('class'):
                posted_within_section.click()
                logging.info("Expanded 'Posted Within' section.")
            
            # Wait for the section to expand and display the input field specifically in the 'Posted Within' section
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.XPATH, './/div[contains(@class, "MuiAccordionDetails-root") and .//input[@id=":r1k:"]]'))
            )

            # Locate and click on the input field within the 'Posted Within' section to show dropdown options
            posted_within_input = sidebar_container.find_element(By.XPATH, './/div[contains(@class, "MuiAccordionDetails-root") and .//input[@id=":r1k:"]]//input[@type="text"]')
            
            # Ensure the input is visible and clickable
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(posted_within_input))

            # Use JavaScript click to ensure proper interaction
            driver.execute_script("arguments[0].click();", posted_within_input)
            logging.info("Clicked on the 'Posted Within' input field to open dropdown.")

            # Type 'Since Yesterday' into the input field to trigger the dynamic dropdown
            posted_within_input.send_keys("Since Yesterday")
            logging.info("Typed 'Since Yesterday' into the input field.")

            # Now, wait for the "Since Yesterday" option to appear dynamically
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.XPATH, '//span[contains(text(), "Since Yesterday")]'))
            )

            # Search for the "Since Yesterday" option dynamically in the dropdown
            try:
                since_yesterday_option = driver.find_element(By.XPATH, '//div[@role="presentation"]//ul//*[contains(text(), "Since Yesterday")]')
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(since_yesterday_option))
                driver.execute_script("arguments[0].click();", since_yesterday_option)
                logging.info("Selected 'Since Yesterday' filter.")
            except NoSuchElementException:
                logging.warning("The 'Since Yesterday' option is not present in the dropdown.")
                return  # Exit if the option is not found

            # Wait for the page to reload after applying filter
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-2.mui-style-isbt42'))
            )
            time.sleep(5)  # Additional wait to ensure jobs are filtered correctly

        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Error while applying 'Since Yesterday' filter: {e}")
            return  # Exit function if the filter application fails

        # Pagination loop
        total_jobs = 0  # Initialize total job counter
        while True:
            # Start scraping job cards
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.select('.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation1.jss2.mui-style-aoeo82')
            total_jobs += len(job_cards)  # Increment total job count

            for index, card in enumerate(job_cards):
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
                    job_details = scrape_job_detail(job_apply_url) if job_apply_url else JobModel()

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
                    job_list.append(job)

                    # Update the progress bar
                    if progress_callback:
                        progress = (index + 1) / total_jobs
                        progress_callback(progress)
                except (StaleElementReferenceException, NoSuchElementException) as e:
                    logging.error(f"Error while parsing job card: {e}")
                except Exception as e:
                    logging.error(f"An unexpected error occurred while scraping job card: {e}")

            logging.info(f"Scraped {len(job_list)} jobs from the current page")

            # Check if there is a next page by looking for the next page number button
            try:
                # Locate the active page number
                active_page_elem = driver.find_element(By.XPATH, '//button[@aria-current="true"]')

                # Determine the next page number
                next_page_number = str(int(active_page_elem.text) + 1)

                # Locate the next page button by its aria-label attribute
                next_page_button = driver.find_element(By.XPATH, f'//button[@aria-label="Go to page {next_page_number}"]')

                # Check if the button is enabled and clickable
                if next_page_button.is_enabled():
                    driver.execute_script("arguments[0].click();", next_page_button)
                    logging.info(f"Navigating to page {next_page_number}.")
                    # Wait for the next page to load
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-2.mui-style-isbt42'))
                    )
                    time.sleep(5)  # Additional wait for content to load
                else:
                    break  # Exit loop if the next page button is not enabled
            except NoSuchElementException:
                logging.info("No more pages to navigate.")
                break  # Exit loop if no next page button is found

    except TimeoutException as e:
        logging.error(f"Timeout while waiting for elements to load: {e}")
    except Exception as e:
        logging.error(f"An error occurred while accessing the sector page: {e}")

    # Process the collected job_list as needed
    logging.info(f"Total jobs scraped: {len(job_list)}")
    return job_list

def scrape_ethio_jobs(progress_callback=None) -> List[Job]:
    """Scrape job listings from ethijob and return a list of JobModel instances."""
    job_listings = []
    logging.info("Starting job scraping by category URLs...")

    driver = setup_driver()


    job_listings = scrape_job(driver, progress_callback)
    # Quit the WebDriver
    driver.quit()

    # Collect job details into the list
    all_job_listings = []
   
    for job in job_listings:
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
