# downloads q guides and put them in the folder QGuides

import concurrent.futures
import os

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
    global global_count
    url = package[0]
    filename = package[1]
    headers = {
        'Cookie': cookie
    }
    page = requests.get(url, headers=headers)
    with open('QGuides/' + filename + '.html', 'w') as f:
        f.write(page.text)
    global_count += 1
    print(str(global_count / len(PACKAGES) * 100) + '% downloaded')


# We can use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
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
    print("done")
