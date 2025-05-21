from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi.requests.models import Response

from base_pars_lib import AsyncBaseCurlCffiParser

parser = AsyncBaseCurlCffiParser(debug=True, print_logs=True)


@pytest.mark.parametrize(
    "ignore_404, save_bad_urls, expected_status",
    [
        (True, False, 404),
        (False, True, 404),
    ],
)
@pytest.mark.asyncio
async def test_make_backoff_request_various_params(
    ignore_404: bool,
    save_bad_urls: bool,
    expected_status: int,
) -> None:
    urls: List[str] = ["http://example.com/hahahehe"]
    params: Dict[str, Any] = {
        "ignore_404": ignore_404,
        "save_bad_urls": save_bad_urls,
        "iter_count": 2,
        "increase_by_seconds": 0.1
    }

    responses = await parser._make_backoff_request(urls, **params)

    assert len(responses) == 1
    assert responses[0] is not None
    assert responses[0].status_code == expected_status


@pytest.mark.asyncio
async def test_make_backoff_request_success() -> None:
    urls: List[str] = ["http://example.com"]
    responses = await parser._make_backoff_request(urls)

    assert len(responses) == 1
    assert responses[0].status_code == 200  # type: ignore[union-attr]


@patch("curl_cffi.requests.AsyncSession")
@pytest.mark.asyncio
async def test_make_backoff_request_with_retries(mock_async_session: Any) -> None:
    mock_response_500 = MagicMock(spec=Response)
    mock_response_500.status_code = 500
    mock_response_200 = MagicMock(spec=Response)
    mock_response_200.status_code = 200

    mock_async_session.return_value.request = AsyncMock(
        side_effect=[mock_response_500, mock_response_500, mock_response_200]
    )

    urls: List[str] = ["http://example.com"]
    responses = await parser._make_backoff_request(
        urls, iter_count=2, iter_count_for_50x_errors=1
    )

    assert len(responses) == 1
    assert responses[0].status_code == mock_response_200.status_code  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_make_backoff_request_ignore_404() -> None:
    urls: List[str] = ["http://example.com/hihihaha"]
    responses = await parser._make_backoff_request(urls, ignore_404=True)

    assert len(responses) == 1
    assert responses[0].status_code == 404  # type: ignore[union-attr]


# pytest tests/test_async_base_curl_cffi_parser.py
