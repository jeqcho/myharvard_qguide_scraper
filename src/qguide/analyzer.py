# analyze the courses

# from scipy import stats
import re
import statistics

import pandas as pd
from bs4 import BeautifulSoup
from nltk.sentiment import SentimentIntensityAnalyzer
from tqdm import tqdm

# you might need to uncomment the below
import nltk
# nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()


def process_rows(raw_rows):
    return [x.text for x in raw_rows]


def get_stats(raw_rows):
    rows = process_rows(raw_rows)
    if int(rows[0]) == 0:
        # no one answered this question
        return [0, 0, 0, -1]
    freqs = rows[1:-2]
    freqs = [int(x[:-1]) for x in freqs]
    scores = []
    freqs.reverse()
    for i in range(5):
        scores += [i + 1] * freqs[i]

    mean = float(rows[-2])
    median = statistics.median(scores)
    mode = statistics.mode(scores)
    stdev = statistics.stdev(scores)
    return [mean, median, mode, stdev]


possible_gem_sentences = []


def get_gem_probability(comment):
    sentences = comment.split('.')
    for sentence in sentences:
        if re.search(r'\bgem\b', sentence.lower()):
            sentiment = sia.polarity_scores(sentence)['compound']
            possible_gem_sentences.append((sentence, str(sentiment)))
            if sentiment <= 0:
                # negative sentiment, most likely not a gem
                continue
            else:
                if re.search(r'(not)|(isn\'t) a \'?"?gem"?\'?', sentence.lower()):
                    # explicit claim of not a gem
                    return 0
                # good sentiment and no explicit claim of not a gem, so gem
                return 1
    return 0


num_errors = 0
error_codes = []


def get_table_with(tables, th_text):
    # returns None or the table with the first th equals th_text
    for table in tables:
        if table.tr.th and table.tr.th.text.strip() == th_text:
            return table
    return None


