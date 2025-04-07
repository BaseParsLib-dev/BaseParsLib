from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest
from fake_useragent import UserAgent
from playwright.async_api import Page

from base_pars_lib.core.async_browsers_parser_base import AsyncBrowsersParserBase


async def page_method(url: str) -> str:
    return url


@pytest.mark.asyncio
async def test_get_pc_user_agent(
    async_browsers_parser: AsyncBrowsersParserBase, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Мокаем UserAgent
    mock_user_agent = MagicMock()
    mock_user_agent.random = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )

    monkeypatch.setattr(UserAgent, "random", mock_user_agent.random)

    user_agent = await async_browsers_parser._get_pc_user_agent()
    assert user_agent == mock_user_agent.random


@pytest.mark.asyncio
async def test_async_pages(async_browsers_parser: AsyncBrowsersParserBase) -> None:
    urls = ["http://example.com", "http://example.org"]
    results = await async_browsers_parser._async_pages(urls, page_method)
    assert results == urls


@pytest.mark.asyncio
async def test_method_in_series_with_list(async_browsers_parser: AsyncBrowsersParserBase) -> None:
    chunked_array = [["http://example.com"], ["http://example.org"]]
    results = await async_browsers_parser._method_in_series(
        chunked_array, page_method, sleep_time=0
    )  # type: ignore
    assert results is None


@pytest.mark.asyncio
async def test_method_in_series_with_tuple(async_browsers_parser: AsyncBrowsersParserBase) -> None:
    chunked_array = (["http://example.com"], ["http://example.org"])
    results = await async_browsers_parser._method_in_series(
        chunked_array, page_method, sleep_time=0
    )  # type: ignore
    assert results is None


@pytest.mark.asyncio
async def test_method_in_series_with_mixed_data(
    async_browsers_parser: AsyncBrowsersParserBase,
) -> None:
    chunked_array = [["http://example.com"], ("http://example.org",)]
    results = await async_browsers_parser._method_in_series(
        chunked_array, page_method, sleep_time=0
    )  # type: ignore
    assert results is None


@pytest.mark.asyncio
async def test_method_in_series_empty(async_browsers_parser: AsyncBrowsersParserBase) -> None:
    chunked_array: List[List[str]] = []
    results = await async_browsers_parser._method_in_series(
        chunked_array, page_method, sleep_time=0
    )  # type: ignore
    assert results is None


@pytest.mark.asyncio
async def test_method_in_series(async_browsers_parser: AsyncBrowsersParserBase) -> None:
    chunked_array = [["http://example.com"], ["http://example.org"]]
    await async_browsers_parser._method_in_series(chunked_array, page_method, sleep_time=0)

    for chunk in chunked_array:
        for url in chunk:
            await page_method(url)


@pytest.mark.asyncio
async def test_scroll_to(async_browsers_parser: AsyncBrowsersParserBase) -> None:
    mock_page = AsyncMock(spec=Page)

    # Тестируем прокрутку до конца страницы
    await async_browsers_parser._scroll_to(mock_page, full_page=True)
    mock_page.evaluate.assert_awaited_with(
        "window.scrollTo(0, document.body.scrollHeight, {behavior: 'smooth'})"
    )

    # Тестируем прокрутку на определенное количество пикселей
    await async_browsers_parser._scroll_to(mock_page, from_=0, to=100)
    mock_page.evaluate.assert_awaited_with("window.scrollTo(0, 100, {behavior: 'smooth'})")

    # Тестируем прокрутку с пользовательским JS кодом
    custom_js_code = "console.log('Scrolling...')"
    await async_browsers_parser._scroll_to(mock_page, custom_js_code=custom_js_code)
    mock_page.evaluate.assert_awaited_with(custom_js_code)


# pytest tests/core/test_async_browsers_parser_base.py
