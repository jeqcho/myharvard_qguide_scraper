"""
Harvard Course Scraper

This script scrapes course information from Harvard's course catalog (beta.my.harvard.edu).
It extracts full course URLs and saves them incrementally to course_urls.txt

Example URL: 'https://beta.my.harvard.edu/course/SYSBIO350/2025-Spring/001'
"""

import requests
import json
import time
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import os

def get_initial_data(base_url, headers):
    """Get initial data to determine total number of courses."""
    try:
        initial_response = requests.get(f"{base_url}&page=1", headers=headers)
        initial_response.raise_for_status()
        initial_data = initial_response.json()
        return initial_data.get('total_hits', 0)
    except Exception as e:
        print(f"Error getting initial data: {e}")
        return 0

def extract_course_info(html_content):
    """Extract course URLs from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    course_cards = soup.find_all('div', class_='bg-white')
    
    course_urls = []
    for card in course_cards:
        # Find link with href containing '/course/'
        course_link = card.find('a', href=re.compile(r'/course/'))
        
        if course_link and course_link.get('href'):
            url = course_link['href']
            # Convert to full URL
            if url.startswith('/'):
                url = f"https://beta.my.harvard.edu{url}"
            course_urls.append(url)
    
    return course_urls

def load_existing_urls(filename):
    """Load existing URLs from file if it exists."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_urls(urls, filename, append=False):
    """Save URLs to a text file."""
    mode = 'a' if append else 'w'
    with open(filename, mode, encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')

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
    
    # Remove existing course_urls.txt file if starting fresh (from page 1 or earlier)
    if start_page <= 1 and os.path.exists('course_urls.txt'):
        os.remove('course_urls.txt')
        print("Removed existing course_urls.txt to start afresh")
        
    base_url = "https://beta.my.harvard.edu/search/?q=&sort=relevance&school=All"
    
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
    
    # Load existing URLs if starting from a page > 1
    existing_urls = load_existing_urls('course_urls.txt') if start_page > 1 else []
    all_course_urls = existing_urls.copy()
    
    # Create progress bar for total courses
    pbar = tqdm(total=total_hits, desc="Scraping courses", unit="course", initial=len(existing_urls))
    print(f"Found {total_hits} total courses")
    if start_page > 1:
        print(f"Resuming with {len(existing_urls)} existing courses")
    print(f"Filtering for {year}-{term}")
    
    page = start_page
    consecutive_empty_pages = 0
    
    while True:
        url = f"{base_url}&page={page}"
        
        # Fetch page data
        data = fetch_page_data(url, headers)

        # Process page data
        if data and 'hits' in data:
            course_urls = extract_course_info(data['hits'])
            
            if not course_urls:
                consecutive_empty_pages += 1
                print(f"\nWarning: Page {page} returned no URLs (likely courses without detail pages)")
                
                # Only stop if we're way past expected pages or many consecutive empty pages
                expected_max_pages = (total_hits // 10) + 10  # Rough estimate with buffer
                if consecutive_empty_pages >= 10 or page > expected_max_pages:
                    pbar.close()
                    print(f"Reached stopping criteria at page {page}.")
                    break
                
                page += 1
                time.sleep(0.1)
                continue
            
            # Reset empty page counter on successful extraction
            consecutive_empty_pages = 0
            
            # Update progress and save incrementally
            pbar.update(len(course_urls))
            all_course_urls.extend(course_urls)
            save_urls(course_urls, 'course_urls.txt', append=True)
            
            # Add a small delay to be respectful to the server
            time.sleep(0.1)
            page += 1
        else:
            pbar.close()
            print(f"\nNo 'hits' found in response for page {page}. Stopping.")
            break
    
    print(f"\nTotal courses found: {len(all_course_urls)}")
    print("All course URLs saved to course_urls.txt")
    return all_course_urls

if __name__ == "__main__":
    # Edit this if it stopped prematurely
    # Set start_page > 1 to resume from a specific page
    # The script will load existing URLs from course_urls.txt
    start_page = 1  # Start from beginning
    year = "2026"  # Required: specify year
    term = "Spring"  # Required: specify term Fall or Spring
    
    course_urls = scrape_harvard_courses(start_page=start_page, year=year, term=term)