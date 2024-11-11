"""
Harvard Course Scraper

This script scrapes course information from Harvard's course catalog (beta.my.harvard.edu).
It extracts course codes and term information, formatting them as 'code/term' pairs.
For example: 'HIST-LIT90HA/2025-Fall'

The information is stored at course_lines.txt

The final HTTP response before termination is stored at final_response_before_stop.json

This information will be used in another code file to construct the course URL.

For example: 'https://beta.my.harvard.edu/course/SYSBIO350/2025-Spring/001'
"""

import requests
import json
import time
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import os

def get_initial_data(base_url, headers):
    """Get initial data to determine total number of pages."""
    try:
        initial_response = requests.get(f"{base_url}&page=1", headers=headers)
        initial_response.raise_for_status()
        initial_data = initial_response.json()
        total_hits = initial_data.get('total_hits', 0)
        return total_hits
    except Exception as e:
        print(f"Error getting initial data: {e}")
        return 0

def save_response_data(data, filename):
    """Save response data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_course_info(html_content):
    """Extract course codes and term information from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    course_cards = soup.find_all('div', class_='bg-white')
    
    course_lines = []
    for card in course_cards:
        # Extract course code by finding the tooltip span first
        tooltip_span = card.find('span', class_='hs-tooltip-content', string=re.compile(r'Subject.*Catalog.*Number'))
        course_code = ''
        if tooltip_span:
            code_span = tooltip_span.find_previous_sibling('span', class_='hs-tooltip-toggle')
            if code_span:
                # Remove all spaces from course code
                course_code = code_span.text.strip().replace(' ', '')
        
        # Extract term information
        term_div = card.find('div', class_='flex gap-x-2 items-center')
        term_text = ''
        if term_div:
            term_span = term_div.find('span')
            if term_span:
                # Replace space with hyphen in term
                term_text = term_span.text.strip().replace(' ', '-')
        
        if course_code and term_text:
            course_lines.append(f"{course_code}/{term_text}")
    
    return course_lines

def load_existing_lines(filename):
    """Load existing course lines from file if it exists."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_course_lines(course_lines, filename, append=False):
    """Save course lines to a text file."""
    mode = 'a' if append else 'w'
    with open(filename, mode, encoding='utf-8') as f:
        for line in course_lines:
            f.write(line + '\n')

def fetch_page_data(url, headers):
    """Fetch and parse data from a single page."""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"\nError fetching the data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"\nError parsing JSON: {e}")
        return None

def scrape_harvard_courses(start_page=1, year=None, term=None):
    """
    Scrape Harvard courses for a specific academic term.
    
    Args:
        start_page (int): Starting page number for scraping
        year (str): Academic year (e.g., '2024')
        term (str): Term (e.g., 'Fall', 'Spring')
    """
    if not year or not term:
        raise ValueError("Both year and term must be specified")
        
    base_url = "https://beta.my.harvard.edu/search/?q=&sort=relevance&school=All&term=All"
    
    # Add term filter
    term_filter = f"&term={year}+{term}"
    base_url += term_filter
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }
    
    # Get initial data
    total_hits = get_initial_data(base_url, headers)
    if total_hits == 0:
        return []
    
    # Load existing lines if starting from a page > 1
    existing_lines = load_existing_lines('course_lines.txt') if start_page > 1 else []
    all_course_lines = existing_lines.copy()
    
    # Create progress bar for total courses
    pbar = tqdm(total=total_hits, desc="Scraping courses", unit="course", initial=len(existing_lines))
    print(f"Found {total_hits} total courses")
    if start_page > 1:
        print(f"Resuming with {len(existing_lines)} existing courses")
    print(f"Filtering for {year}-{term}")
    
    page = start_page
    
    while True:
        url = f"{base_url}&page={page}"
        
        # Fetch page data
        data = fetch_page_data(url, headers)

        # Process page data
        if data and 'hits' in data:
            course_lines = extract_course_info(data['hits'])
            
            if not course_lines:
                pbar.close()
                print(f"\nNo more courses found. Stopping.")
                save_response_data(data, 'final_response_before_stop.json')
                break
            
            # Update progress bar with number of new courses found
            new_courses = len(course_lines)
            pbar.update(new_courses)
            
            all_course_lines.extend(course_lines)
            
            # Add a small delay to be respectful to the server
            time.sleep(0.1)
            page += 1
        else:
            pbar.close()
            print("\nNo 'hits' found in the response. Stopping.")
            save_response_data(data, 'final_response_before_stop.json')
            break
    
    # Save results
    save_course_lines(all_course_lines, 'course_lines.txt', append=(start_page > 1))
    print(f"\nTotal courses found: {len(all_course_lines)}")
    print("All course lines saved to course_lines.txt")
    return all_course_lines

if __name__ == "__main__":
    # Edit this if it stopped prematurely
    start_page = 0
    year = "2025"  # Required: specify year
    term = "Fall"  # Required: specify term
    
    course_lines = scrape_harvard_courses(start_page=start_page, year=year, term=term)