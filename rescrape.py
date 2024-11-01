# rescrape for those who have sections, so need to click again
# remember to edit the term below
import time
import urllib.parse

import pandas as pd
# selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class AnyEc:
    """ Use with WebDriverWait to combine expected_conditions
        in an OR.
    """

    def __init__(self, *args):
        self.ecs = args

    def __call__(self, driver):
        for fn in self.ecs:
            try:
                res = fn(driver)
                if res:
                    return True
                    # Or return res if you need the element found
            except:
                pass


driver_path = "/Users/jeqcho/chromedriver-mac-arm64/chromedriver"
driver = webdriver.Chrome(service=Service(driver_path))

season = "spring"
container_url = 'https://courses.my.harvard.edu/psp/courses/EMPLOYEE/EMPL/h/?tab=HU_CLASS_SEARCH&SearchReqJSON=%7B' \
                '%22ExcludeBracketed%22%3Atrue%2C%22SaveRecent%22%3Atrue%2C%22Facets%22%3A%5B%5D%2C%22PageNumber%22' \
                '%3A1%2C%22SortOrder%22%3A%5B%22SCORE%22%5D%2C%22TopN%22%3A%22%22%2C%22PageSize%22%3A%22%22%2C' \
                '%22SearchText%22%3A%22{}%20' + season + '%22%7D '

df = pd.read_csv('courses.csv')

results = []
course_codes = list(dict.fromkeys(df.course_code.tolist()))

to_be_rescraped = []
for course_code in course_codes:
    print(course_code)
    try:
        with open('myharvard/' + course_code + '.html', 'r') as f:
            text = f.read()
        if text == """<div id="lbContentMain" class="cMain ">&nbsp;</div>""":
            to_be_rescraped.append(course_code)
    except FileNotFoundError as e:
        print(e)

PACKAGES = []
urls = [container_url.format(urllib.parse.quote(x)) for x in to_be_rescraped]
for i in range(len(urls)):
    PACKAGES.append([urls[i], to_be_rescraped[i]])

for idx, package in enumerate(PACKAGES):
    url = package[0]
    course_code = package[1]
    print(f'{idx}/{len(PACKAGES)}')
    print(course_code)
    driver.get(url)
    time.sleep(1)
    WebDriverWait(driver, 10).until(EC.invisibility_of_element((By.ID, "HU_LoaderAll")))

    try:
        driver.find_elements(By.CLASS_NAME, "isSCL_ResultItem")[0].click()
        time.sleep(10) # increase if necessary
        driver.find_elements(By.CLASS_NAME, "isSCL_ResultItem")[1].click()
        element = driver.find_element(By.ID, "lbContentMain")

        # Save the element's HTML to a file
        with open("myharvard/" + course_code + '.html', "w") as f:
            f.write(element.get_attribute("outerHTML"))

    except IndexError as e:
        print(e)
        print('no such element')
        with open('not-offered.txt', 'a') as f:
            f.write(course_code + '\n')

# infinite loop
driver.quit()
