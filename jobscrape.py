import json
import string
import subprocess as sp
import urllib.request
import concurrent.futures

import numpy as np
import pandas as pd

from tqdm import tqdm
from blacklist import blacklist, whitelist
from html.parser import HTMLParser

PUNCTUATION = "><,.:;'\"[{}]|\\=_()*&^%$@!"
MAX_WORKERS = 100
MAX_PAGE_LIMIT = 1000

class Scraper(HTMLParser):
    frequencies = dict()
    stoi = dict()
    getting_keys = True
    keys = []

    def __init__(self, blacklist, whitelist):
        super().__init__()

        self.whitelist = whitelist

        for i, word in enumerate(self.whitelist):
            self.stoi[word] = i

        self.frequency_matrix = np.zeros([len(self.whitelist), len(self.whitelist)])

    def load_url(self, url):
        with urllib.request.urlopen(url) as url:
            return url.read().decode()

    def sort_dict(self):
        self.frequencies = { k: v for k, v in sorted(self.frequencies.items(), key=lambda item: item[1]) }

    def increment_dict(self, word):
        try:
            self.frequencies[word] += 1
        except KeyError:
            self.frequencies[word] = 1

    def increment_matrix(self, word, index, words):
        row = min(self.stoi[word], len(self.whitelist)-1)

        self.frequency_matrix[row][row] += 1

        for i, w in enumerate(words):
            if i != index:
                try:
                    col = min(self.stoi[w], len(self.whitelist))
                    self.frequency_matrix[row][col] += 1
                except KeyError:
                    pass

    def handle_starttag(self, tag, attrs):
        if self.getting_keys:
            for attr in attrs:
                if attr[0] == 'href':
                    split = attr[1].split('/')
                    if len(split) > 1 and split[1] == 'jobsearch':
                        key = split[-1].split('?')[0]
                        self.keys.append(key)

    def handle_data(self, data):
        if not self.getting_keys:
            stripped = data.translate(str.maketrans(dict.fromkeys(PUNCTUATION)))
            words = stripped.split(' ')

            for i, word in enumerate(words):
                word = word.lower()
                word = word.replace('\n', '')

                if len(word) == 0 or not word in whitelist:
                    continue

                self.increment_dict(word)
                self.increment_matrix(word, i, words)

    def get_keys(self, locations, page_limit=None):
        page_limit = 999 if None else page_limit

        for location in locations:
            location = location.replace(' ', '%20')
            base_link = "https://www.engineerjobs.com/jobs/search?from=homepage_searchbox&ak=software+engineer&l="+location+"&page="
            links = [base_link+str(i+1) for i in range(page_limit)]

            self.getting_keys = True
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_url = (executor.submit(self.load_url, url) for url in links)
                for future in tqdm(concurrent.futures.as_completed(future_to_url)):
                    html_string = future.result()
                    self.feed(html_string)

        a = "https://www.engineerjobs.com/api/job?key="
        b = "&isp=0&al=1&ia=0&tk=1f3is9ubjt4at800&tkt=serp"
        self.keys = [a+key+b for key in self.keys]

    def build_frequencies(self):
        self.getting_keys = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = (executor.submit(self.load_url, url) for url in self.keys)
            for future in tqdm(concurrent.futures.as_completed(future_to_url)):
                try:
                    data = json.loads(future.result())
                    description = data['job']['description']
                    self.feed(description)

                    for skill in data['skillEntities']:
                        word = skill.lower()
                        self.increment_dict(word)

                except urllib.error.HTTPError as e:
                    print("Error!", e)
                    continue

    def get_cooccurrences(self):
        return np.minimum(self.frequency_matrix.T.dot(self.frequency_matrix), len(self.keys)//10)

if __name__ == "__main__":
    scraper = Scraper(blacklist, whitelist)
    locations = []
    locations_default = ["Seattle, WA", "Columbus, OH", "Los Angeles, CA", "San Diego, CA",
                         "New York City, NY", "Austin, TX", "Dallas, TX", "Portland, OR"]

    input_string = "Input location as City, ST (empty input to continue): "

    print("Default locations: ")
    for location in locations_default:
        print(location)
    print(' ')

    location = input(input_string)
    while len(location) > 0:
        locations.append(location)
        location = input(input_string)

    if len(locations) == 0:
        locations = locations_default

    correct_input = False
    page_limit = 30
    while not correct_input:
        try:
            inp = input(f"Number of pages to scrape (max=1000, default={page_limit}): ")
            if len(inp) == 0:
                break

            page_limit = int(inp)
            page_limit = int(page_limit)
            correct_input = True
        except ValueError:
            print("Number must be decimal. e.g. 10")

    page_limit = min(page_limit, MAX_PAGE_LIMIT)

    output_filename = input("Output filename, no extension (default='scrape')")
    if len(output_filename) == 0:
        output_filename = "scrape"

    output_filename += ".txt"

    print("Gathering job posting keys...")
    scraper.get_keys(locations, page_limit)
    print(f"{len(scraper.keys)} job postings gathered.\n")
    print("Counting key word frequencies...")
    scraper.build_frequencies()

    scraper.sort_dict()

    df = { 'whitelist': scraper.whitelist }
    df = pd.DataFrame.from_dict(df)
    df.to_csv("whitelist.csv", index=False)

    df = { 'word': list(scraper.frequencies.keys()), 'frequency': list(scraper.frequencies.values()) }
    df = pd.DataFrame.from_dict(df)
    df.to_csv("frequencies.csv", index=False)

    coocc = scraper.get_cooccurrences()
    np.save("cooccurrences.npy", coocc)

    print(f"See `frequencies.csv`, `cooccurrences.npy` for results and `whitelist.csv`.")
