# swe-job-scraper
A simple script to scrape www.engineerjobs.com for the frequencies of key words in software engineer job postings. Sample output is located in scrape.txt. Input options include locations and number of pages to scrape.

`blacklist.py` contains the blacklist and whitelist for key words. Additional words appearing in the frequencies dictionary are due to specific skills listed by employers on their job postings.

Run `jobscrape.py` as main to execute the program. Tested with python 3.9.3. Requires [tqdm](https://github.com/tqdm/tqdm).
