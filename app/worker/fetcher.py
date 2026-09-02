import asyncio
import hashlib

import httpx
from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.exceptions.fetcher import PageFetchError
from app.schemas.fetcher import FetchedPage

logger = get_logger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF = 1
MAX_BACKOFF = 32


class PageFetcher:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
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
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=headers,
            follow_redirects=True,
        )

    async def aclose(self):
        await self.client.aclose()

    async def _should_retry(self, error: Exception, status_code: int | None = None) -> bool:
        if isinstance(error, (asyncio.TimeoutError, httpx.TimeoutException)):
            return True
        if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
            return True
        if status_code == 429:
            return True
        if status_code and 500 <= status_code < 600:
            return True
        return False

    async def _fetch_with_retry(self, url: str) -> tuple[str, int]:
        backoff = INITIAL_BACKOFF
        last_error = None
        last_status = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                logger.debug(f"Successfully fetched {url}, {len(response.text)} bytes")
                return response.text, response.status_code

            except httpx.HTTPStatusError as e:
                last_error = e
                last_status = e.response.status_code
                if not self._should_retry(e, last_status):
                    raise
                logger.warning(
                    f"HTTP error {last_status} fetching {url} (attempt {attempt + 1}/{MAX_RETRIES})"
                )

            except httpx.HTTPError as e:
                last_error = e
                if not self._should_retry(e):
                    raise
                logger.warning(
                    f"Network error fetching {url}: {type(e).__name__} "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})"
                )

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)

        raise PageFetchError(
            f"Failed to fetch {url} after {MAX_RETRIES} attempts: {str(last_error)}"
        ) from last_error

    async def fetch(self, url: str) -> FetchedPage:
        try:
            html, status_code = await self._fetch_with_retry(url)
        except PageFetchError as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            raise

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
