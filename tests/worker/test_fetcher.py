from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import Request, Response

from app.exceptions.fetcher import PageFetchError
from app.worker.fetcher import PageFetcher


@pytest.fixture
def fetcher():
    f = PageFetcher(timeout=1)
    yield f
    # Typically would be awaited in async test teardown, but we'll mock client in tests


@pytest.mark.asyncio
async def test_fetcher_success(fetcher):
    html_content = (
        "<html><head><title>Test Page</title></head>"
        "<body><p>Hello World.</p><p>This is a long text to make sure we bypass the SPA "
        "detection logic, which requires less than 200 chars. "
        "Here are more characters just to be absolutely sure we pass the 200 limit. "
        "More characters. More characters. More characters. More characters. "
        "More characters. More characters.</p>"
        "<script>alert(1)</script></body></html>"
    )
    mock_response = Response(
        status_code=200,
        text=html_content,
        request=Request("GET", "https://example.com"),
    )

    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        result = await fetcher.fetch("https://example.com")

        assert result.title == "Test Page"
        assert result.url == "https://example.com"
        assert result.content_hash is not None
        assert result.needs_js_upgrade is False


@pytest.mark.asyncio
async def test_fetcher_spa_upgrade(fetcher):
    html_content = (
        "<html><body><noscript>You need JavaScript</noscript><script></script></body></html>"
    )
    mock_response = Response(
        status_code=200,
        text=html_content,
        request=Request("GET", "https://example.com"),
    )

    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        with patch.object(fetcher, "_fetch_with_playwright", new_callable=AsyncMock) as mock_pw:
            mock_get.return_value = mock_response
            mock_pw.return_value = (
                "<html><head><title>SPA</title></head><body>Rendered!</body></html>"
            )

            result = await fetcher.fetch("https://example.com")

            assert result.needs_js_upgrade is True
            assert result.title == "SPA"
            assert result.clean_text == "SPA Rendered!"
            assert mock_pw.call_count == 1


@pytest.mark.asyncio
async def test_fetcher_with_requires_js(fetcher):
    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        with patch.object(fetcher, "_fetch_with_playwright", new_callable=AsyncMock) as mock_pw:
            mock_pw.return_value = (
                "<html><head><title>JS Title</title></head><body>Rendered directly!</body></html>"
            )

            # Call fetch with requires_js=True
            result = await fetcher.fetch("https://example.com", requires_js=True)

            assert result.title == "JS Title"
            assert result.clean_text == "JS Title Rendered directly!"
            assert (
                result.needs_js_upgrade is False
            )  # Because it was explicitly requested, not auto-upgraded

            # HTTPX should NOT be called
            mock_get.assert_not_called()
            assert mock_pw.call_count == 1


@pytest.mark.asyncio
async def test_fetcher_no_title(fetcher):
    mock_response = Response(
        status_code=200,
        text="<html><body>Some content</body></html>",
        request=Request("GET", "https://example.com"),
    )

    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        result = await fetcher.fetch("https://example.com")

        assert result.title == "No title"
        assert result.clean_text == "Some content"


@pytest.mark.asyncio
async def test_fetcher_retry_on_timeout(fetcher):
    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        # Mock sleep to not wait in tests
        with patch("app.worker.fetcher.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_get.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(PageFetchError, match="Failed to fetch"):
                await fetcher.fetch("https://example.com")

            assert mock_get.call_count == 3
            assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_fetcher_retry_on_500(fetcher):
    mock_response = Response(
        status_code=500, text="Internal Server Error", request=Request("GET", "https://example.com")
    )

    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        with patch("app.worker.fetcher.asyncio.sleep", new_callable=AsyncMock):
            mock_get.side_effect = httpx.HTTPStatusError(
                "500", request=mock_response.request, response=mock_response
            )

            with pytest.raises(PageFetchError):
                await fetcher.fetch("https://example.com")

            assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_fetcher_no_retry_on_404(fetcher):
    mock_response = Response(
        status_code=404, text="Not Found", request=Request("GET", "https://example.com")
    )

    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError(
            "404", request=mock_response.request, response=mock_response
        )

        with pytest.raises(PageFetchError):
            await fetcher.fetch("https://example.com")

        assert mock_get.call_count == 1
