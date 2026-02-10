from typing import Any, Dict, List, Optional

import pytest
from curl_cffi.requests.models import Response

from base_pars_lib.core.async_requests_parser_base import AiohttpResponse, AsyncRequestsParserBase


async def async_page_method(url: List[str]) -> List[str]:
    return url


async def check_page(
        response: AiohttpResponse | Response,
        test_arg: bool | None = None
) -> bool:
    if test_arg is None:
        return response.text == "Hihi"
    return test_arg


@pytest.mark.parametrize(
    "params, response_status_code, results",
    [
        (  # Базовая ситуация
            {
                "iteration": 1,
                "url": "http://example.com",
                "increase_by_seconds": 1,
                "iter_count": 3,
                "save_bad_urls": False,
                "ignore_404": False,
                "ignore_410": False,
                "long_wait_for_50x": False,
                "iteration_for_50x": 0,
                "iter_count_for_50x_errors": 0,
                "increase_by_minutes_for_50x_errors": 0,
                "check_page": check_page,
                "check_page_args": {"test_arg": None},
            },
            200,
            {
                "result": True,
                "response_returned": True
            }
        ),
        (  # Проверка, когда check_page взвращает False (+ проверка работы check_page_args)
            {
                "iteration": 1,
                "url": "http://example.com",
                "increase_by_seconds": 1,
                "iter_count": 3,
                "save_bad_urls": False,
                "ignore_404": False,
                "ignore_410": False,
                "long_wait_for_50x": False,
                "iteration_for_50x": 0,
                "iter_count_for_50x_errors": 0,
                "increase_by_minutes_for_50x_errors": 0,
                "check_page": check_page,
                "check_page_args": {"test_arg": False},
            },
            200,
            {
                "result": False,
                "response_returned": True
            }
        ),
        (  # Проверка сбора bad_urls + проверка возврата значений при статус коде не 200
            {
                "iteration": 1,
                "url": "http://example.com",
                "increase_by_seconds": 1,
                "iter_count": 3,
                "save_bad_urls": True,
                "ignore_404": False,
                "ignore_410": False,
                "long_wait_for_50x": False,
                "iteration_for_50x": 0,
                "iter_count_for_50x_errors": 0,
                "increase_by_minutes_for_50x_errors": 0,
                "check_page": check_page,
                "check_page_args": {"test_arg": None},
            },
            403,
            {
                "result": False,
                "response_returned": False
            }
        ),
        (  # Проверка iteration == iter_count
            {
                "iteration": 3,
                "url": "http://example.com",
                "increase_by_seconds": 1,
                "iter_count": 3,
                "save_bad_urls": False,
                "ignore_404": False,
                "ignore_410": False,
                "long_wait_for_50x": False,
                "iteration_for_50x": 0,
                "iter_count_for_50x_errors": 0,
                "increase_by_minutes_for_50x_errors": 0,
                "check_page": check_page,
                "check_page_args": {"test_arg": None},
            },
            403,
            {
                "result": True,
                "response_returned": True
            }
        )
    ],
)
@pytest.mark.asyncio
async def test_check_response(
        async_requests_parser: AsyncRequestsParserBase,
        params: dict[str, Any],
        response_status_code: int,
        results: dict[str, Any],
) -> None:
    response = AiohttpResponse(
        text="Hihi",
        json={"hi": "hihi"},
        url=params["url"],
        status_code=response_status_code,
    )

    result, resp = await async_requests_parser._check_response(
        response,
        **params
    )

    assert result == results["result"]
    if results["response_returned"]:
        assert resp == response
    else:
        assert resp is None
    if params["save_bad_urls"]:
        assert params["url"] in async_requests_parser.bad_urls


@pytest.mark.asyncio
async def test_append_to_bad_urls(async_requests_parser: AsyncRequestsParserBase) -> None:
    initial_count = len(async_requests_parser.bad_urls)  # Сохраняем начальное количество ссылок
    await async_requests_parser._append_to_bad_urls("http://bad-url.com")

    # Проверяем, что ссылка добавлена
    assert "http://bad-url.com" in async_requests_parser.bad_urls

    # Проверяем, что общее количество ссылок увеличилось на 1
    assert len(async_requests_parser.bad_urls) == initial_count + 1


@pytest.mark.asyncio
async def test_delete_from_bad_urls(async_requests_parser: AsyncRequestsParserBase) -> None:
    async_requests_parser.bad_urls.append("http://bad-url.com")
    initial_count = len(async_requests_parser.bad_urls)
    await async_requests_parser._delete_from_bad_urls("http://bad-url.com")

    # Проверяем, что ссылка была удалена
    assert "http://bad-url.com" not in async_requests_parser.bad_urls

    # Проверяем, что общее количество ссылок уменьшилось на 1
    assert len(async_requests_parser.bad_urls) == initial_count - 1


@pytest.mark.parametrize(
    "item, random_index, expected_result",
    [
        ([{"key": "value1"}, {"key": "value2"}], 1, {"key": "value2"}),  # Тест для списка
        ({"key": "value"}, 0, {"key": "value"}),  # Тест для словаря
    ],
)
@pytest.mark.asyncio
async def test_get_by_random_index(
    async_requests_parser: AsyncRequestsParserBase,
    item: Any,
    random_index: int,
    expected_result: dict,
) -> None:
    result = await async_requests_parser._get_by_random_index(item, random_index, "item")
    assert result == expected_result


