import hashlib

import httpx
from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.exceptions.fetcher import PageFetchError
from app.schemas.fetcher import FetchedPage

logger = get_logger(__name__)


class PageFetcher:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def fetch(self, url: str) -> FetchedPage:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
                logger.debug(f"Successfully fetched {url}, {len(html)} bytes")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {str(e)}")
            raise PageFetchError(f"Failed to fetch {url}: {str(e)}") from e

        soup = BeautifulSoup(html, "html.parser")

        title = "No title"
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        for element in soup(["script", "style", "noscript", "meta"]):
            element.extract()

        clean_text = soup.get_text(separator=" ", strip=True)
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        logger.debug(f"Parsed {url}: title='{title}', content_hash={content_hash[:8]}...")

        return FetchedPage(
            url=url,
            title=title,
            clean_text=clean_text,
            content_hash=content_hash,
        )
