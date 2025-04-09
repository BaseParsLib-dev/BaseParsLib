from unittest.mock import Mock, patch

import pytest

from base_pars_lib.core._requests_digest_proxy import (
    HTTPProxyDigestAuth,
    HTTPProxyResponse,
    ProxyError,
)


@pytest.mark.parametrize("method, url", [("GET", "http://example.com")])
@patch("requests.auth.HTTPDigestAuth.build_digest_header")
def test_build_digest_header(
    mock_build_digest_header: Mock, auth: HTTPProxyDigestAuth, method: str, url: str
) -> None:
    auth.build_digest_header(method, url)

    # Проверка, что метод был вызван
    mock_build_digest_header.assert_called_once_with(method, url)


def test_call_method(auth: HTTPProxyDigestAuth, mock_request: Mock) -> None:
    result = auth(mock_request)

    # Проверка, что возвращается запрос
    assert result == mock_request


@pytest.mark.parametrize("mock_read_status_return", [(1, 407, "Proxy Authentication Required")])
@patch("http.client.HTTPResponse._read_status")
def test_read_status(
    mock_read_status: Mock, mock_socket: Mock, mock_read_status_return: tuple
) -> None:
    mock_read_status.return_value = mock_read_status_return

    # Создание экземпляра HTTPProxyResponse
    response = HTTPProxyResponse(mock_socket)

    # Вызов метода
    with pytest.raises(ProxyError):
        response._read_status()


@patch("http.client.HTTPResponse._check_close")
def test_check_close(mock_check_close: Mock, mock_socket: Mock) -> None:
    mock_check_close.return_value = True

    # Создание экземпляра HTTPProxyResponse
    response = HTTPProxyResponse(mock_socket)

    # Вызов метода
    result = response._check_close()

    # Проверка, что метод _check_close возвращает True
    assert result is True


# pytest tests/core/test_requests_digest_proxy.py
