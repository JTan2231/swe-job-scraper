import json
import string
import subprocess as sp
import urllib.request
import concurrent.futures

from tqdm import tqdm
from blacklist import blacklist, whitelist
from html.parser import HTMLParser

PUNCTUATION = "><,.:;'\"[{}]|\\=_()*&^%$@!"
MAX_WORKERS = 100
MAX_PAGE_LIMIT = 1000

def increment_dict(d, word):
    if not word in d:
        d[word] = 1
    else:
        d[word] += 1

    return d

def sort_dict(d):
    return { k: v for k, v in sorted(d.items(), key=lambda item: item[1]) }

class Parser(HTMLParser):
    frequencies = dict()

    getting_keys = True

    keys = []

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

            for word in words:
                word = word.lower()
                word = word.replace('\n', '')

                if len(word) == 0 or not word in whitelist:
                    continue

                self.frequencies = increment_dict(self.frequencies, word)

def load_url(url):
    with urllib.request.urlopen(url) as url:
        return url.read().decode()

def get_keys(parser, locations, page_limit=None):
    page_limit = 999 if None else page_limit

    for location in locations:
        location = location.replace(' ', '%20')
        base_link = "https://www.engineerjobs.com/jobs/search?from=homepage_searchbox&ak=software+engineer&l="+location+"&page="
        links = [base_link+str(i+1) for i in range(page_limit)]

        parser.getting_keys = True
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = (executor.submit(load_url, url) for url in links)
            for future in tqdm(concurrent.futures.as_completed(future_to_url)):
                html_string = future.result()
                parser.feed(html_string)

    a = "https://www.engineerjobs.com/api/job?key="
    b = "&isp=0&al=1&ia=0&tk=1f3is9ubjt4at800&tkt=serp"
    parser.keys = [a+key+b for key in parser.keys]

    return parser

def build_parser(parser):
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = (executor.submit(load_url, url) for url in parser.keys)
        for future in tqdm(concurrent.futures.as_completed(future_to_url)):
            try:
                data = json.loads(future.result())
                description = data['job']['description']
                parser.feed(description)

                for skill in data['skillEntities']:
                    word = skill.lower()
                    parser.frequencies = increment_dict(parser.frequencies, word)

            except urllib.error.HTTPError as e:
                print("Error!", e)
                continue

    return parser

parser = Parser()
locations = []
locations_default = ["Seattle, WA", "Columbus, OH", "Los Angeles, CA", "San Diego, CA", "New York City, NY", "Austin, TX", "Dallas, TX"]
input_string = "Input location as City, ST (empty input to continue): "
print("Default input: ")
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
page_limit = 10
while not correct_input:
    try:
        inp = input("Input number of pages to scrape (max 1000, default 10): ")
        if len(inp) == 0:
            break

        page_limit = int(inp)
        page_limit = int(page_limit)
        correct_input = True
    except ValueError:
        print("Number must be decimal. e.g. 10")

page_limit = min(page_limit, MAX_PAGE_LIMIT)

print("Gathering job posting keys...")
parser = get_keys(parser, locations, page_limit)
print(f"{len(parser.keys)} keys gathered.")
print('')
print("Counting key word appearances...")
parser = build_parser(parser)

parser.frequencies = sort_dict(parser.frequencies)

with open("scrape.txt", 'w') as f:
    f.write('') # clear file

with open("scrape.txt", 'a') as f:
    for key, value in parser.frequencies.items():
        s = f"{key}: {value}\n"
        print(s[:-1])
        f.write(s)

print("Displaying word frequencies in console. Output saved to 'scrape.txt'")
