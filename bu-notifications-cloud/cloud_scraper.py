"""
Cloud Scraper for GitHub Actions
Autonomous LMS scraping for all registered students.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from html.parser import HTMLParser


# API Configuration
API_BASE = os.environ.get("API_URL", "https://buassignmenttracker.pythonanywhere.com")


class AssignmentParser(HTMLParser):
    """Parse assignment HTML from LMS."""
    
    def __init__(self):
        super().__init__()
        self.assignments = []
        self.current_assignment = {}
        self.in_row = False
        self.current_cell = 0
        self.cell_data = ""
        
    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.in_row = True
            self.current_cell = 0
            self.current_assignment = {}
        elif tag == "td" and self.in_row:
            self.cell_data = ""
            
    def handle_endtag(self, tag):
        if tag == "td" and self.in_row:
            self.current_cell += 1
            data = self.cell_data.strip()
            
            if self.current_cell == 1:
                self.current_assignment["title"] = data
            elif self.current_cell == 2:
                self.current_assignment["status"] = data
            elif self.current_cell == 3:
                self.current_assignment["deadline"] = data
                
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_assignment.get("title"):
                self.assignments.append(self.current_assignment)
                
    def handle_data(self, data):
        if self.in_row:
            self.cell_data += data


def calculate_days_left(deadline_str: str) -> Optional[int]:
    """Calculate days until deadline."""
    formats = [
        "%A, %d %B %Y, %I:%M %p",
        "%d %B %Y, %I:%M %p",
        "%Y-%m-%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            deadline = datetime.strptime(deadline_str.strip(), fmt)
            delta = deadline - datetime.now()
            return delta.days
        except ValueError:
            continue
    
    return None


def scrape_student(enrollment: str, password: str, institute: str) -> Dict:
    """Scrape assignments for a single student."""
    
    print(f"  Scraping: {enrollment}")
    
    # Chrome options for headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        
        # Step 1: CMS Login
        cms_url = "https://cms.bahria.edu.pk/Logins/Student/Login.aspx"
        driver.get(cms_url)
        time.sleep(2)
        
        # Fill login form
        driver.find_element(By.ID, "BodyPH_tbEnrollment").send_keys(enrollment)
        driver.find_element(By.ID, "BodyPH_tbPassword").send_keys(password)
        
        # Select institute
        institute_dropdown = Select(driver.find_element(By.ID, "BodyPH_ddlInstituteID"))
        for option in institute_dropdown.options:
            if institute.lower() in option.text.lower():
                option.click()
                break
        
        # Click login
        driver.find_element(By.ID, "BodyPH_btnLogin").click()
        time.sleep(3)
        
        # Check login success
        if "Login.aspx" in driver.current_url:
            return {"error": "Login failed", "enrollment": enrollment}
        
        # Step 2: Navigate to LMS
        lms_link = driver.find_element(By.XPATH, "//a[contains(@href, 'LMS')]")
        lms_link.click()
        time.sleep(3)
        
        # Switch to LMS window
        windows = driver.window_handles
        if len(windows) > 1:
            driver.switch_to.window(windows[-1])
        
        time.sleep(2)
        
        # Step 3: Get assignments page
        assignments_url = "https://lms.bahria.edu.pk/Student/Assignment.aspx"
        driver.get(assignments_url)
        time.sleep(3)
        
        # Wait for dropdown
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "courseId"))
        )
        
        # Get cookies for HTTP requests
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        session = requests.Session()
        for name, value in cookies.items():
            session.cookies.set(name, value)
        
        # Get course options
        course_dropdown = Select(driver.find_element(By.ID, "courseId"))
        course_options = [(opt.get_attribute("value"), opt.text) 
                         for opt in course_dropdown.options if opt.get_attribute("value")]
        
        all_assignments = []
        
        # Fetch assignments for each course
        for course_id, course_name in course_options:
            try:
                url = f"https://lms.bahria.edu.pk/Student/Assignment.aspx?cid={course_id}"
                response = session.get(url, timeout=15)
                
                if response.status_code == 200:
                    parser = AssignmentParser()
                    parser.feed(response.text)
                    
                    for a in parser.assignments:
                        a["course"] = course_name
                        a["days_left"] = calculate_days_left(a.get("deadline", ""))
                        all_assignments.append(a)
                        
            except Exception as e:
                print(f"    Error fetching {course_name}: {e}")
        
        return {
            "enrollment": enrollment,
            "assignments": all_assignments,
            "scraped_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e), "enrollment": enrollment}
        
    finally:
        if driver:
            driver.quit()


def sync_to_api(enrollment: str, assignments: List[Dict]) -> bool:
    """Upload assignments to cloud API."""
    try:
        response = requests.post(
            f"{API_BASE}/api/sync",
            json={"enrollment": enrollment, "assignments": assignments},
            timeout=30
        )
        return response.status_code == 200
    except Exception as e:
        print(f"    Sync error: {e}")
        return False


def get_auto_sync_students() -> List[Dict]:
    """Get list of students with auto-sync enabled."""
    # API key for security
    API_KEY = os.environ.get("API_KEY", "bu-tracker-secret-2024")
    
    try:
        response = requests.get(
            f"{API_BASE}/api/students/autosync",
            params={"key": API_KEY},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("students", [])
        else:
            print(f"API returned {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error fetching students: {e}")
    return []


def main():
    """Main entry point for cloud scraping."""
    print("=" * 60)
    print("BU Assignment Tracker - Autonomous Cloud Scraper")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    # Get students with auto-sync enabled
    students = get_auto_sync_students()
    print(f"Found {len(students)} students with auto-sync enabled")
    
    if not students:
        print("No students to process.")
        return
    
    success_count = 0
    error_count = 0
    
    for student in students:
        enrollment = student.get("enrollment")
        password = student.get("password")  # Decrypted by API
        institute = student.get("institute", "Karachi Campus")
        
        if not enrollment or not password:
            print(f"  Skipping {enrollment}: missing credentials")
            error_count += 1
            continue
        
        # Scrape
        result = scrape_student(enrollment, password, institute)
        
        if "error" in result:
            print(f"  ❌ {enrollment}: {result['error']}")
            error_count += 1
        else:
            assignments = result.get("assignments", [])
            print(f"  ✓ {enrollment}: {len(assignments)} assignments")
            
            # Sync to API
            if sync_to_api(enrollment, assignments):
                success_count += 1
            else:
                error_count += 1
    
    print("=" * 60)
    print(f"Completed: {success_count} success, {error_count} errors")
    print("=" * 60)


if __name__ == "__main__":
    main()
