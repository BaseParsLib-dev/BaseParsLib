from typing import Any, Callable
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Page

from base_pars_lib import AsyncPlaywrightBaseParser


@pytest.mark.asyncio
async def test_backoff_open_new_page_on_context_success() -> None:
    parser = AsyncPlaywrightBaseParser(debug=True, print_logs=True)
    parser.playwright = AsyncMock()
    parser.playwright.chromium = AsyncMock()
    parser._get_pc_user_agent = AsyncMock(return_value="mock_user_agent")  # type: ignore
    parser.proxy = None  # Инициализация proxy
    parser.browser = AsyncMock()

    mock_page = AsyncMock()
    parser.context = AsyncMock()
    parser.context.new_page = AsyncMock(return_value=mock_page)
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_load_state = AsyncMock(return_value=None)

    result = await parser._backoff_open_new_page_on_context(
        url="http://example.com", load_timeout=5, check_page=lambda page: True
    )

    assert result == mock_page
    parser.context.new_page.assert_called_once()
    mock_page.goto.assert_called_once_with("http://example.com", timeout=5000)


@pytest.mark.asyncio
async def test_backoff_open_new_page_on_context_failure() -> None:
    parser = AsyncPlaywrightBaseParser(debug=True, print_logs=True)
    parser.playwright = AsyncMock()
    parser.proxy = None  # Инициализация proxy
    parser.context = AsyncMock()
    parser.context.new_page = AsyncMock(side_effect=Exception("Failed to create page"))

    result = await parser._backoff_open_new_page_on_context(
        url="http://example.com", load_timeout=5, check_page=lambda page: True, iter_count=2
    )

    assert result is None


@pytest.mark.asyncio
async def test_generate_new_context() -> None:
    parser = AsyncPlaywrightBaseParser(debug=True, print_logs=True)
    parser.playwright = AsyncMock()
    parser.proxy = None  # Инициализация proxy
    mock_browser = AsyncMock()
    parser.playwright.chromium.launch = AsyncMock(return_value=mock_browser)  # type: ignore
    parser.browser = None  # type: ignore

    await parser._generate_new_context(headless_browser=True)

    assert parser.browser == mock_browser
    parser.playwright.chromium.launch.assert_called_once_with(  # type: ignore
        proxy=parser.proxy,
        headless=True,  # type: ignore
    )  # type: ignore


@pytest.mark.asyncio
async def test_backoff_open_new_page_with_check_page() -> None:
    parser = AsyncPlaywrightBaseParser(debug=True, print_logs=True)
    parser.playwright = AsyncMock()
    parser.proxy = None  # Инициализация proxy
    mock_page = AsyncMock()
    parser.context = AsyncMock()
    parser.context.new_page = AsyncMock(return_value=mock_page)
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_load_state = AsyncMock(return_value=None)

    async def check_page(page: Page) -> bool:
        return True  # Симулирую успешную проверку страницы

    result = await parser._backoff_open_new_page_on_context(
        url="http://example.com", load_timeout=5, check_page=check_page
    )

    assert result == mock_page


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "check_page, expected_result",
    [
        (lambda page: True, True),  # Успешная проверка
        # (lambda page: False, None),  # Неуспешная проверка
    ],
)
async def test_backoff_open_new_page_with_various_check_page(
    check_page: Callable[[Any], bool], expected_result: Any
) -> None:
    parser = AsyncPlaywrightBaseParser(debug=True, print_logs=True)
    parser.playwright = AsyncMock()
    parser.proxy = None  # Инициализация proxy
    mock_page = AsyncMock()
    parser.context = AsyncMock()
    parser.context.new_page = AsyncMock(return_value=mock_page)
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.wait_for_load_state = AsyncMock(return_value=None)

    result = await parser._backoff_open_new_page_on_context(
        url="http://example.com", load_timeout=5, check_page=check_page
    )

    assert result == (mock_page if expected_result else None)


# pytest tests/test_async_playwright_base_parser.py
