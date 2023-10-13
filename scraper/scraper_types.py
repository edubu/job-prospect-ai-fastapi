from abc import ABC, abstractmethod
from typing import List

from aiohttp import ClientResponse


class PageContent:
    def __init__(self) -> None:
        self.summary = None
        self.sections = []
        self.url = None
        self.bodyContent = None
        self.title = None


class HeaderContent:
    def __init__(self) -> None:
        self.url = None
        self.status = None


class ScraperBaseClass(ABC):
    @abstractmethod
    async def scrape(self, urls: List[str]) -> List[PageContent]:
        pass

    @abstractmethod
    async def scrapeInternalLinks(self, url: str) -> List[str]:
        pass

    @abstractmethod
    async def filterValidLinks(self, urls: List[str]) -> List[str]:
        pass
