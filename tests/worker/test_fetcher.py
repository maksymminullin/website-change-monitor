import asyncio
from unittest.mock import AsyncMock, patch
import pytest
import httpx
from httpx import Response, Request

from app.worker.fetcher import PageFetcher
from app.exceptions.fetcher import PageFetchError

@pytest.fixture
def fetcher():
    f = PageFetcher(timeout=1)
    yield f
    # Typically would be awaited in async test teardown, but we'll mock client in tests

@pytest.mark.asyncio
async def test_fetcher_success(fetcher):
    mock_response = Response(
        status_code=200, 
        text="<html><head><title>Test Page</title></head><body><p>Hello World</p><script>alert(1)</script></body></html>",
        request=Request("GET", "https://example.com")
    )
    
    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        result = await fetcher.fetch("https://example.com")
        
        assert result.title == "Test Page"
        assert result.clean_text == "Test Page Hello World"
        assert result.url == "https://example.com"
        assert result.content_hash is not None

@pytest.mark.asyncio
async def test_fetcher_no_title(fetcher):
    mock_response = Response(
        status_code=200, 
        text="<html><body>Some content</body></html>",
        request=Request("GET", "https://example.com")
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
        status_code=500, 
        text="Internal Server Error",
        request=Request("GET", "https://example.com")
    )
    
    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        with patch("app.worker.fetcher.asyncio.sleep", new_callable=AsyncMock):
            mock_get.side_effect = httpx.HTTPStatusError("500", request=mock_response.request, response=mock_response)
            
            with pytest.raises(PageFetchError):
                await fetcher.fetch("https://example.com")
                
            assert mock_get.call_count == 3

@pytest.mark.asyncio
async def test_fetcher_no_retry_on_404(fetcher):
    mock_response = Response(
        status_code=404, 
        text="Not Found",
        request=Request("GET", "https://example.com")
    )
    
    with patch.object(fetcher.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError("404", request=mock_response.request, response=mock_response)
        
        with pytest.raises(PageFetchError):
            await fetcher.fetch("https://example.com")
            
        assert mock_get.call_count == 1
