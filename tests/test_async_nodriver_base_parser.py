import unittest
from unittest.mock import AsyncMock, patch

from playwright.async_api import Page

from base_pars_lib import AsyncNodriverBaseParser
from base_pars_lib.async_nodriver_base_parser import BrowserIsNotInitError


class TestAsyncNodriverBaseParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = AsyncNodriverBaseParser()
        self.parser.browser = AsyncMock()

    @patch("your_module.logger")  # Adjust the import as necessary
    async def test_backoff_open_new_page_success(self, mock_logger: AsyncMock) -> None:
        mock_page: AsyncMock = AsyncMock()
        mock_page.close = AsyncMock()
        self.parser.browser.get = AsyncMock(return_value=mock_page)  # type: ignore

        async def is_page_loaded_check(page: Page) -> bool:
            return True

        result = await self.parser._backoff_open_new_page(
            url="http://example.com", is_page_loaded_check=is_page_loaded_check
        )

        self.assertEqual(result, mock_page)
        self.parser.browser.get.assert_called_once_with(  # type: ignore
            "http://example.com", new_tab=True, new_window=False
        )  # type: ignore

    @patch("your_module.logger")
    async def test_backoff_open_new_page_failure(self, mock_logger: AsyncMock) -> None:
        self.parser.browser.get = AsyncMock(side_effect=Exception("Failed to open page"))  # type: ignore

        async def is_page_loaded_check(page: Page) -> bool:
            return False

        result = await self.parser._backoff_open_new_page(
            url="http://example.com",
            is_page_loaded_check=is_page_loaded_check,
            iter_count=2,
        )

        self.assertIsNone(result)
        self.assertEqual(mock_logger.backoff_exception.call_count, 2)

    async def test_make_request_from_page_single_url(self) -> None:
        mock_page: AsyncMock = AsyncMock()
        self.parser._make_js_script = AsyncMock(return_value="mock_script")
        mock_page.evaluate = AsyncMock(return_value="response_text")

        response = await self.parser._make_request_from_page(mock_page, "http://example.com", "GET")

        self.assertEqual(response, "response_text")
        mock_page.evaluate.assert_called_once_with("mock_script", await_promise=True)

    async def test_make_request_from_page_multiple_urls(self) -> None:
        mock_page: AsyncMock = AsyncMock()
        self.parser._make_js_script = AsyncMock(return_value="mock_script")
        mock_page.evaluate = AsyncMock(return_value="response_text")

        response = await self.parser._make_request_from_page(
            mock_page, ["http://example.com", "http://example.org"], "GET"
        )

        self.assertEqual(response, ["response_text", "response_text"])
        self.assertEqual(mock_page.evaluate.call_count, 2)

    async def test_make_chrome_proxy_extension(self) -> None:
        path = await self.parser._make_chrome_proxy_extension("127.0.0.1", 8080, "user", "pass")

        self.assertTrue(path.endswith("nodriver_proxy_extension"))
        with open(path + "/background.js") as f:
            content = f.read()
            self.assertIn("127.0.0.1", content)
            self.assertIn("8080", content)
            self.assertIn("user", content)
            self.assertIn("pass", content)

        with open(path + "/manifest.json") as f:
            content = f.read()
            self.assertIn('"name": "Chrome Proxy"', content)

    async def test_browser_not_initialized_error(self) -> None:
        self.parser.browser = None

        with self.assertRaises(BrowserIsNotInitError):
            await self.parser._backoff_open_new_page(
                url="http://example.com", is_page_loaded_check=lambda page: True
            )


# pytest tests/test_async_nodriver_base_parser.py
