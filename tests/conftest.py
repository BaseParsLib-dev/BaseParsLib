from collections.abc import Generator
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from base_pars_lib import BaseParser, WebDriverBaseParser
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
