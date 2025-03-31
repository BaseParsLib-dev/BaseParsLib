import unittest
from unittest.mock import AsyncMock

from playwright.async_api import Page

from base_pars_lib import AsyncPlaywrightBaseParser


class TestAsyncPlaywrightBaseParser(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.parser = AsyncPlaywrightBaseParser(debug=True, print_logs=True)
        self.parser.playwright = AsyncMock()
        self.parser.playwright.chromium = AsyncMock()
        self.parser._get_pc_user_agent = AsyncMock(return_value="mock_user_agent")  # type: ignore
        self.parser.proxy = None
        self.parser.browser = AsyncMock()

    async def test_backoff_open_new_page_on_context_success(self) -> None:
        mock_page = AsyncMock()
        self.parser.context = AsyncMock()
        self.parser.context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=None)
        mock_page.wait_for_load_state = AsyncMock(return_value=None)

        result = await self.parser._backoff_open_new_page_on_context(
            url="http://example.com", load_timeout=5, check_page=lambda page: True
        )

        self.assertEqual(result, mock_page)
        self.parser.context.new_page.assert_called_once()
        mock_page.goto.assert_called_once_with("http://example.com", timeout=5000)

    async def test_backoff_open_new_page_on_context_failure(self) -> None:
        self.parser.context = AsyncMock()
        self.parser.context.new_page = AsyncMock(side_effect=Exception("Failed to create page"))

        result = await self.parser._backoff_open_new_page_on_context(
            url="http://example.com", load_timeout=5, check_page=lambda page: True, iter_count=2
        )

        self.assertIsNone(result)

    async def test_generate_new_context(self) -> None:
        mock_browser = AsyncMock()
        self.parser.playwright.chromium.launch = AsyncMock(return_value=mock_browser)  # type: ignore
        self.parser.browser = None  # type: ignore

        await self.parser._generate_new_context(headless_browser=True)

        self.assertEqual(self.parser.browser, mock_browser)
        self.parser.playwright.chromium.launch.assert_called_once_with(  # type: ignore
            proxy=self.parser.proxy,
            headless=True,  # type: ignore
        )  # type: ignore
        self.parser.context.new_page.assert_called_once()  # type: ignore

    async def test_backoff_open_new_page_with_check_page(self) -> None:
        mock_page = AsyncMock()
        self.parser.context = AsyncMock()
        self.parser.context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=None)
        mock_page.wait_for_load_state = AsyncMock(return_value=None)

        async def check_page(page: Page) -> bool:
            return True  # Симулирую успешную проверку страницы

        result = await self.parser._backoff_open_new_page_on_context(
            url="http://example.com", load_timeout=5, check_page=check_page
        )

        self.assertEqual(result, mock_page)


# pytest tests/test_async_playwright_base_parser.py
