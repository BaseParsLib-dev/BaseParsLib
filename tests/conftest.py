from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp import ClientResponse, ClientSession
from pytest_mock import MockerFixture

from base_pars_lib import (
    AsyncBaseCurlCffiParser,
    AsyncBaseParser,
    BaseParser,
    WebDriverBaseParser,
    AsyncCamoufoxBaseParser
)
from base_pars_lib.core._requests_digest_proxy import HTTPProxyDigestAuth
from base_pars_lib.core.async_browsers_parser_base import AsyncBrowsersParserBase
from base_pars_lib.core.async_requests_parser_base import AsyncRequestsParserBase


@pytest.fixture(scope="module")
def setup_module() -> Generator[None, None, None]:
    # Код для настройки модуля
    yield
    # Код для очистки после тестов


@pytest.fixture
def mock_requests_session(mocker: MockerFixture) -> Mock:
    """Создаем мок для requests.Session."""
    return mocker.patch("requests.Session")


@pytest.fixture
def base_parser(mock_requests_session: Mock) -> BaseParser:
    """Создаем экземпляр BaseParser с мок-сессией."""
    return BaseParser(requests_session=mock_requests_session)


@pytest.fixture
def mock_driver() -> Mock:
    """Создаем мок для WebDriver."""
    return Mock()


@pytest.fixture
def web_driver_base_parser(mock_driver: Mock) -> WebDriverBaseParser:
    """Создаем экземпляр WebDriverBaseParser с мок-драйвером."""
    return WebDriverBaseParser(driver=mock_driver)


@pytest.fixture
def async_requests_parser() -> AsyncRequestsParserBase:
    return AsyncRequestsParserBase()


@pytest.fixture
def async_browsers_parser() -> AsyncBrowsersParserBase:
    return AsyncBrowsersParserBase()


@pytest.fixture
def async_base_parser() -> AsyncBaseParser:
    return AsyncBaseParser(debug=True, print_logs=True, check_exceptions=True)


@pytest.fixture
def mock_response() -> ClientResponse:
    response = MagicMock(spec=ClientResponse)
    response.url = "http://example.com"
    response.status = 200
    response.text.return_value = "test text"
    response.json.return_value = {"key": "value"}
    response.read.return_value = b"raw content"
    return response


@pytest.fixture
def mock_session(mock_response: ClientResponse) -> Generator[MagicMock, None, None]:
    session = MagicMock(spec=ClientSession)

    # Создаем асинхронный контекстный менеджер
    async def request(*args: Any, **kwargs: Any) -> ClientResponse:
        return mock_response

    session.request = AsyncMock(side_effect=request)
    yield session


@pytest.fixture
def mock_request() -> Mock:
    mock = MagicMock()
    mock.method = "GET"
    mock.url = "http://example.com"
    return mock


@pytest.fixture
def auth() -> HTTPProxyDigestAuth:
    username = "user"
    password = "pass"
    return HTTPProxyDigestAuth(username, password)


@pytest.fixture
def mock_socket() -> MagicMock:
    return MagicMock()


@pytest.fixture
def parser() -> AsyncBaseCurlCffiParser:
    return AsyncBaseCurlCffiParser(debug=True, print_logs=True)


@pytest.fixture
def mock_async_session() -> Mock:
    with patch("curl_cffi.requests.AsyncSession") as mock:
        yield mock


@pytest.fixture
def async_base_curl_cffi_parser() -> AsyncBaseCurlCffiParser:
    return AsyncBaseCurlCffiParser(debug=True, print_logs=True)


@pytest.fixture
def async_camoufox_base_parser() -> AsyncCamoufoxBaseParser:
    return AsyncCamoufoxBaseParser()
