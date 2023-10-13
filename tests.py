import asyncio
import json

from scraper.scraper_bs4 import ScraperBS4
from scraper.scraper_types import PageContent
from summarizer import generateCompanySummary


def test_scraping_links():
    scraper = ScraperBS4()

    with open("test_data/airtable_links.json", "r") as json_file:
        links = json.load(json_file)

    print(f"Attempting to scrape {len(links)} links")
    pages = scraper.scrape(links, concurrently=True)
    print(f"Succesfully scraped {len(pages)} pages")
    x = 10


def test_generate_company_summary():
    asyncio.run(generateCompanySummary("https://www.airtable.com"))


if __name__ == "__main__":
    test_scraping_links()
