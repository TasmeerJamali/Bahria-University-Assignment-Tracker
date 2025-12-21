"""
Browser Automation Module
Handles CMS login, LMS navigation, and assignment scraping.
"""

import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class BUAutomation:
    """Handles all browser automation for Bahria University CMS/LMS."""
    
    CMS_LOGIN_URL = "https://cms.bahria.edu.pk/Logins/Student/Login.aspx"
    CMS_DASHBOARD_URL = "https://cms.bahria.edu.pk/Sys/Student/Dashboard.aspx"
    LMS_ASSIGNMENTS_URL = "https://lms.bahria.edu.pk/Student/Assignments.php"
    
    INSTITUTE_OPTIONS = {
        "Karachi Campus": "Karachi Campus",
        "Islamabad E-8 Campus": "Islamabad E-8 Campus",
        "Lahore Campus": "Lahore Campus",
        "Health Sciences Campus": "Health Sciences Campus"
    }
    
    def __init__(self, headless=False, progress_callback=None):
        """Initialize the automation with browser options."""
        self.driver = None
        self.headless = headless
        self.progress_callback = progress_callback or (lambda msg: None)
        
    def _update_progress(self, message):
        """Update progress status."""
        self.progress_callback(message)
        
    def start_browser(self):
        """Start Chrome browser with configured options."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        else:
            # Run minimized
            options.add_argument("--start-minimized")
            
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Suppress logging
        options.add_argument("--log-level=3")
        
        self._update_progress("Starting browser...")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            raise Exception(f"Failed to start browser: {str(e)}")
    
    def login_to_cms(self, enrollment, password, institute):
        """Login to CMS with provided credentials."""
        self._update_progress("Navigating to CMS login page...")
        
        try:
            self.driver.get(self.CMS_LOGIN_URL)
            wait = WebDriverWait(self.driver, 15)
            
            # Wait for login form
            enrollment_field = wait.until(
                EC.presence_of_element_located((By.ID, "BodyPH_tbEnrollment"))
            )
            
            self._update_progress("Entering credentials...")
            
            # Fill enrollment
            enrollment_field.clear()
            enrollment_field.send_keys(enrollment)
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "BodyPH_tbPassword")
            password_field.clear()
            password_field.send_keys(password)
            
            # Select institute
            institute_dropdown = Select(
                self.driver.find_element(By.ID, "BodyPH_ddlInstituteID")
            )
            institute_dropdown.select_by_visible_text(institute)
            
            # Ensure Student role is selected
            role_dropdown = Select(
                self.driver.find_element(By.ID, "BodyPH_ddlSubUserType")
            )
            role_dropdown.select_by_visible_text("Student")
            
            # Click Sign In
            self._update_progress("Signing in...")
            sign_in_btn = self.driver.find_element(By.ID, "BodyPH_btnLogin")
            sign_in_btn.click()
            
            # Wait for dashboard to load
            time.sleep(3)
            
            # Check if login was successful
            if "Dashboard" in self.driver.current_url:
                self._update_progress("Login successful!")
                return True
            else:
                # Check for error message
                try:
                    error_elem = self.driver.find_element(By.CLASS_NAME, "alert-danger")
                    raise Exception(f"Login failed: {error_elem.text}")
                except NoSuchElementException:
                    raise Exception("Login failed: Unknown error")
                    
        except TimeoutException:
            raise Exception("Login page took too long to load")
        except Exception as e:
            raise Exception(f"Login error: {str(e)}")
    
    def navigate_to_lms(self):
        """Navigate from CMS Dashboard to LMS."""
        self._update_progress("Navigating to LMS...")
        
        try:
            wait = WebDriverWait(self.driver, 20)
            
            # Store current window handle
            original_window = self.driver.current_window_handle
            original_windows = set(self.driver.window_handles)
            
            # Find and click "Go To LMS" link
            lms_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Go To LMS')]"))
            )
            lms_link.click()
            
            # Wait for new window to open
            self._update_progress("Waiting for LMS to open...")
            time.sleep(8)
            
            # Check if new window opened
            new_windows = set(self.driver.window_handles) - original_windows
            
            if new_windows:
                # Switch to the new window
                new_window = new_windows.pop()
                self.driver.switch_to.window(new_window)
                self._update_progress("Switched to LMS window...")
                time.sleep(5)
            
            # Verify we're on LMS (check current tab)
            if "lms.bahria.edu.pk" in self.driver.current_url:
                self._update_progress("LMS loaded successfully!")
                return True
            else:
                # Maybe it redirected in same window, wait more
                time.sleep(5)
                if "lms.bahria.edu.pk" in self.driver.current_url:
                    self._update_progress("LMS loaded successfully!")
                    return True
                raise Exception("Failed to navigate to LMS")
                
        except TimeoutException:
            raise Exception("Could not find 'Go To LMS' button")
        except Exception as e:
            raise Exception(f"LMS navigation error: {str(e)}")
    
    def scrape_assignments(self):
        """Scrape all assignments from all courses using parallel HTTP requests (TURBO MODE)."""
        self._update_progress("Loading assignments page...")
        
        try:
            import requests
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from bs4 import BeautifulSoup
            import re
            
            # Navigate to Assignments page first to get cookies
            self.driver.get(self.LMS_ASSIGNMENTS_URL)
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.ID, "courseId")))
            
            # Extract session cookies from Selenium
            cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
            
            # Get semester ID and courses from dropdown
            semester_select = self.driver.find_element(By.ID, "semesterId")
            semester_id = Select(semester_select).first_selected_option.get_attribute("value")
            
            course_dropdown = self.driver.find_element(By.ID, "courseId")
            course_select = Select(course_dropdown)
            courses = [(opt.get_attribute("value"), opt.text) 
                      for opt in course_select.options 
                      if opt.get_attribute("value")]
            
            self._update_progress(f"⚡ Turbo Mode: Fetching {len(courses)} courses...")
            
            # Create session with cookies
            session = requests.Session()
            session.cookies.update(cookies)
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                'Referer': 'https://lms.bahria.edu.pk/Student/Assignments.php'
            })
            
            all_assignments = []
            
            def fetch_course_assignments(course_info):
                """Fetch assignments for a single course."""
                course_id, course_name = course_info
                try:
                    url = f"https://lms.bahria.edu.pk/Student/Assignments.php?s={semester_id}&oc={course_id}"
                    response = session.get(url, timeout=15)
                    
                    if response.status_code != 200:
                        return []
                    
                    # Parse HTML with regex (faster than BeautifulSoup for simple parsing)
                    html = response.text
                    assignments = []
                    
                    # Find all table rows
                    row_pattern = r'<tr[^>]*>(.*?)</tr>'
                    rows = re.findall(row_pattern, html, re.DOTALL)
                    
                    for row in rows:
                        # Skip header rows
                        if '<th' in row:
                            continue
                        
                        # Extract cells
                        cell_pattern = r'<td[^>]*>(.*?)</td>'
                        cells = re.findall(cell_pattern, row, re.DOTALL)
                        
                        if len(cells) < 8:
                            continue
                        
                        # Clean HTML tags from cell content
                        def clean_html(text):
                            return re.sub(r'<[^>]+>', '', text).strip()
                        
                        title = clean_html(cells[1])
                        deadline = clean_html(cells[7])
                        has_submission = '<a' in cells[3]
                        is_overdue = 'Deadline Exceeded' in cells[6]
                        
                        if title:
                            assignments.append({
                                "course": course_name,
                                "title": title,
                                "deadline": deadline,
                                "status": "Submitted" if has_submission else "Not Submitted",
                                "is_overdue": is_overdue
                            })
                    
                    return assignments
                except Exception as e:
                    return []
            
            # Fetch all courses in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(fetch_course_assignments, course): course for course in courses}
                
                for future in as_completed(futures):
                    course = futures[future]
                    try:
                        result = future.result()
                        all_assignments.extend(result)
                    except Exception:
                        pass
            
            # Add days_left calculation
            for a in all_assignments:
                deadline_date = self._parse_deadline(a.get('deadline', ''))
                a['deadline_date'] = deadline_date
                a['days_left'] = self._calculate_days_left(deadline_date)
            
            self._update_progress(f"⚡ Found {len(all_assignments)} assignments!")
            return all_assignments
            
        except Exception as e:
            raise Exception(f"Failed to scrape assignments: {str(e)}")
    
    def _parse_assignment_table(self, course_name):
        """Parse the assignments table for current course."""
        assignments = []
        
        try:
            # Find table rows
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 8:
                        continue
                    
                    # Extract data
                    title = cells[1].text.strip()
                    deadline_text = cells[7].text.strip()
                    
                    # Check submission status
                    try:
                        cells[3].find_element(By.TAG_NAME, "a")
                        status = "Submitted"
                    except NoSuchElementException:
                        status = "Not Submitted"
                    
                    # Check if deadline exceeded
                    action_text = cells[6].text.strip() if len(cells) > 6 else ""
                    if "Deadline Exceeded" in action_text:
                        is_overdue = True
                    else:
                        is_overdue = False
                    
                    # Parse deadline
                    deadline_date = self._parse_deadline(deadline_text)
                    days_left = self._calculate_days_left(deadline_date)
                    
                    assignment = {
                        "course": course_name,
                        "title": title,
                        "deadline": deadline_text,
                        "deadline_date": deadline_date,
                        "status": status,
                        "days_left": days_left,
                        "is_overdue": is_overdue
                    }
                    assignments.append(assignment)
                    
                except Exception:
                    continue
                    
        except Exception:
            pass
            
        return assignments
    
    def _parse_deadline(self, deadline_text):
        """Parse deadline text into datetime object."""
        try:
            # Format: "25 September 2025-11:00 pm"
            deadline_text = deadline_text.replace("-", " ")
            formats = [
                "%d %B %Y %I:%M %p",
                "%d %b %Y %I:%M %p",
                "%d %B %Y",
                "%d %b %Y"
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(deadline_text, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def _calculate_days_left(self, deadline_date):
        """Calculate days remaining until deadline."""
        if not deadline_date:
            return None
        
        now = datetime.now()
        delta = deadline_date - now
        return delta.days
    
    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
    def get_lms_url(self):
        """Get the LMS URL for opening in browser."""
        return "https://lms.bahria.edu.pk/Student/Dashboard.php"
