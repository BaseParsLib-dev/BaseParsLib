import unittest
from unittest.mock import MagicMock, patch

from base_pars_lib.core._requests_digest_proxy import (
    HTTPProxyDigestAuth,
    HTTPProxyResponse,
    ProxyError,
)


class TestHTTPProxyDigestAuth(unittest.TestCase):
    @patch("requests.auth.HTTPDigestAuth.build_digest_header")
    def test_build_digest_header(self, mock_build_digest_header: MagicMock) -> None:
        # Настройка
        username = "user"
        password = "pass"
        auth = HTTPProxyDigestAuth(username, password)

        # Вызов метода
        url = "http://example.com"
        method = "GET"
        auth.build_digest_header(method, url)

        # Проверка, что метод был вызван
        mock_build_digest_header.assert_called_once_with(method, url)

    def test_call_method(self) -> None:
        # Настройка
        username = "user"
        password = "pass"
        auth = HTTPProxyDigestAuth(username, password)

        # Создание мок-объекта запроса
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url = "http://example.com"

        # Вызов метода
        result = auth(mock_request)

        # Проверка, что возвращается запрос
        self.assertEqual(result, mock_request)


class TestHTTPProxyResponse(unittest.TestCase):
    @patch("http.client.HTTPResponse._read_status")
    def test_read_status(self, mock_read_status: MagicMock) -> None:
        # Настройка
        mock_read_status.return_value = (1, 407, "Proxy Authentication Required")

        # Создание экземпляра HTTPProxyResponse
        mock_socket = MagicMock()
        response = HTTPProxyResponse(mock_socket)

        # Вызов метода
        with self.assertRaises(ProxyError):
            response._read_status()

    @patch("http.client.HTTPResponse._check_close")
    def test_check_close(self, mock_check_close: MagicMock) -> None:
        # Настройка
        mock_check_close.return_value = True

        # Создание экземпляра HTTPProxyResponse
        mock_socket = MagicMock()
        response = HTTPProxyResponse(mock_socket)

        # Вызов метода
        result = response._check_close()

        # Проверка, что метод _check_close возвращает True
        self.assertTrue(result)


# pytest tests/core/test_requests_digest_proxy.py
