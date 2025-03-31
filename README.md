# myHarvard and QGuide scraper

This scraper compiles Harvard courses and QReport feedback into a nice CSV. Current results are at  [release](./release). Archived results at [archive](./archive).

The scraper is customized for the Harvard Gem [website](https://jeqcho.github.io/harvard-gems), but you can also use the CSV for anything you like.

![Screenshot of the Harvard Gem website](readme_images/readme-screenshot.png)

If you found it useful, you can

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jeqcho)

## Further analytics

Course ratings correlate well with recommendation score.

![Course score vs recommendation score graph](readme_images/course_vs_rec.png)

Course ratings also correlate well with lecturer scores, but with more scatter.

![Course score vs lecturer score graph](readme_images/course_vs_lecturer.png)

Sentiment analysis on the course comments also agree well with its average course rating.

![Course score vs sentiment score graph](readme_images/course_vs_sentiment.png)

Most high-scoring courses have low workload.

![Course score vs workload score graph](readme_images/course_vs_workload.png)

Harvard classes tend to have high ratings. It is rare to get a low score.

![Histogram of the courses by rating](readme_images/course_score_freq.png)

Most Harvard classes have a workload demand of around 5 hours per week outside of classes, though the distribution is skewed so some classes have much higher workloads.

![Histogram of the courses by workload hours](readme_images/workload_freq.png)

There is little correlation between the number of students in the class and the score of the class.

![Course score vs number of students graph](readme_images/course_vs_num_students.png)

More analysis, and the code for the graphs can be found through this [Colab Notebook](https://colab.research.google.com/drive/1WR3_DSCN_aL7l6b5yqrqto8116Ktb_TY?usp=sharing). A copy of
the notebook is also available in the repo above as `course_ratings_analysis.ipynb`. Remember to upload `verbose_course_ratings.csv` if you hope to tinker around.

## Website
The code for the website can be found at [this repo](https://github.com/jeqcho/harvard-gems). This repo is for the scrapping and analytics.

## Installation

If you use a virtual environment, please specify Python 3.11 for numpy compatibility

```bash
conda create -n harvard-gems python=3.11
conda activate harvard-gems
```

Then install the requirements

`pip install -r requirements.txt`

## Usage

You probably don't need to follow the steps below since the results can be found at `release` (or `archive` for older results), but
this is a step-by-step guide on how to create that csv from scratch.


### Scraping the QGuide

The code for this section is at [src/qguide](./src/qguide).

1. First the program needs to discover all the QGuide links for that year and term. Navigate to this link `https://qreports.fas.harvard.edu/browse/index?school=FAS&calTerm=YEAR%20SEMESTER` where you replace `YEAR` with the current year (e.g. `2025`) and `SEMESTER` with one of `Spring` and `Fall`. It requires login.
2. Download the webpage (<kbd>ctrl</kbd>+<kbd>s</kbd> or <kbd>cmd</kbd>+<kbd>s</kbd>) as a HTML-only file. Keep the default name `QReports.html` and put it in this folder replacing the old file.
3. Run `scraper.py` to scrape the links for the QGuides for each course. The links generated will be stored at `courses.csv`.
4. Visit the first QGuide link scrapped at `courses.csv`. Be careful in VSCode, since it will concat the other fields and result in an invalid URL.
5. Open the Developer Console, go to Application and click on the Cookie tab. Get the values for `ASP.NET_SessionId` and `CookieName` and paste it to `secret_cookie.txt` in the following format
   ```text
   ASP.NET_SessionId=YOUR_VALUE_HERE
   CookieName=YOUR_VALUE_HERE
   ```
6. Make sure you delete the current `QGuides` folder to start afresh if it exists.
7. Run `downloader.py` to use your cookies to download all the QGuides with the links scrapped from the previous step. The QGuides will be
   stored at the folder `QGuides`. This takes about 5 minutes.
8. Run `analyzer.py` to generate `course_ratings.csv`. If you run into a course with bugs, you can copy that FAS string and paste it to the `demo or debug` section of the code. My usual debugging process is to search for that file in the IDE, reveal in Finder, open in Chrome and see what's up.
9. Once that's done, rename `course_ratings.csv` as `YEAR_TERM.csv` like `2025_Fall.csv` and put this in `release/qguide`.

### Scraping myHarvard

The code for this section is at [src/qguide](./src/myharvard).

1. Remove existing file `course_lines.txt` to start afresh.
2. Specify the `year` and `term` at the bottom of `get_myharvard_url_chunks.py` and run it to get the URL chunks of the courses that will be offered. This will generate `course_lines.txt`.
3. Run `get_all_course_data.py` to get `all_courses.csv`.
4. Rename this as `YEAR_TERM.csv` like `2025_Fall.csv` and put this in `release/myharvard`.


### Combining QGuide and myHarvard for hugems.net

The code for this section is at [src/hugems](./src/hugems).

1. Specify the years and terms for the myharvard and qguide at `combine.py` and run it to get `hugems.csv`. This will match the myHarvard records with the qguide using `course_id`.
2. Run`course_ratings_analysis.ipynb`. This will generate the graphs above and the data at `release/hugems`. Follow through the notebook and play around!


# Future todo

- There is a course catalog PDF at the beta myHarvard. We can use that to generate the myHarvard URLs instead of cycling through the actual website. This will cut down the waiting time from about 10 minutes to near instant, and also save some traffic from hitting Harvard's server.
- HDS and XREG has bug where their catalog number of the pagination process has a suffix that doesn't appear in the actual URL. Right now, we catch this error when it happens and remove that suffix on the go. There might be a better way to do this.
- The `src/qguide` code is ancient (pre-Cursor) and can benefit from better design. For example, one can get a better methodology for the gems, especially given LLMs nowadays.
- There are duplicates on the myHarvard pagination. For example, for 2025 Fall, you can find similar classes (e.g. see Ochestra) on [page 29](https://beta.my.harvard.edu/?q=&school=All&sort=relevance&page=29&Term=2025+Fall&term=All) and on [page 47](https://beta.my.harvard.edu/?q=&school=All&sort=relevance&page=47&Term=2025+Fall&term=All). Right now we drop duplicate rows at `get_all_course_data.py`, but there might be a better way to do this.
- Sometimes, the unique code in `qguide` is not unique when two people with the same last name teach the course together (see GENED 1069 - Courtney Lamberth, Fall 2024). Currently, we simply drop duplicates in `src/hugems/combine.py`.
- Instead of manually copying over the release files we can programmatically do that.
- At time of writing March 31 2025, the beta myharvard search doesn't show the course level (though it allows filtering by it). Implement course level scraping somehow. (the old myharvard has it).
- The new search groups the EXPOS 20 courses under a single course as different sections suffixing the URL with `201`, `202` etc, though they have different course IDs. We currently don't have EXPOS 20 scrapped because we scrape by assuming all the URLs begin with `001`.