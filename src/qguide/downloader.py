# downloads q guides and put them in the folder QGuides

import concurrent.futures
import os
import time
import threading

import pandas as pd
import requests

PACKAGES = []


def preprocess_qlinks():
    df = pd.read_csv('courses.csv')
    urls = df.link.tolist()
    unique_codes = df.unique_code.tolist()
    for i in range(len(urls)):
        PACKAGES.append([urls[i], unique_codes[i]])


preprocess_qlinks()
# Uncomment line below to test code with smaller sample
# PACKAGES = PACKAGES[:10]
global_count = 0
count_lock = threading.Lock()
start_time = None

# Create the QGuide folder if not exist
if not os.path.exists('QGuides'):
    os.makedirs('QGuides')

# Choose any QGuide link, visit it on your browser, then open DevTools (Applications pane)
# to copy everything in the cookie field
# There should be three cookies: ASP.NET_SessionId, CookieName, and session_token
# Copy paste the entire cookie string into secret_cookie.txt as one line.
# You should create the secret cookie file
# the file should looke like
# "ASP.NET_SessionId=value; CookieName=value2; session_token=value3"
with open('secret_cookie.txt', 'r') as f:
    cookie = f.read()


# Retrieve a single page and report the URL and contents
def load_url(package, timeout):
    global global_count, start_time
    url = package[0]
    filename = package[1]
    headers = {
        'Cookie': cookie
    }
    
    # Exponential backoff parameters
    max_retries = 5
    base_delay = 1  # Start with 1 second
    
    for attempt in range(max_retries):
        try:
            page = requests.get(url, headers=headers, timeout=timeout)
            page.raise_for_status()  # Raise an exception for bad status codes
            
            with open('QGuides/' + filename + '.html', 'w') as f:
                f.write(page.text)
            
            # Success - break out of retry loop
            break
            
        except (requests.RequestException, IOError) as e:
            if attempt < max_retries - 1:
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt)
                print(f"Error downloading {filename} (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                # Final attempt failed
                print(f"Failed to download {filename} after {max_retries} attempts: {e}")
                raise
    
    with count_lock:
        global_count += 1
        elapsed_time = time.time() - start_time
        progress_percent = global_count / len(PACKAGES) * 100
        
        # Calculate ETA
        if global_count > 0:
            avg_time_per_file = elapsed_time / global_count
            remaining_files = len(PACKAGES) - global_count
            eta_seconds = avg_time_per_file * remaining_files
            
            # Format ETA
            if eta_seconds < 60:
                eta_str = f"{eta_seconds:.0f}s"
            elif eta_seconds < 3600:
                eta_str = f"{eta_seconds/60:.1f}m"
            else:
                eta_str = f"{eta_seconds/3600:.1f}h"
            
            print(f"Progress: {global_count}/{len(PACKAGES)} ({progress_percent:.1f}%) | "
                  f"Elapsed: {elapsed_time:.1f}s | ETA: {eta_str}")


# We can use a with statement to ensure threads are cleaned up promptly
print(f"Starting download of {len(PACKAGES)} files with 50 concurrent threads...")
start_time = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    # Start the load operations and mark each future with its URL
    future_to_url = {executor.submit(load_url, url, 60): url for url in PACKAGES}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))
        else:
            pass
            # print('%r page is %d bytes' % (url, len(data)))
    
    total_time = time.time() - start_time
    print(f"\nDownload complete! {len(PACKAGES)} files downloaded in {total_time:.1f}s ({total_time/60:.1f}m)")
