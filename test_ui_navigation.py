"""
UI navigation test script for the POS/post-sales system.
Tests navigation paths between different apps and screens.
"""
import os
import sys
import django
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

# Main test class for UI navigation
class UINavigationTester:
    def __init__(self):
        self.setup_driver()
        self.base_url = "http://127.0.0.1:8000"
        self.login_credentials = {
            'username': 'admin',
            'password': 'adminpassword'
        }
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.screenshots_dir = "test_screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def setup_driver(self):
        """Setup Chrome webdriver with options and automatic driver installation"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Add headless option if needed
            # chrome_options.add_argument("--headless")

            # Use webdriver_manager to automatically download and setup the correct ChromeDriver
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("Chrome WebDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def check_server_running(self):
        """Check if the Django server is running before attempting tests"""
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Server is running at {self.base_url}")
                return True
            else:
                logger.error(f"Server returned status code {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Server is not running at {self.base_url}: {e}")
            print(f"\nERROR: Django server is not running at {self.base_url}")
            print("Please start the server with: python manage.py runserver\n")
            return False

    def debug_page(self, context="page"):
        """Print debug information about the current page"""
        try:
            logger.info(f"Debug information for {context}")
            logger.info(f"Current URL: {self.driver.current_url}")

            # Take a screenshot
            self.take_screenshot(f"debug_{context}")

            # Get all visible form elements
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            logger.info(f"Found {len(forms)} forms on the page")

            for i, form in enumerate(forms):
                logger.info(f"Form {i+1} action: {form.get_attribute('action')}")
                inputs = form.find_elements(By.TAG_NAME, "input")
                logger.info(f"  Form has {len(inputs)} input elements")
                for input_elem in inputs:
                    input_type = input_elem.get_attribute("type")
                    input_name = input_elem.get_attribute("name")
                    input_id = input_elem.get_attribute("id")
                    logger.info(f"  Input: type={input_type}, name={input_name}, id={input_id}")

            # Save page source for inspection
            with open(f"{self.screenshots_dir}/page_source_{context}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"Saved page source to {self.screenshots_dir}/page_source_{context}.html")

        except Exception as e:
            logger.error(f"Error getting debug info: {e}")

    def login(self):
        """Log in to the system with retry mechanism"""
        # First check if the server is running
        if not self.check_server_running():
            return False

        for attempt in range(self.max_retries):
            try:
                # First try the admin login page
                self.driver.get(f"{self.base_url}/admin/login/")
                self.debug_page("admin_login")

                # Look for the login form in different ways
                try:
                    # Try to find by form tag first
                    login_form = self.driver.find_element(By.TAG_NAME, "form")

                    # Try to find username field with various selectors
                    username_field = None
                    password_field = None

                    # Try different strategies to find the fields
                    selectors = [
                        (By.NAME, "username"),
                        (By.ID, "id_username"),
                        (By.CSS_SELECTOR, "input[type='text']"),
                        (By.XPATH, "//input[@placeholder='Username']"),
                        (By.XPATH, "//label[contains(text(), 'Username')]/following::input[1]")
                    ]

                    for by, selector in selectors:
                        try:
                            username_field = self.driver.find_element(by, selector)
                            logger.info(f"Found username field with selector: {by}={selector}")
                            break
                        except NoSuchElementException:
                            continue

                    # Similar approach for password
                    password_selectors = [
                        (By.NAME, "password"),
                        (By.ID, "id_password"),
                        (By.CSS_SELECTOR, "input[type='password']"),
                        (By.XPATH, "//input[@placeholder='Password']"),
                        (By.XPATH, "//label[contains(text(), 'Password')]/following::input[1]")
                    ]

                    for by, selector in password_selectors:
                        try:
                            password_field = self.driver.find_element(by, selector)
                            logger.info(f"Found password field with selector: {by}={selector}")
                            break
                        except NoSuchElementException:
                            continue

                    # If we found both fields, proceed with login
                    if username_field and password_field:
                        username_field.clear()
                        password_field.clear()
                        username_field.send_keys(self.login_credentials['username'])
                        password_field.send_keys(self.login_credentials['password'])

                        # Find submit button
                        try:
                            submit_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                            submit_button.click()
                        except NoSuchElementException:
                            # If no submit button, just submit the form
                            login_form.submit()

                        # Verify login success
                        try:
                            # Admin login success indicators
                            success_selectors = [
                                (By.ID, "user-tools"),
                                (By.CSS_SELECTOR, ".navbar-nav"),
                                (By.CSS_SELECTOR, ".navbar"),
                                (By.XPATH, "//a[contains(text(), 'Log out')]")
                            ]

                            for by, selector in success_selectors:
                                try:
                                    self.wait_for_element(by, selector, timeout=5)
                                    logger.info(f"Login successful, found element: {by}={selector}")
                                    return True
                                except TimeoutException:
                                    continue

                            # If we get here, login probably failed
                            logger.warning("Couldn't verify login success")
                            self.debug_page("post_login_verification")
                        except Exception as verify_error:
                            logger.error(f"Error verifying login: {verify_error}")
                    else:
                        logger.error("Couldn't find username or password field")

                except NoSuchElementException:
                    # If we couldn't find the admin login, try the regular login
                    logger.info("Admin login form not found, trying alternative login page")
                    self.driver.get(f"{self.base_url}/login/")
                    self.debug_page("regular_login")
                    # ... Rest of the login logic would be similar ...

                # If login verification failed, retry
                if attempt < self.max_retries - 1:
                    logger.warning(f"Login failed, retrying ({attempt+1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    continue

            except Exception as e:
                logger.error(f"Login error: {e}")
                self.debug_page(f"login_error_{attempt}")
                if attempt < self.max_retries - 1:
                    logger.warning(f"Retrying login ({attempt+1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    self.take_screenshot("login_error")
                    raise

        return False

    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be visible with better error handling"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"Timeout waiting for element {by}={value}")
            self.take_screenshot(f"wait_timeout_{value}")
            raise

    def take_screenshot(self, name):
        """Take a screenshot for debugging"""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{self.screenshots_dir}/screenshot_{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved as {filename}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")

    def navigate_client_to_equipment(self):
        """Test navigation from client details to their equipment"""
        try:
            # Navigate to clients list
            self.driver.get(f"{self.base_url}/clientes/")

            # Click on the first client
            clients = self.driver.find_elements(By.CSS_SELECTOR, "table.dataTable tbody tr td:first-child a")
            if not clients:
                print("✗ No clients found")
                return False

            clients[0].click()

            # Wait for client details page to load
            self.wait_for_element(By.CSS_SELECTOR, "h1.h3.mb-4")

            # Find equipment tab/section and click
            equipment_link = self.driver.find_element(By.LINK_TEXT, "Equipamentos")
            equipment_link.click()

            # Verify we're now seeing equipment
            self.wait_for_element(By.CSS_SELECTOR, "table#equipamentosTable")
            print("✓ Successfully navigated from client to their equipment")
            return True
        except Exception as e:
            print(f"✗ Error testing client to equipment navigation: {e}")
            return False

    # Add more navigation tests here:
    # - client to service requests
    # - service request to parts used
    # - inventory to suppliers
    # - etc.

    def run_all_tests(self):
        """Run all navigation tests"""
        try:
            login_success = self.login()
            if not login_success:
                logger.error("Login failed, cannot proceed with navigation tests")
                return False

            results = []
            results.append(("Client → Equipment", self.navigate_client_to_equipment()))
            # Add more tests here

            print("\n=== UI Navigation Test Results ===")
            for name, result in results:
                print(f"{name}: {'PASSED' if result else 'FAILED'}")

            overall = all(result for _, result in results)
            print(f"\nOverall Result: {'PASSED' if overall else 'FAILED'}")

            return overall
        finally:
            self.driver.quit()

if __name__ == "__main__":
    try:
        print("Starting UI Navigation Tests...")
        print("Make sure the Django development server is running at http://127.0.0.1:8000")
        tester = UINavigationTester()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Test execution failed: {e}")
        print(f"\nERROR: Test execution failed: {e}")
        print("Check the log file and screenshots directory for details.")
        sys.exit(1)
