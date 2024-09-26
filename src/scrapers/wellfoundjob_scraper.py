import requests
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL of the website
base_url = 'https://wellfound.com'
main_url = f'{base_url}/location/united-states'

class Job:
    def __init__(self, id=None, company_name=None, company_logo=None, job_title=None, job_description=None,
                 application_deadline=None, job_sector=None, job_type=None, skills=None, job_apply_type=None,
                 job_apply_url=None, salary_type=None, min_salary=None, max_salary=None, salary_currency=None,
                 salary_position=None, salary_separator=None, salary_decimals=None, experience=None, gender=None,
                 qualifications=None, career_level=None, country=None, state=None, city=None, postal_code=None,
                 full_address=None, latitude=None, longitude=None, zoom=None, unique_job_id=None, detail_url=None,
                 date_posted=None):
        self.id = id
        self.company_name = company_name
        self.company_logo = company_logo
        self.job_title = job_title
        self.job_description = job_description
        self.application_deadline = application_deadline
        self.job_sector = job_sector
        self.job_type = job_type
        self.skills = skills
        self.job_apply_type = job_apply_type
        self.job_apply_url = job_apply_url
        self.salary_type = salary_type
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.salary_currency = salary_currency
        self.salary_position = salary_position
        self.salary_separator = salary_separator
        self.salary_decimals = salary_decimals
        self.experience = experience
        self.gender = gender
        self.qualifications = qualifications
        self.career_level = career_level
        self.country = country
        self.state = state
        self.city = city
        self.postal_code = postal_code
        self.full_address = full_address
        self.latitude = latitude
        self.longitude = longitude
        self.zoom = zoom
        self.unique_job_id = unique_job_id
        self.detail_url = detail_url
        self.date_posted = date_posted

def fetch_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching the page: {e}")
        return None

def parse_html(html_content):
    try:
        return BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logger.error(f"Error parsing HTML content: {e}")
        return None

def extract_job_listings(soup):
    return soup.find_all('div', class_='styles_jobListing__PLqQ_')

def extract_job_details(job):
    try:
        job_title_elem = job.find('a', class_='styles_jobTitle___jT4l')
        location_and_compensation_elem = job.find('span', class_='styles_locationAndCompensation__vDfgW')
        date_posted_elem = job.find('span', class_='text-dark-a text-xs lowercase md:hidden')

        job_title = job_title_elem.text if job_title_elem else None
        job_url = f"{base_url}{job_title_elem['href']}" if job_title_elem else None
        location_and_compensation = location_and_compensation_elem.text.strip() if location_and_compensation_elem else None
        date_posted = date_posted_elem.text.strip() if date_posted_elem else None

        job_description = scrape_job_description(job_url) if job_url else {}

        job = Job(
            job_title=job_title,
            detail_url=job_url,
            job_description=job_description.get('description'),
            company_name=job_description.get('company_name'),
            job_type=job_description.get('job_type'),
            country='United States',  # Assuming jobs are in the US based on the main URL
            city=job_description.get('job_location'),
            salary_type='Annual',  # Assuming salary type is annual, can be adjusted as needed
            min_salary=job_description.get('min_salary'),
            max_salary=job_description.get('max_salary'),
            salary_currency='USD',  # Assuming salary is in USD, can be adjusted as needed
            date_posted=date_posted
        )

        return job
    except Exception as e:
        logger.error(f"Error extracting job details: {e}")
        return None

