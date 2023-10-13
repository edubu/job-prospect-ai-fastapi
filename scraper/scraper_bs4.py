import asyncio
import concurrent.futures
from typing import Dict, List

import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scraper.scraper_types import HeaderContent, PageContent, ScraperBaseClass


class ScraperBS4(ScraperBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def scrape(self, urls: List[str], concurrently: bool = True) -> List[PageContent]:
        # Using ThreadPoolExecutor to scrape concurrently
        if concurrently:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(self.fetchPage, urls))
                return results
        else:
            pages = []
            for url in urls:
                pages.append(self.fetchPage(url))
            return pages

    async def scrapeInternalLinks(self, raw_url: str) -> List[str]:
        url = raw_url
        if url[-1] == "/":
            url = url[:-1]

        internal_links = []

        html_content = await self.fetchUnhyrdratedHtmlContent(url)

        soup = BeautifulSoup(html_content, "html.parser")
        links = soup.find_all("a")

        protocol, hostname = await self.splitUrl(url)

        for link in links:
            if link.has_attr("href"):
                if hostname in link["href"]:
                    internal_links.append(link["href"])
                elif link["href"].startswith("/"):
                    internal_links.append(url + link["href"])

        return internal_links

    async def fetchUnhyrdratedHtmlContent(self, url: str) -> str:
        # open session
        self.session = aiohttp.ClientSession()

        # get unhydrated html content
        html_content = None
        async with self.session.get(url) as response:
            html_content = await response.text()

        # close session
        await self.session.close()

        return html_content

    async def filterValidLinks(self, urls: List[str]) -> List[str]:
        headers = await self.getHeaders(urls)

        valid_urls = []

        for header in headers:
            if header.status == 200 and header.url not in valid_urls:
                valid_urls.append(header.url)

        return valid_urls

    async def getHeaders(self, urls: List[str]) -> List[HeaderContent]:
        # create session
        self.session = aiohttp.ClientSession()

        # Fetch all pages and store if they return a status of 200 then put true into the list
        tasks = [self.fetchHeader(url) for url in urls]
        headers = await asyncio.gather(*tasks)

        # close session
        await self.session.close()
        self.session = None

        return headers

    # returns the header from the url
    async def fetchHeader(self, url: str) -> HeaderContent:
        async with self.session.get(url) as response:
            header = HeaderContent()
            header.status = response.status
            header.url = response.url.__str__()
            return header

    def fetchPage(self, url: str) -> PageContent:
        options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--headless")

        with webdriver.Chrome(options=options) as driver:
            driver.get(url)

            # Define a list of element locators (e.g., TAG_NAME, CSS_SELECTOR, XPATH)
            # element_locators = [
            #     By.TAG_NAME,
            #     "p",
            #     By.TAG_NAME,
            #     "h1",
            #     By.TAG_NAME,
            #     "h2",
            #     By.TAG_NAME,
            #     "h3",
            # ]

            # # # Wait for each element type to load
            # wait_timeout = 15  # Adjust the timeout as needed
            # for i in range(0, len(element_locators), 2):
            #     WebDriverWait(driver, wait_timeout).until(
            #         EC.presence_of_all_elements_located(
            #             (element_locators[i], element_locators[i + 1])
            #         )
            #     )
            print(f"Finding tags for {url}")

            # Find all 'h1', 'h2', 'h3', and 'p' elements
            elements_h1 = driver.find_elements(By.TAG_NAME, "h1")
            h1_text = [
                text for text in [element.text for element in elements_h1] if text != ""
            ]

            elements_h2 = driver.find_elements(By.TAG_NAME, "h2")
            h2_text = [
                text for text in [element.text for element in elements_h2] if text != ""
            ]

            elements_h3 = driver.find_elements(By.TAG_NAME, "h3")
            h3_text = [
                text for text in [element.text for element in elements_h3] if text != ""
            ]

            elements_p = driver.find_elements(By.TAG_NAME, "p")
            p_text = [
                text for text in [element.text for element in elements_p] if text != ""
            ]

            print(f"Found tags for {url}")

            h1s = "\n".join(h1_text)
            h2s = "\n".join(h2_text)
            h3s = "\n".join(h3_text)
            ps = "\n".join(p_text)

            page_text = f"{h1s}\n{h2s}\n{h3s}\n{ps}"

            # Construct PageContent object
            page = PageContent()
            page.title = driver.title
            page.bodyContent = page_text
            page.url = driver.current_url

            driver.close()

            return page

    async def splitUrl(self, url: str) -> str:
        hostname = None
        protocol = None

        if "www" in url:
            splits = url.split("www.")
            protocol = splits[0]
            hostname = splits[1]
        else:
            splits = url.split("//")
            protocol = splits[0]
            hostname = splits[1]

        return protocol, hostname
