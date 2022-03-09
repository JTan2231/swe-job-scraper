# swe-job-scraper
A simple script to scrape www.engineerjobs.com for the frequencies of key words in software engineer job postings. Sample output is located in scrape.txt. Input options include locations and number of pages to scrape.

`blacklist.py` contains the blacklist and whitelist for key words. Additional words appearing in the frequencies dictionary are due to specific skills listed by employers on their job postings.

Run `python jobscrape.py` to get the co-occurrence matrix, word frequencies, and used whitelist.

Run `python visualize.py` to view the matrix using the files generated from `jobscrape.py`. Below is an example visualization using the provided files.

![swescrape](https://user-images.githubusercontent.com/37962780/157366534-8c10a716-887d-49bc-8ae6-207663ef0c9a.png)

![bar](https://user-images.githubusercontent.com/37962780/157367516-3f2e1780-95c2-4777-b842-58f369682202.png)
All gathered words with frequencies over 50.
