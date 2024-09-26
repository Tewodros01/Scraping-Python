import requests
from bs4 import BeautifulSoup

# URL of the FlexJobs search page
url = "https://www.flexjobs.com/search?&remoteoptions=100%25%20Remote%20Work&careerlevel=Entry-Level&anywhereinworld=0&anywhereinus=1"

# Define headers to mimic a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Send a GET request to the URL with headers
response = requests.get(url, headers=headers)
response.raise_for_status()  # Check that the request was successful

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find the job listings in the HTML structure
job_listings = soup.find_all('div', class_='sc-14nyru2-2 fmkHkh')

# Extract the relevant information from each job listing
jobs = []
for listing in job_listings:
    job_id = listing.find('div', class_='sc-jv5lm6-0')['id']
    job_title = listing.find('a', class_='sc-jv5lm6-13').text.strip()
    job_age = listing.find('div', id=f'job-age-{job_id}').text.strip()
    job_description = listing.find('p', id=f'description-{job_id}').text.strip()

    job_salary_element = listing.find('li', id=f'salartRange-0-{job_id}')
    job_salary = job_salary_element.text.strip() if job_salary_element else 'N/A'

    job_remote_element = listing.find('li', id=f'remoteoption-0-{job_id}')
    job_remote = job_remote_element.text.strip() if job_remote_element else 'N/A'

    job_schedule_element = listing.find('li', id=f'jobschedule-0-{job_id}')
    job_schedule = job_schedule_element.text.strip() if job_schedule_element else 'N/A'

    job_location_element = listing.find('span', class_='allowed-location')
    job_location = job_location_element.text.strip() if job_location_element else 'N/A'

    jobs.append({
        'id': job_id,
        'title': job_title,
        'age': job_age,
        'description': job_description,
        'salary': job_salary,
        'remote': job_remote,
        'schedule': job_schedule,
        'location': job_location
    })

# Print the extracted job listings
for job in jobs:
    print(f"Job ID: {job['id']}")
    print(f"Title: {job['title']}")
    print(f"Posted: {job['age']}")
    print(f"Description: {job['description']}")
    print(f"Salary: {job['salary']}")
    print(f"Remote: {job['remote']}")
    print(f"Schedule: {job['schedule']}")
    print(f"Location: {job['location']}")
    print("-" * 40)
