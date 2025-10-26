# use get_course_myharvard.py to scrape all the URLs given in course_urls.txt and return all the data as a CSV. Concat the instructors with commas.

import csv
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from get_course_myharvard import CourseScraper
import pandas as pd


def read_course_urls(filename: str) -> List[str]:
    """Read course URLs from the text file."""
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]


def format_instructors(instructors: List[Dict[str, str]]) -> str:
    """Format instructor names into a comma-separated string."""
    return ", ".join(instructor["name"] for instructor in instructors)


def scrape_single_course(url: str) -> Optional[Dict[str, Any]]:
    """Scrape a single course and return its data."""
    try:
        scraper = CourseScraper(url)
        course_data = scraper.scrape()
        course_data["instructors"] = format_instructors(course_data["instructors"])
        return course_data
    except Exception as e:
        tqdm.write(f"Error scraping {url}: {str(e)}")
        return None


def scrape_all_courses(
    course_urls: List[str], output_file: str = "all_courses.csv", max_workers: int = 10
):
    """Scrape all courses and save to CSV using multiple threads."""
    # Define CSV headers based on the course data structure
    headers = [
        "course_title",
        "subject_catalog",
        "instructors",
        "year_term",
        "term_type",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "weekdays",
        "class_number",
        "course_id",
        "consent",
        "enrolled",
        "waitlist",
        "lecture_sunday",
        "lecture_monday",
        "lecture_tuesday",
        "lecture_wednesday",
        "lecture_thursday",
        "lecture_friday",
        "lecture_saturday",
        "description",
        "notes",
        "school",
        "units",
        "cross_registration",
        "department",
        "course_component",
        "instruction_mode",
        "grading_basis",
        "course_requirements",
        "general_education",
        "quantitative_reasoning",
        "divisional_distribution",
    ]

    # List to store all course data
    all_course_data = []

    # Use ThreadPoolExecutor for parallel scraping
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_course = {
            executor.submit(scrape_single_course, url): url
            for url in course_urls
        }

        # Process completed tasks with tqdm progress bar
        with tqdm(
            total=len(course_urls), desc="Scraping courses", unit="course"
        ) as pbar:
            for future in as_completed(future_to_course):
                course_data = future.result()
                if course_data:
                    all_course_data.append(course_data)
                pbar.update(1)

    # Convert to DataFrame and drop duplicates
    df = pd.DataFrame(all_course_data)
    df = df.drop_duplicates()
    print(f"Found {len(df)} unique courses after removing duplicates")
    
    # Write unique courses to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for _, row in df.iterrows():
            writer.writerow(row.to_dict())


def main():
    """Main function to run the scraper."""
    debug = False

    try:
        course_urls = read_course_urls("course_urls.txt")
        print(f"Found {len(course_urls)} courses to scrape")

        if debug:
            # test: random 100
            # Get a random sample of 100 courses for testing
            import random

            if len(course_urls) > 100:
                course_urls = random.sample(course_urls, 100)
                print("Testing with random 100 courses")

        scrape_all_courses(course_urls)
        print("Scraping completed successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
