from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponse, ClientSession

from base_pars_lib import AiohttpResponse


@pytest.mark.asyncio
async def test_forming_aiohttp_response_success(
    async_base_parser: Any, mock_response: ClientResponse
) -> None:
    result = await async_base_parser._AsyncBaseParser__forming_aiohttp_response(mock_response)
    assert isinstance(result, AiohttpResponse)
    assert result.text == "test text"
    assert result.json == {"key": "value"}
    assert result.url == "http://example.com"
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_forming_aiohttp_response_failure(async_base_parser: Any) -> None:
    # Создаем мок-объект для ответа
    bad_response = MagicMock(spec=ClientResponse)
    bad_response.url = "http://example.com"
    bad_response.status = 500
    bad_response.text = AsyncMock(side_effect=Exception("Error"))

    # Проверяем, что при вызове метода возникает исключение
    with pytest.raises(Exception, match="Error"):
        await async_base_parser._AsyncBaseParser__forming_aiohttp_response(bad_response)


@pytest.mark.asyncio
async def test_get_request_params(async_base_parser: Any) -> None:
    params = await async_base_parser._AsyncBaseParser__get_request_params(
        method="GET",
        verify=True,
        with_random_useragent=True,
        proxies=None,
        headers={"Header": "value"},
        cookies={"Cookie": "value"},
        data={"data": "value"},
        json={"json": "value"},
        params={"param": "value"},
    )

    assert params["method"] == "GET"
    assert "User-Agent" in params["headers"]
    assert params["headers"]["Header"] == "value"
    assert params["cookies"]["Cookie"] == "value"
    assert params["data"] == {"data": "value"}
    assert params["json"] == {"json": "value"}
    assert params["params"] == {"param": "value"}
    assert params["ssl"] is True


@pytest.mark.asyncio
async def test_fetch_success(async_base_parser: Any) -> None:
    # Создаем mock ответа
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    mock_response.status = 200
    mock_response.url = "http://example.com"
    mock_response.text.return_value = "test text"
    mock_response.json.return_value = {"key": "value"}

    # Создаем mock сессии
    mock_session = MagicMock(spec=ClientSession)
    mock_session.request.return_value = mock_response

    result = await async_base_parser._AsyncBaseParser__fetch(
        url="http://example.com",
        session=mock_session,
        params={"method": "GET"},
        get_raw_aiohttp_response_content=False,
    )

    assert isinstance(result, AiohttpResponse)
    assert result.text == "test text"
    assert result.url == "http://example.com"
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_fetch_raw_content(async_base_parser: Any) -> None:
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None
    mock_response.read.return_value = b"raw content"

    mock_session = MagicMock(spec=ClientSession)
    mock_session.request.return_value = mock_response

    result = await async_base_parser._AsyncBaseParser__fetch(
        url="http://example.com",
        session=mock_session,
        params={"method": "GET"},
        get_raw_aiohttp_response_content=True,
    )

    assert result == b"raw content"


@pytest.mark.asyncio
async def test_fetch_with_retries(async_base_parser: Any) -> None:
    # Создаем ответы
    bad_response = MagicMock(spec=ClientResponse)
    bad_response.__aenter__.return_value = bad_response
    bad_response.__aexit__.return_value = None
    bad_response.url = "http://example.com"
    bad_response.status = 500
    bad_response.text.return_value = "Server error"

    good_response = MagicMock(spec=ClientResponse)
    good_response.__aenter__.return_value = good_response
    good_response.__aexit__.return_value = None
    good_response.url = "http://example.com"
    good_response.status = 200
    good_response.text.return_value = "OK"

    # Создаем mock сессии
    mock_session = MagicMock(spec=ClientSession)
    mock_session.request.side_effect = [bad_response, good_response]

    # Вызываем метод
    result = await async_base_parser._AsyncBaseParser__fetch(
        url="http://example.com",
        session=mock_session,
        params={"method": "GET"},
        iter_count=3,
        iter_count_for_50x_errors=2,
        save_bad_urls=True,
    )

    # Проверяем результаты
    assert isinstance(result, AiohttpResponse)
    assert result.text == "OK"

    # URL должен быть в bad_urls только если все попытки завершились ошибкой
    assert "http://example.com" not in async_base_parser.bad_urls
    assert mock_session.request.call_count == 2  # Проверяем, что было 2 запроса