def scrape_job_description(url):
    html_content = fetch_page(url)
    if not html_content:
        return {}

    soup = parse_html(html_content)
    if not soup:
        return {}

    try:
        details = {}

        # Job description
        description_elem = soup.find('div', id='job-description')
        details['description'] = description_elem.text.strip() if description_elem else None

        # Company name
        company_name_elem = soup.find('a', class_='text-m font-bold text-black underline')
        details['company_name'] = company_name_elem.text.strip() if company_name_elem else None

        # Job position
        job_position_elem = soup.find('h1', class_='inline text-xl font-semibold text-black')
        details['job_position'] = job_position_elem.text.strip() if job_position_elem else None

        # Date posted
        date_posted_elem = soup.find('div', class_='mb-4 mt-1 text-sm font-medium text-gray-800')
        details['date_posted'] = date_posted_elem.text.strip() if date_posted_elem else None

        # Job location
        job_location_elem = soup.find('span', string='Job Location')
        if job_location_elem:
            job_location_elem = job_location_elem.find_next('div')
            details['job_location'] = job_location_elem.text.strip() if job_location_elem else None
        else:
            details['job_location'] = None

        # Job type
        job_type_elem = soup.find('span', string='Job Type')
        if job_type_elem:
            job_type_elem = job_type_elem.find_next('p')
            details['job_type'] = job_type_elem.text.strip() if job_type_elem else None
        else:
            details['job_type'] = None

        # Visa sponsorship
        visa_sponsorship_elem = soup.find('span', string='Visa Sponsorship')
        if visa_sponsorship_elem:
            visa_sponsorship_elem = visa_sponsorship_elem.find_next('p')
            details['visa_sponsorship'] = visa_sponsorship_elem.text.strip() if visa_sponsorship_elem else None
        else:
            details['visa_sponsorship'] = None

        # Hires remotely
        hires_remotely_elem = soup.find('span', string='Hires remotely')
        if hires_remotely_elem:
            hires_remotely_elem = hires_remotely_elem.find_next('div')
            details['hires_remotely'] = hires_remotely_elem.text.strip() if hires_remotely_elem else None
        else:
            details['hires_remotely'] = None

        # Relocation
        relocation_elem = soup.find('span', string='Relocation')
        if relocation_elem:
            relocation_elem = relocation_elem.find_next('span', class_='flex items-center')
            details['relocation'] = relocation_elem.text.strip() if relocation_elem else None
        else:
            details['relocation'] = None

        # Hiring contact
        hiring_contact_elem = soup.find('span', string='Hiring contact')
        if hiring_contact_elem:
            hiring_contact_elem = hiring_contact_elem.find_next('p')
            details['hiring_contact'] = hiring_contact_elem.text.strip() if hiring_contact_elem else None
        else:
            details['hiring_contact'] = None

        # Salary details
        salary_text = soup.find(string=lambda x: 'Salary' in x if x else False)
        if salary_text:
            salary_elem = salary_text.find_next('p')
            salary = salary_elem.text.strip() if salary_elem else None
            if salary and ' - ' in salary:
                min_salary, max_salary = salary.split(' - ')
                details['min_salary'] = min_salary.replace('$', '').replace(',', '').strip()
                details['max_salary'] = max_salary.replace('$', '').replace(',', '').strip()
            else:
                details['min_salary'] = salary.replace('$', '').replace(',', '').strip()
                details['max_salary'] = details['min_salary']
        else:
            details['min_salary'] = None
            details['max_salary'] = None

        return details

    except Exception as e:
        logger.error(f"Error extracting job description: {e}")
        return {}

def main():
    html_content = fetch_page(main_url)
    if html_content:
        soup = parse_html(html_content)
        if soup:
            job_listings = extract_job_listings(soup)
            jobs = []
            for job in job_listings:
                job_details = extract_job_details(job)
                if job_details:
                    jobs.append(job_details)

            # Print job details
            for job in jobs:
                print(f"Job Title: {job.job_title}")
                print(f"URL: {job.detail_url}")
                print(f"Location: {job.city}")
                print(f"Date Posted: {job.date_posted}")
                print(f"Company Name: {job.company_name}")
                print(f"Job Type: {job.job_type}")
                print(f"Salary: {job.min_salary} - {job.max_salary}")
                print(f"Description: {job.job_description}")
                print('-' * 40)

if __name__ == "__main__":
    main()
