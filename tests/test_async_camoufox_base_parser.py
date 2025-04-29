import platform
from typing import Any

import pytest
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Page

from base_pars_lib import AsyncCamoufoxBaseParser


async def is_page_loaded_check_success(_page: Page) -> bool:
    return "Example Domain" in await _page.content()


async def is_page_loaded_check_failure(_page: Page) -> bool:
    return False


async def check_page(_page: Page, test_row: str) -> bool:
    return (
            "This domain is for use in illustrative examples in documents" +
            test_row in await _page.content()
    )


@pytest.mark.parametrize(
    "params, results",
    [
        (
            {
                "url": "http://example.com/",
                "is_page_loaded_check": is_page_loaded_check_success,
                "check_page": check_page,
                "check_page_args": {"test_row": ""},
                "load_timeout": 30,
                "increase_by_seconds": 0,
                "iter_count": 1
            },
            {
                "url": "http://example.com/",
                "content_part": "Example Domain"
            }
        ),
        (
            {
                "url": "http://example.com/",
                "is_page_loaded_check": is_page_loaded_check_failure,
                "check_page": check_page,
                "check_page_args": {"test_row": ""},
                "load_timeout": 1,
                "increase_by_seconds": 0,
                "iter_count": 1
            },
            {
                "page": None
            }
        ),
        (
            {
                "url": "url",
                "is_page_loaded_check": is_page_loaded_check_success,
                "check_page": check_page,
                "check_page_args": {"test_row": ""},
                "load_timeout": 1,
                "increase_by_seconds": 0,
                "iter_count": 1
            },
            {
                "page": None
            }
        ),
        (
            {
                "url": "http://example.com/",
                "is_page_loaded_check": is_page_loaded_check_success,
                "check_page": check_page,
                "check_page_args": {"test_row": "check_page_fail"},
                "load_timeout": 1,
                "increase_by_seconds": 0,
                "iter_count": 2
            },
            {
                "page": None
            }
        )
    ],
)
@pytest.mark.asyncio
async def test_backoff_open_new_page(
        params: dict[str, Any],
        results: dict[str, Any],
        async_camoufox_base_parser: AsyncCamoufoxBaseParser
) -> None:
    browser_manager = AsyncCamoufox(
        headless="virtual" if platform.system() == "linux" else False
    )
    await browser_manager.__aenter__()
    async_camoufox_base_parser.browser = browser_manager.browser  # type: ignore[assignment]

    page = await async_camoufox_base_parser._backoff_open_new_page(**params)

    if (
        params.get("is_page_loaded_check") == is_page_loaded_check_failure or
        params.get("url") == "url" or
        params.get("check_page_args").get("test_row") == "check_page_fail"  # type: ignore[union-attr]
    ):
        assert results.get("page") is None
    else:
        assert page.url == results.get("url")  # type: ignore[union-attr]
        assert results.get("content_part") in await page.content()  # type: ignore[union-attr]

    await browser_manager.__aexit__()


@pytest.mark.parametrize(
    "params, results",
    [
        (
            {
                "url_to_request_from_page": "http://example.com/",
                "method": "GET"
            },
            {
                "response_part": "Example Domain"
            }
        ),
        (
            {
                "url_to_request_from_page": ["http://example.com/", "http://example.com/"],
                "method": "GET"
            },
            {
                "response_part": "Example Domain"
            },
        ),
        (
            {
                "url_to_request_from_page": ["http://example.com/"],
                "method": "GET"
            },
            {
                "response_part": "Example Domain"
            },
        )
    ]
)
@pytest.mark.asyncio
async def test_make_request_from_page(
    params: dict[str, Any],
    results: dict[str, Any],
    async_camoufox_base_parser: AsyncCamoufoxBaseParser
) -> None:
    browser_manager = AsyncCamoufox(
        headless="virtual" if platform.system() == "linux" else False
    )
    await browser_manager.__aenter__()
    async_camoufox_base_parser.browser = browser_manager.browser  # type: ignore[assignment]

    page = await async_camoufox_base_parser._backoff_open_new_page(
        url="http://example.com/",
        is_page_loaded_check=is_page_loaded_check_success,
        load_timeout=2,
        increase_by_seconds=0,
        iter_count=1
    )

    response = await async_camoufox_base_parser._make_request_from_page(
        page=page,  # type: ignore[arg-type]
        url=params.get("url_to_request_from_page"),  # type: ignore[arg-type]
        method=params.get("method")  # type: ignore[arg-type]
    )

    if isinstance(params.get("url_to_request_from_page"), str):
        assert results.get("response_part") in response
    elif isinstance(params.get("url_to_request_from_page"), list):
        assert isinstance(response, list)
        assert len(response) == len(params.get("url_to_request_from_page"))  # type: ignore[arg-type]
        for rsp in response:
            assert str(results.get("response_part")) in rsp

    await browser_manager.__aexit__()


# pytest tests/test_async_camoufox_base_parser.py