@pytest.mark.parametrize(
    "chunked_array, expected_results",
    [
        (
            [["http://example.com"], ["http://example.org"]],
            ["http://example.com", "http://example.org"],
        ),
        ([["http://example.com"]], ["http://example.com"]),
        ([[], []], []),  # Тест для пустого массива
    ],
)
@pytest.mark.asyncio
async def test_method_in_series(
    async_requests_parser: AsyncRequestsParserBase,
    chunked_array: List[List[str]],
    expected_results: List[str],
) -> None:
    results = []
    await async_requests_parser._method_in_series(chunked_array, async_page_method, sleep_time=0)

    for chunk in chunked_array:
        if chunk:  # Проверяем только непустые чанки
            result = await async_page_method(chunk)
            results.extend(result)

    assert results == expected_results


@pytest.mark.asyncio
async def test_calculate_random_cookies_headers_index(
    async_requests_parser: AsyncRequestsParserBase,
) -> None:
    cookies = [{"cookie1": "value1"}, {"cookie2": "value2"}]
    headers = [{"header1": "value1"}, {"header2": "value2"}]

    index = await async_requests_parser._calculate_random_cookies_headers_index(cookies, headers)

    assert 0 <= index < 2  # Проверяем, что индекс в пределах допустимого диапазона


@pytest.mark.parametrize(
    "value, match_to_urls, index, urls_length, expected",
    [
        # 1) Передаем не список, а один словарь
        ({"header1": "value1"}, True, 0, 1, {"header1": "value1"}),
        # 2) urls_length не равно количеству словарей в списке
        (
            [{"header1": "value1"}, {"header2": "value2"}],
            True,
            0,
            3,
            {"header1": "value1"},
        ),  # urls_length больше
        (
            [{"header1": "value1"}, {"header2": "value2"}],
            True,
            1,
            1,
            {"header2": "value2"},
        ),  # urls_length меньше
        # 3) Передали один словарь, а urls_length не равно 1
        ({"header1": "value1"}, True, 0, 2, {"header1": "value1"}),  # urls_length больше
        ({"header1": "value1"}, True, 0, 0, {"header1": "value1"}),  # urls_length меньше
        # 4) Проверка на случай, когда список не пустой
        ([{"header1": "value1"}, {"header2": "value2"}], False, 0, 1, None),  # Не привязываем к URL
    ],
)
@pytest.mark.asyncio
async def test_select_value(
    async_requests_parser: AsyncRequestsParserBase,
    value: Any,
    match_to_urls: bool,
    index: int,
    urls_length: int,
    expected: Optional[Any],
) -> None:
    selected_value = async_requests_parser._select_value(
        value, match_to_urls=match_to_urls, index=index, urls_length=urls_length
    )

    # Проверяем, что возвращаемое значение - это одно из значений в списке
    if isinstance(value, list) and value:
        assert selected_value in value
    else:
        assert selected_value == expected


@pytest.mark.parametrize(
    "urls, data, json, expected_url_count, "
    "expected_max_requests, expected_data_list, expected_json_list",
    [
        # Обычный случай
        (
            ["http://example.com", "http://example.org"],
            [{"key": "value1"}, {"key": "value2"}],
            {"key": "value3"},
            2,
            2,
            [{"key": "value1"}, {"key": "value2"}],
            [{"key": "value3"}, {"key": "value3"}],
        ),
        # 1) Количество словарей в списке data не равно количеству ссылок
        (
            ["http://example.com"],
            [{"key": "value1"}, {"key": "value2"}],
            {"key": "value3"},
            1,
            2,
            [{"key": "value1"}, {"key": "value2"}],
            [{"key": "value3"}, {"key": "value3"}],
        ),  # data больше
        # 2) Если в data передали просто словарь, а в json - список
        (
            ["http://example.com"],
            {"key": "value1"},
            [{"key": "value3"}],
            1,
            1,
            [{"key": "value1"}],
            [{"key": "value3"}],
        ),
        # 3) Если передали None в data
        (["http://example.com"], None, {"key": "value3"}, 1, 1, [None], [{"key": "value3"}]),
        # 4) Если передали None в json
        (["http://example.com"], [{"key": "value1"}], None, 1, 1, [{"key": "value1"}], [None]),
        # 5) Если передали None в обоих
        (["http://example.com"], None, None, 1, 1, [None], [None]),
    ],
)
@pytest.mark.asyncio
async def test_prepare_request_data(
    async_requests_parser: AsyncRequestsParserBase,
    urls: List[str],
    data: Optional[List[Dict[str, Any]]],
    json: Optional[Dict[str, Any]],
    expected_url_count: int,
    expected_max_requests: int,
    expected_data_list: List[Optional[Dict[str, Any]]],
    expected_json_list: List[Optional[Dict[str, Any]]],
) -> None:
    (
        url_count,
        max_requests,
        data_list,
        json_list,
    ) = await async_requests_parser._prepare_request_data(urls, data, json)  # type: ignore

    assert url_count == expected_url_count
    assert max_requests == expected_max_requests
    assert data_list == expected_data_list
    assert json_list == expected_json_list


# pytest tests/core/test_async_requests_parser_base.py