@pytest.mark.asyncio
async def test_make_backoff_request_with_different_responses(async_base_parser: Any) -> None:
    # Создаем разные mock ответы
    response1 = MagicMock(spec=ClientResponse)
    response1.__aenter__.return_value = response1
    response1.__aexit__.return_value = None
    response1.status = 200
    response1.url = "http://example.com"
    response1.text.return_value = "response1"

    response2 = MagicMock(spec=ClientResponse)
    response2.__aenter__.return_value = response2
    response2.__aexit__.return_value = None
    response2.status = 200
    response2.url = "http://example.org"
    response2.text.return_value = "response2"

    # Настраиваем сессию
    mock_session = MagicMock(spec=ClientSession)
    mock_session.request.side_effect = [response1, response2]
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("aiohttp.ClientSession", return_value=mock_session):
        results = await async_base_parser._make_backoff_request(
            urls=["http://example.com", "http://example.org"], method="GET"
        )

        assert len(results) == 2
        assert results[0].text == "response1"
        assert results[1].text == "response2"
        assert mock_session.request.call_count == 2


@pytest.mark.asyncio
async def test_prepare_request_data(async_base_parser: Any) -> None:
    urls = ["url1", "url2"]
    data = [{"data1": "value1"}, {"data2": "value2"}]
    json = [{"json1": "value1"}, {"json2": "value2"}]

    url_count, max_requests, data_list, json_list = await async_base_parser._prepare_request_data(
        urls=urls, data=data, json=json
    )

    assert url_count == 2
    assert max_requests == 2
    assert data_list == data
    assert json_list == json


def test_select_value(async_base_parser: Any) -> None:
    result = async_base_parser._select_value({"key": "value"}, False, 0, 1)
    assert result == {"key": "value"}

    result = async_base_parser._select_value([{"key1": "value1"}, {"key2": "value2"}], False, 0, 2)
    assert result in [{"key1": "value1"}, {"key2": "value2"}]

    result = async_base_parser._select_value([{"key1": "value1"}, {"key2": "value2"}], True, 1, 2)
    assert result == {"key2": "value2"}


@pytest.mark.asyncio
async def test_check_response_200(async_base_parser: Any) -> None:
    response = AiohttpResponse(text="OK", json=None, url="http://example.com", status_code=200)
    is_cycle_end, response_ = await async_base_parser._check_response(
        response=response,
        iteration=1,
        url="http://example.com",
        increase_by_seconds=1,
        iter_count=3,
        save_bad_urls=False,
        ignore_404=False,
        long_wait_for_50x=False,
        iteration_for_50x=1,
        iter_count_for_50x_errors=3,
        increase_by_minutes_for_50x_errors=20,
        check_page=None,
        check_page_args=None,
    )

    assert is_cycle_end is True
    assert response_ == response


@pytest.mark.asyncio
async def test_check_response_404_ignored(async_base_parser: Any) -> None:
    response = AiohttpResponse(
        text="Not found", json=None, url="http://example.com", status_code=404
    )
    is_cycle_end, response_ = await async_base_parser._check_response(
        response=response,
        iteration=1,
        url="http://example.com",
        increase_by_seconds=1,
        iter_count=3,
        save_bad_urls=False,
        ignore_404=True,
        long_wait_for_50x=False,
        iteration_for_50x=1,
        iter_count_for_50x_errors=3,
        increase_by_minutes_for_50x_errors=20,
        check_page=None,
        check_page_args=None,
    )

    assert is_cycle_end is True
    assert response_ == response


@pytest.mark.asyncio
async def test_check_response_500_retry(async_base_parser: Any) -> None:
    response = AiohttpResponse(text="Error", json=None, url="http://example.com", status_code=500)
    is_cycle_end, response_ = await async_base_parser._check_response(
        response=response,
        iteration=1,
        url="http://example.com",
        increase_by_seconds=1,
        iter_count=3,
        save_bad_urls=False,
        ignore_404=False,
        long_wait_for_50x=False,
        iteration_for_50x=1,
        iter_count_for_50x_errors=3,
        increase_by_minutes_for_50x_errors=20,
        check_page=None,
        check_page_args=None,
    )

    assert is_cycle_end is False
    assert response_ is None


# pytest tests/utils/test_async_base_parser.py
