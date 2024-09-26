from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import pandas as pd

# Configuration
CPANEL_URL = 'https://sebatsolutions.com:2083'
CPANEL_USERNAME = 'sebatsab'
CPANEL_PASSWORD = 'Alephtav@2024(_)'


# Global Variables
errored_users = []
registered_users = []

def setup_driver() -> webdriver.Chrome:
    """Set up the Selenium WebDriver using a context manager."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-gpu")
    # Uncomment the following line to run in headless mode (without opening a browser window)
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)   
    return driver


def generate_email_user(full_name):
    """Generate email username from full name."""
    return full_name.lower().replace(' ', '')


def login_to_cpanel(driver, wait):
    """Log in to cPanel."""
    driver.get(CPANEL_URL)
    wait.until(EC.presence_of_element_located((By.ID, 'user')))
    driver.find_element(By.ID, 'user').send_keys(CPANEL_USERNAME)
    driver.find_element(By.ID, 'pass').send_keys(CPANEL_PASSWORD)
    driver.find_element(By.ID, 'login_submit').click()
    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'Email Accounts')))
    print("Logged into cPanel")

def logout_of_cpanel(driver, wait):
    """Log out of cPanel."""
    try:
        user_menu = wait.until(EC.presence_of_element_located((By.ID, 'userDropdown')))
        user_menu.click()
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="logout"]'))).click()
        wait.until(EC.presence_of_element_located((By.ID, 'login_submit')))
        print("Logged out of cPanel")
    except TimeoutException:
        print("Logout button not found, continuing...")

def navigate_to_email_accounts(driver, wait):
    """Navigate to the Email Accounts section."""
    try:
        email_accounts_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'User Manager')))
        email_accounts_link.click()
        print("Navigated to Accounts section")
    except TimeoutException:
        print("Email Accounts link not found")

def navigate_to_create(driver, wait):
    """Navigate to the Create Email Account section."""
    try:
        create_button = wait.until(EC.presence_of_element_located((By.ID, 'btnCreate')))
        create_button.click()
        driver.find_element(By.ID, 'send-invite-off').click()
        print("Navigated to Create Email Account section")
    except TimeoutException:
        print("Create Email Account button not found")

def clear_fields(driver):
    """Clear all fields in the form."""
    driver.find_element(By.ID, 'full-name').clear()
    driver.find_element(By.ID, 'username').clear()
    driver.find_element(By.ID, 'password').clear()
    driver.find_element(By.ID, 'password-confirm').clear()

def create_email_account(driver, wait, full_name, email_user, email_password, email_confirm_password):
    """Create an email account with provided details."""
    try:
        driver.find_element(By.ID, 'send-invite-off').click()
        sleep(3)
        driver.find_element(By.ID, 'full-name').send_keys(full_name)
        driver.find_element(By.ID, 'username').send_keys(email_user)
        driver.find_element(By.ID, 'password').send_keys(email_password)
        driver.find_element(By.ID, 'password-confirm').send_keys(email_confirm_password)
        
        toggle_switch = driver.find_element(By.ID, 'toggleEmail')
        toggle_class = toggle_switch.get_attribute('class')

        if 'switch-off' in toggle_class:
            toggle_switch.click()
            print("Toggle switch was off and is now clicked to turn on.")
        else:
            print("Toggle switch is already on.")
        
        sleep(3)
        driver.find_element(By.ID, 'btn-create').click()
        print(f"Created email account: {email_user}")
        registered_users.append({'email_accounts': email_user})
    except TimeoutException:
        handle_error("Timed out", full_name, email_user, email_password)
    except NoSuchElementException:
        handle_error("Element not found", full_name, email_user, email_password)
    except ElementClickInterceptedException:
        handle_error("Element click intercepted", full_name, email_user, email_password)
    except Exception as e:
        handle_error(str(e), full_name, email_user, email_password)

def handle_error(error_message, full_name, email_user, email_password):
    """Handle errors by logging them and clearing fields."""
    print(f"An error occurred: {error_message}")
    errored_users.append({'full_name': full_name, 'email_user': email_user, 'email_password': email_password, 'error': error_message})
    clear_fields(driver)

def export_error_logs():
    """Export errored users and registered users to Excel files."""
    if errored_users:
        errored_df = pd.DataFrame(errored_users)
        registered_df = pd.DataFrame(registered_users)
        errored_df.to_excel('errored_users.xlsx', index=False)
        registered_df.to_excel('registered_users.xlsx', index=False)
        print("Error logs exported successfully.")
    else:
        print("No errors to log.")

def create_email(company_name):
    # Execute the command using subprocess
    try:
      # Initialize
      global driver, wait
      driver = setup_driver()
      wait = WebDriverWait(driver, 10)


      # Log in to cPanel
      login_to_cpanel(driver, wait)

      # Navigate to Email Accounts and Create section
      navigate_to_email_accounts(driver, wait)
      navigate_to_create(driver, wait)

      account_email = generate_email_user(company_name)
      create_email_account(driver, wait, company_name, account_email,'company@7jobs12','company@7jobs12')
      sleep(3)
          
      # Export error logs if any
      export_error_logs()

      # Log out and close browser
      logout_of_cpanel(driver, wait)
      driver.quit()

      full_email = account_email+'@sebatsolutions.com'
      return full_email
    except Exception as e:
      # Code that runs if an exception occurs
      print(f"An error occurred while creating email: {e}")
      return None
