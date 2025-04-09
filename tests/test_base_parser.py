from typing import Any, Dict, List
from unittest.mock import Mock, call

import pytest
from requests.models import Response

from base_pars_lib.base_parser import BaseParser


@pytest.mark.parametrize(
    "status_code, expected_status",
    [
        (200, 200),  # Успешный запрос
        (404, 404),  # Неуспешный запрос
    ],
)
def test_make_request(
    base_parser: BaseParser, mock_requests_session: Mock, status_code: int, expected_status: int
) -> None:
    # Создание мок ответа
    mock_response = Response()
    mock_response.status_code = status_code
    mock_requests_session.request.return_value = mock_response
    params: Dict[str, str] = {
        "method": "GET",
        "url": "http://example.com",
    }
    response = base_parser._make_request(params)

    # Проверяем, что метод request был вызван
    mock_requests_session.request.assert_called_once_with(**params)
    assert response.status_code == expected_status


def test_make_backoff_request_success(base_parser: BaseParser, mock_requests_session: Mock) -> None:
    # Создание отложенного мок ответа
    mock_response = Response()
    mock_response.status_code = 200
    mock_requests_session.request.return_value = mock_response
    response = base_parser._make_backoff_request(
        url="http://example.com", method="GET", iter_count=1
    )

    assert response.status_code == 200


def test_make_backoff_request_with_retry(
    base_parser: BaseParser, mock_requests_session: Mock
) -> None:
    # Создание отложенного мок ответа с ошибкой
    mock_response_500 = Response()
    mock_response_500.status_code = 500
    mock_response_200 = Response()
    mock_response_200.status_code = 200

    # Устанавливаем side_effect для имитации двух 500 и одного 200
    mock_requests_session.request.side_effect = [
        mock_response_500,
        mock_response_500,
        mock_response_200,
    ]

    response = base_parser._make_backoff_request(
        url="http://example.com", method="GET", iter_count=3, iter_count_for_50x_errors=2
    )

    assert response.status_code == 200


def test_append_to_bad_urls(base_parser: BaseParser) -> None:
    url: str = "http://bad-url.com"
    base_parser._append_to_bad_urls(url)
    assert url in base_parser.bad_urls


def test_delete_from_bad_urls(base_parser: BaseParser) -> None:
    url: str = "http://bad-url.com"
    base_parser._append_to_bad_urls(url)
    base_parser._delete_from_bad_urls(url)
    assert url not in base_parser.bad_urls


def test_get_request_params(base_parser: BaseParser) -> None:
    url: str = "http://example.com"
    headers: dict[str, str] = {"User-Agent": "test-agent"}
    cookies: dict[str, str] = {"session_id": "12345"}
    params = base_parser._get_request_params(
        url=url, compare_headers_and_cookies_indexes=True, headers=headers, cookies=cookies
    )

    assert params["url"] == url
    assert params["headers"] == headers
    assert params["cookies"] == cookies
    assert "User-Agent" in params["headers"]


def test_threading_method(base_parser: BaseParser) -> None:
    # Создаем мок-метод
    mock_method = Mock(side_effect=lambda chunk: chunk)
    chunked_array: list[int] = [1, 2, 3]

    # Вызываем метод с чанками
    base_parser._threading_method(chunked_array, mock_method)

    # Проверяем, что мок-метод был вызван для каждого чанка
    mock_method.assert_has_calls([call(chunk) for chunk in chunked_array])
    assert mock_method.call_count == len(chunked_array)


def test_get_by_random_index_with_list(base_parser: BaseParser) -> None:
    item: List[Dict[str, str]] = [{"key1": "value1"}, {"key2": "value2"}, {"key3": "value3"}]
    result = base_parser._get_by_random_index(item, None, "TestItem")

    # Проверяем, что результат находится в списке
    assert result in item


@pytest.mark.parametrize(
    "cookies, headers, expected_index",
    [
        (
            [{"cookie1": "value1"}, {"cookie2": "value2"}],
            [{"header1": "value1"}, {"header2": "value2"}, {"header3": "value3"}],
            0,
        ),  # Ожидаем, что индекс будет в пределах
        ([], [], 0),  # Пустые списки
        ([{"cookie1": "value1"}], [], 0),  # Один пустой список
    ],
)
def test_calculate_random_cookies_headers_index(
    base_parser: BaseParser,
    cookies: List[Dict[str, str]],
    headers: List[Dict[str, str]],
    expected_index: int,
) -> None:
    index = base_parser._calculate_random_cookies_headers_index(cookies, headers)

    # Проверяем, что индекс находится в допустимых пределах
    assert index == expected_index


def test_make_request_with_valid_params(base_parser: BaseParser) -> None:
    # Тестируем метод _make_request с корректными параметрами
    params: Dict[str, Any] = {
        "method": "GET",
        "url": "http://example.com",
        "headers": {},
        "cookies": {},
        "verify": True,
    }

    # Настраиваем мок-сессию для возврата успешного ответа
    mock_response = Mock()
    mock_response.status_code = 200
    base_parser.requests_session.request.return_value = mock_response

    response = base_parser._make_request(params)

    # Проверяем, что метод возвращает объект response
    assert response.status_code == 200


def test_make_request_with_invalid_params(base_parser: BaseParser) -> None:
    params: Dict[str, Any] = {
        "method": "INVALID_METHOD",  # Некорректный HTTP метод
        "url": "http://example.com",
        "headers": {},
        "cookies": {},
        "verify": True,
    }

    # Настраиваем мок-сессию для возврата ошибки
    base_parser.requests_session.request.side_effect = ValueError("Invalid HTTP method")

    with pytest.raises(ValueError, match="Invalid HTTP method"):
        base_parser._make_request(params)


# pytest tests/test_base_parser.py
