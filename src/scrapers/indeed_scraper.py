import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

def initialize_driver():
    options = uc.ChromeOptions()
    options.headless = False  # Set to False to see browser actions
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)
    return driver

def handle_captcha(driver):
    print("CAPTCHA detected. Please solve it manually.")
    while True:
        input("Press Enter after solving the CAPTCHA and verifying that the page has loaded completely.")
        try:
            # Check if CAPTCHA is still present
            captcha_present = driver.find_elements(By.ID, "challenge-form")
            if not captcha_present:
                print("CAPTCHA solved.")
                break
        except:
            break

def extract_jobs(driver):
    job_listings = []
    try:
        # Wait for the job results to load
        main_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#mosaic-provider-jobcards"))
        )

        # Find all job cards within the results
        job_cards = main_element.find_elements(By.CSS_SELECTOR, ".cardOutline")
        
        for job_card in job_cards:
            try:
                time.sleep(random.uniform(2, 5))  # Random delay to mimic human behavior

                # Extract job title
                job_title = job_card.find_element(By.CSS_SELECTOR, "h2.jobTitle > a span").text
                
                # Extract company name
                company_name = job_card.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']").text
                
                # Extract job location
                location = job_card.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']").text
                
                # Extract job description
                description_element = job_card.find_element(By.CSS_SELECTOR, ".css-9446fg")
                job_description = description_element.text if description_element else "N/A"
                
                job_listings.append({
                    "Job Title": job_title,
                    "Company Name": company_name,
                    "Location": location,
                    "Description": job_description
                })
                
            except Exception as e:
                print(f"Error extracting job details: {e}")

    except Exception as e:
        print(f"Error finding job results container: {e}")

    return job_listings

def main():
    driver = initialize_driver()
    
    URL = "https://www.indeed.com/jobs?q=Software+Engineer&l=Remote"
    driver.get(URL)
    
    time.sleep(random.uniform(5, 10))
    
    # Handle CAPTCHA manually if encountered
    handle_captcha(driver)
    
    jobs = extract_jobs(driver)
    
    for index, job in enumerate(jobs):
        print(f"Job {index + 1}:")
        print(f"Title: {job['Job Title']}")
        print(f"Company: {job['Company Name']}")
        print(f"Location: {job['Location']}")
        print(f"Description: {job['Description']}")
        print("=" * 40)
    
    driver.quit()

if __name__ == "__main__":
    main()
