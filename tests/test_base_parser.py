from requests.models import Response
from unittest.mock import Mock, call


def test_make_request_success(base_parser, mock_requests_session):
    # Создание мок ответа
    mock_response = Response()
    mock_response.status_code = 200
    mock_requests_session.request.return_value = mock_response
    params = {
        'method': 'GET',
        'url': 'http://example.com',
    }
    response = base_parser._make_request(params)

    # Проверяем, что метод request был вызван
    mock_requests_session.request.assert_called_once_with(**params)
    assert response.status_code == 200


def test_make_request_failure(base_parser, mock_requests_session):
    # Создание мок ответа с ошибкой
    mock_response = Response()
    mock_response.status_code = 404
    mock_requests_session.request.return_value = mock_response
    params = {
        'method': 'GET',
        'url': 'http://example.com',
    }
    response = base_parser._make_request(params)

    # Проверяем, что метод request был вызван
    mock_requests_session.request.assert_called_once_with(**params)
    assert response.status_code == 404


def test_make_backoff_request_success(base_parser, mock_requests_session):
    # Создание отложенного мок ответа
    mock_response = Response()
    mock_response.status_code = 200
    mock_requests_session.request.return_value = mock_response
    response = base_parser._make_backoff_request(
        url='http://example.com',
        method='GET',
        iter_count=1
    )

    assert response.status_code == 200


def test_make_backoff_request_with_retry(base_parser, mock_requests_session):
    # Создание отложенного мок ответа с ошибкой
    mock_response_500 = Response()
    mock_response_500.status_code = 500
    mock_response_200 = Response()
    mock_response_200.status_code = 200

    # Устанавливаем side_effect для имитации двух 500 и одного 200
    mock_requests_session.request.side_effect = [mock_response_500, mock_response_500, mock_response_200]

    response = base_parser._make_backoff_request(
        url='http://example.com',
        method='GET',
        iter_count=3,
        iter_count_for_50x_errors=2
    )

    assert response.status_code == 200


def test_append_to_bad_urls(base_parser):
    url = 'http://bad-url.com'
    base_parser._append_to_bad_urls(url)
    assert url in base_parser.bad_urls


def test_delete_from_bad_urls(base_parser):
    url = 'http://bad-url.com'
    base_parser._append_to_bad_urls(url)
    base_parser._delete_from_bad_urls(url)
    assert url not in base_parser.bad_urls


def test_get_request_params(base_parser):
    url = 'http://example.com'
    headers = {'User-Agent': 'test-agent'}
    cookies = {'session_id': '12345'}
    params = base_parser._get_request_params(
        url=url,
        compare_headers_and_cookies_indexes=True,
        headers=headers,
        cookies=cookies
    )

    assert params['url'] == url
    assert params['headers'] == headers
    assert params['cookies'] == cookies
    assert 'User-Agent' in params['headers']


def test_threading_method(base_parser):
    # Создаем мок-метод
    mock_method = Mock(side_effect=lambda chunk: chunk)
    chunked_array = [1, 2, 3]

    # Вызываем метод с чанками
    base_parser._threading_method(chunked_array, mock_method)

    # Проверяем, что мок-метод был вызван для каждого чанка
    mock_method.assert_has_calls([call(chunk) for chunk in chunked_array])
    assert mock_method.call_count == len(chunked_array)


# pytest tests/test_base_parser.py
