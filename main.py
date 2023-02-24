import gzip
import json
import os
import re
import shutil
import time

import requests
from bs4 import BeautifulSoup


def get_page(url):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
    }
    retries = 1
    while retries < 5:
        try:
            return requests.get(url, timeout=30, headers=HEADERS)
        except Exception as e:
            wait = retries * 5
            print(f"Error! Waiting {wait} secs and re-trying {url}...\n{e}")
            time.sleep(wait)
            retries += 1

    raise ValueError("Page could not be loaded")


BASE_URL = "https://www.state.gov/international-religious-freedom-reports/"

OUT = {}

p = get_page(BASE_URL)

soup = BeautifulSoup(p.text, "html.parser")

# get the most current report
current_year_url = (
    soup.find("a", id="latest")
    .parent.find_next_sibling()
    .find("a", href=True)
    .get("href")
)

p = get_page(f"{current_year_url}")

soup = BeautifulSoup(p.text, "html.parser")

# get list of all country data.
urls = [
    *set(
        [
            x.get("value")
            for x in soup.find(
                "select", class_="field-container chosen-container--country"
            ).find_all("option")
            if x.get("value").startswith("http")
        ]
    )
]

# iterate countries and get the region
for country in urls:
    print(country)
    d = get_page(country)

    soup = BeautifulSoup(d.text, "html.parser")

    country_name = (
        soup.find("select", class_="chosen-container--country")
        .find("option", selected=True)
        .string
    )

    report = soup.find("div", class_="report__content")

    summary = "\n\n".join(
        [
            x.text
            for x in report.find(
                "h2", string=re.compile(r"Executive Summary", re.I)
            ).parent.find_all("p")
        ]
    )

    OUT[country_name] = {"name": country_name, "summary": summary, "url": country}

    # break

if not os.path.isdir("data"):
    os.makedirs("data")

json_object = json.dumps(OUT, indent=4)
with open("data/data.json", "w") as outfile:
    outfile.write(json_object)

# gzip version
with open("data/data.json", "rb") as infile:
    with gzip.open("data/data.json.gz", "wb") as outfile:
        shutil.copyfileobj(infile, outfile)
