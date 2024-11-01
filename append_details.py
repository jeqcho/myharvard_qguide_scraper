import pandas as pd
from bs4 import BeautifulSoup

df = pd.read_csv('courses.csv')


def process(text, course_code):
    soup = BeautifulSoup(text, 'html.parser')
    soup_code = soup.find_all('h3')[0].text
    soup_title = soup.find_all('h2')[2].text
    if course_code not in soup_code.replace('  ', ' '):
        print("Wrong codes")
        print(f'Expected: {course_code} but got {soup_code}')
        return -1

    soup_term = soup.find_all("div", class_="isSCL_LBTermLabel")[0].text
    # edit this to the upcoming term
    if soup_term.strip() != "2025 Spring":
        print("Wrong term")
        print(soup_term)
        return -1

    interests = [
        "Course ID:",
        "Course Level:",
        "Department:",
        "Subject:",
        "Quantitative Reasoning with Data:",
        "Divisional Distribution:",
        "General Education:",
        "Course Component:"
    ]
    result = []
    for interest in interests:
        matches = soup.find_all('span', string=interest)
        if len(matches) == 0:
            result.append('')
            continue
        result.append(matches[0].parent.text.split(":")[1].strip())

    if "NOTE" in result[-1]:
        result[-1] = result[-1][:-4].strip()

    result.append(soup_title)
    print(result)
    return result


results = []
course_codes = list(dict.fromkeys(df.course_code.tolist()))

# for debug
start_index = 0
# start_index = course_codes.index('AFVS 40H')

for course_code in course_codes[start_index:]:
    print(course_code)
    try:
        with open('myharvard/' + course_code + '.html', 'r') as f:
            text = f.read()
        result = process(text, course_code)
        if result == -1:
            continue
        results.append([course_code] + result)
    except FileNotFoundError as e:
        print(e)

df2 = pd.DataFrame(results,
                   columns=['course_code', 'course_id', 'course_level', 'department', 'subject', 'qrd', 'divisional',
                            'gened',
                            'course_component', 'course_title_2024'])

df1 = pd.read_csv('course_ratings.csv')

df3 = pd.merge(df1, df2, on='course_code', how="outer")
df3.to_csv('verbose_course_ratings.csv', index=False)
