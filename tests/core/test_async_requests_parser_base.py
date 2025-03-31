from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest

from base_pars_lib.core.async_requests_parser_base import AiohttpResponse, AsyncRequestsParserBase


@pytest.mark.asyncio
async def test_check_response(async_requests_parser: AsyncRequestsParserBase) -> None:
    response = AiohttpResponse(
        text="OK", json=None, url="http://example.com", status_code=HTTPStatus.OK
    )

    result, resp = await async_requests_parser._check_response(
        response, 1, "http://example.com", 1, 3, False, False, False, 0, 0, 0
    )

    assert result is True
    assert resp == response

    # Тестируем с None
    result, resp = await async_requests_parser._check_response(
        None, 1, "http://example.com", 1, 3, False, False, False, 0, 0, 0
    )

    assert result is False
    assert resp is None


@pytest.mark.asyncio
async def test_append_to_bad_urls(async_requests_parser: AsyncRequestsParserBase) -> None:
    await async_requests_parser._append_to_bad_urls("http://bad-url.com")
    assert "http://bad-url.com" in async_requests_parser.bad_urls


@pytest.mark.asyncio
async def test_delete_from_bad_urls(async_requests_parser: AsyncRequestsParserBase) -> None:
    async_requests_parser.bad_urls.append("http://bad-url.com")
    await async_requests_parser._delete_from_bad_urls("http://bad-url.com")
    assert "http://bad-url.com" not in async_requests_parser.bad_urls


@pytest.mark.asyncio
async def test_get_by_random_index(async_requests_parser: AsyncRequestsParserBase) -> None:
    item = [{"key": "value1"}, {"key": "value2"}]
    random_index = 1
    result = await async_requests_parser._get_by_random_index(item, random_index, "item")

    assert result == {"key": "value2"}


@pytest.mark.asyncio
async def test_method_in_series(async_requests_parser: AsyncRequestsParserBase) -> None:
    mock_async_method = AsyncMock()
    chunked_array = [["http://example.com"], ["http://example.org"]]

    await async_requests_parser._method_in_series(chunked_array, mock_async_method, sleep_time=0)

    assert mock_async_method.call_count == len(chunked_array)
    for chunk in chunked_array:
        mock_async_method.assert_any_await(chunk)


@pytest.mark.asyncio
async def test_calculate_random_cookies_headers_index(
    async_requests_parser: AsyncRequestsParserBase,
) -> None:
    cookies = [{"cookie1": "value1"}, {"cookie2": "value2"}]
    headers = [{"header1": "value1"}, {"header2": "value2"}]

    index = await async_requests_parser._calculate_random_cookies_headers_index(cookies, headers)

    assert 0 <= index < 2  # Проверяем, что индекс в пределах допустимого диапазона


@pytest.mark.asyncio
async def test_select_value(async_requests_parser: AsyncRequestsParserBase) -> None:
    value = [{"header1": "value1"}, {"header2": "value2"}]
    selected_value = async_requests_parser._select_value(
        value, match_to_urls=True, index=0, urls_length=2
    )

    assert selected_value == {"header1": "value1"}


@pytest.mark.asyncio
async def test_prepare_request_data(async_requests_parser: AsyncRequestsParserBase) -> None:
    urls = ["http://example.com", "http://example.org"]
    data = [{"key": "value1"}, {"key": "value2"}]
    json = {"key": "value3"}

    (
        url_count,
        max_requests,
        data_list,
        json_list,
    ) = await async_requests_parser._prepare_request_data(urls, data, json)  # type: ignore

    assert url_count == 2
    assert max_requests == 2
    assert data_list == data
    assert json_list == [json, json]  # json дублируется до длины max_requests


# pytest tests/core/test_async_requests_parser_base.py
