import unittest
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi.requests.models import Response

from base_pars_lib import AsyncBaseCurlCffiParser


class TestAsyncBaseCurlCffiParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = AsyncBaseCurlCffiParser(debug=True, print_logs=True)

    @patch("curl_cffi.requests.AsyncSession")
    async def test_fetch_success(self, mock_async_session: Any) -> None:
        # Mocking the response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_async_session.return_value.request = AsyncMock(return_value=mock_response)

        url: str = "http://example.com"
        params: Dict[str, Any] = {"headers": {}, "data": None}
        response: Response = await self.parser._AsyncBaseCurlCffiParser__fetch(
            url, mock_async_session, params
        )

        self.assertEqual(response, mock_response)

    @patch("curl_cffi.requests.AsyncSession")
    async def test_fetch_retry_on_404(self, mock_async_session: Any) -> None:
        # Mocking the response to return 404
        mock_response_404 = MagicMock(spec=Response)
        mock_response_404.status_code = 404
        mock_async_session.return_value.request = AsyncMock(
            side_effect=[mock_response_404, mock_response_404]
        )

        url: str = "http://example.com"
        params: Dict[str, Any] = {"headers": {}, "data": None}
        response: Response = await self.parser._AsyncBaseCurlCffiParser__fetch(
            url, mock_async_session, params, ignore_404=True
        )

        assert response == mock_response_404

    @patch("curl_cffi.requests.AsyncSession")
    @pytest.mark.parametrize(
        "ignore_404, ignore_exceptions, save_bad_urls, impersonate, expected_status",
        [
            (True, False, False, False, 404),  # ignore_404 = True, ожидаем 404
            (False, True, False, False, 404),  # ignore_exceptions = True, ожидаем 404
            (False, False, True, False, 404),  # save_bad_urls = True, ожидаем 404
            (False, False, False, True, 404),  # impersonate = True, ожидаем 404
        ],
    )
    async def test_make_backoff_request_various_params(
        self,
        mock_async_session: Any,
        ignore_404: bool,
        ignore_exceptions: bool,
        save_bad_urls: bool,
        impersonate: bool,
        expected_status: int,
    ) -> None:
        # Mocking the response to return 404
        mock_response_404 = MagicMock(spec=Response)
        mock_response_404.status_code = 404
        mock_async_session.return_value.request = AsyncMock(return_value=mock_response_404)

        urls: List[str] = ["http://example.com"]
        params: Dict[str, Any] = {
            "ignore_404": ignore_404,
            "ignore_exceptions": ignore_exceptions,
            "save_bad_urls": save_bad_urls,
            "impersonate": impersonate,
        }

        responses = await self.parser._make_backoff_request(urls, **params)

        assert len(responses) == 1
        assert responses[0] is not None
        assert responses[0].status_code == expected_status

    @patch("curl_cffi.requests.AsyncSession")
    async def test_make_backoff_request_success(self, mock_async_session: Any) -> None:
        # Mocking the response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_async_session.return_value.request = AsyncMock(return_value=mock_response)

        urls: List[str] = ["http://example.com"]
        responses = await self.parser._make_backoff_request(urls)

        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0], mock_response)

    @patch("curl_cffi.requests.AsyncSession")
    async def test_make_backoff_request_with_retries(self, mock_async_session: Any) -> None:
        mock_response_500 = MagicMock(spec=Response)
        mock_response_500.status_code = 500
        mock_response_200 = MagicMock(spec=Response)
        mock_response_200.status_code = 200

        mock_async_session.return_value.request = AsyncMock(
            side_effect=[mock_response_500, mock_response_500, mock_response_200]
        )

        urls: List[str] = ["http://example.com"]
        responses = await self.parser._make_backoff_request(
            urls, iter_count=2, iter_count_for_50x_errors=1
        )

        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0], mock_response_200)

    @patch("curl_cffi.requests.AsyncSession")
    async def test_make_backoff_request_ignore_404(self, mock_async_session: Any) -> None:
        # Mocking the response to return 404
        mock_response_404 = MagicMock(spec=Response)
        mock_response_404.status_code = 404
        mock_async_session.return_value.request = AsyncMock(return_value=mock_response_404)

        urls: List[str] = ["http://example.com"]
        responses = await self.parser._make_backoff_request(urls, ignore_404=True)

        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0], mock_response_404)


# pytest tests/test_async_base_curl_cffi_parser.py