def analyze(unique_code):
    global num_errors, error_codes
    with open('QGuides/' + unique_code + '.html', 'r') as f:
        page_text = f.read()
    soup = BeautifulSoup(page_text, 'html.parser')
    tables = soup.find_all('tbody')
    print(unique_code)
    no_comment_flag = False
    if len(tables) != 8:
        if len(tables) < 3:
            print('ERROR: Course missing most tables')
            num_errors += 1
            error_codes.append(unique_code)
            return []
        # check if no comments
        if tables[-1].th and tables[-1].th.text.strip() == 'Elective':
            print('Course missing comments table')
            no_comment_flag = True
    # number of students
    response_rate_table = get_table_with(tables, 'Responded')
    assert response_rate_table
    num_responded = response_rate_table.find_all('td')[0].text
    num_students = response_rate_table.find_all('td')[1].text

    # course score
    course_score_table = get_table_with(tables, 'Evaluate the course overall.')
    assert course_score_table
    course_score_rows = course_score_table.tr.find_all('td')
    course_score_stats = get_stats(course_score_rows)

    # lecturer score
    lecturer_score_table = get_table_with(tables, 'Evaluate your Instructor overall.')
    if lecturer_score_table:
        lecturer_score_rows = lecturer_score_table.tr.find_all('td')
        lecturer_score_stats = get_stats(lecturer_score_rows)
    else:
        lecturer_score_stats = [0, 0, 0, -1]

    # workload
    workload_score_table = get_table_with(tables, 'Response Count')
    if workload_score_table:
        workload_rows = workload_score_table.find_all('td')
        workload_stats = process_rows(workload_rows)[-4:]
        # split , for multi modes and choose max
        workload_stats = [str(-1) if x == 'N/A' else x for x in workload_stats]
        workload_stats = [float(x.split(',')[-1]) for x in workload_stats]
    else:
        workload_stats = [0, 0, 0, -1]

    # recommendation
    rec_freqs = []
    first_rec_table = get_table_with(tables, 'Recommend with Enthusiasm')
    assert first_rec_table
    for row in first_rec_table.find_all('tr'):
        rec_freqs.append(int(row.find_all('td')[1].text))
    rec_freqs.reverse()
    recs = []
    for i in range(5):
        recs += [i + 1] * rec_freqs[i]
    second_rec_table = get_table_with(tables, 'Response Ratio')
    assert second_rec_table
    rec_rows = second_rec_table.find_all('td')
    rec_stats = process_rows(rec_rows)[-3:]
    rec_stats = [str(-1) if x in ['N/A','NRP'] else x for x in rec_stats]
    rec_stats = [float(x) for x in rec_stats]
    if not recs:
        # empty rec scores
        num_errors += 1
        error_codes.append(unique_code)
        return []
    rec_stats.insert(2, statistics.mode(recs))

    # comments
    max_sent_score = 0
    min_sent_score = 0
    max_gem_sentiment = 0
    best_comment = ''
    worse_comment = ''
    best_gem_comment = ''
    if no_comment_flag:
        sentiment_stats = [0, 0, 0, -1]
        gem_stats = [0, 0, 0, -1]
    else:
        comments = [x.text for x in tables[-1].find_all('td')]
        sentiment_scores = []
        gem_probabilities = []
        for comment in comments:
            sentiment_score = sia.polarity_scores(comment)['compound']
            sentiment_scores.append(sentiment_score)
            if sentiment_score > max_sent_score:
                max_sent_score = sentiment_score
                best_comment = comment
            if sentiment_score < min_sent_score:
                min_sent_score = sentiment_score
                worse_comment = comment

            gem_probability = get_gem_probability(comment)
            gem_probabilities.append(gem_probability)
            if gem_probability > 0 and sentiment_score > 0 and sentiment_score > max_gem_sentiment:
                max_gem_sentiment = sentiment_score
                best_gem_comment = comment

        gem_stats = [statistics.mean(gem_probabilities),
                     statistics.median(gem_probabilities),
                     statistics.mode(gem_probabilities)]
        if len(gem_probabilities) > 1:
            gem_stats.append(statistics.stdev(gem_probabilities))
        else:
            gem_stats.append(-1)

        sentiment_stats = [statistics.mean(sentiment_scores),
                           statistics.median(sentiment_scores),
                           statistics.mode(sentiment_scores)]
        if len(sentiment_scores) > 1:
            sentiment_stats.append(statistics.stdev(sentiment_scores))
        else:
            sentiment_stats.append(-1)

    # Extract course_id from unique_code
    # Format: FAS-156950-2248-F2-1-001(Kehayova) -> 156950
    course_id = unique_code.split('-')[1]

    return [
        unique_code,
        course_id,
        num_responded,
        num_students,
        *course_score_stats,
        *lecturer_score_stats,
        *workload_stats,
        *rec_stats,
        *sentiment_stats,
        *gem_stats,
        best_comment,
        max_sent_score,
        worse_comment,
        min_sent_score,
        best_gem_comment,
        max_gem_sentiment
    ]


# demo or debug
# print(analyze('FAS-156950-2248-F2-1-001(Kehayova)'))

df = pd.read_csv('courses.csv')
unique_codes = df.unique_code.tolist()
stats = []
for code in tqdm(unique_codes):
    stats.append(analyze(code))
print("num_errors: " + str(num_errors))

# Print the first 10 error codes if any errors exist
if num_errors > 0:
    print("\nFirst 10 error codes:")
    for code in error_codes[:10]:
        print(code)

df2 = pd.DataFrame(stats, columns=[
    'unique_code',
    'course_id',
    "num_responded",
    "num_students",
    "course_score_mean",
    "course_score_median",
    "course_score_mode",
    "course_score_stdev",
    "lecturer_score_mean",
    "lecturer_score_median",
    "lecturer_score_mode",
    "lecturer_score_stdev",
    "workload_score_mean",
    "workload_score_median",
    "workload_score_mode",
    "workload_score_stdev",
    "rec_score_mean",
    "rec_score_median",
    "rec_score_mode",
    "rec_score_stdev",
    "sentiment_score_mean",
    "sentiment_score_median",
    "sentiment_score_mode",
    "sentiment_score_stdev",
    "gem_probability_mean",
    "gem_probability_median",
    "gem_probability_mode",
    "gem_probability_stdev",
    "best_comment",
    "max_sent_score",
    "worse_comment",
    "min_sent_score",
    "best_gem_comment",
    "max_gem_probability"
])

df3 = pd.merge(df, df2, on='unique_code')
df3.to_csv('course_ratings.csv', index=False)

with open('gem_sentences.txt', 'w') as file:
    for tup in possible_gem_sentences:
        file.write(': '.join(map(str, tup)) + '\n')
