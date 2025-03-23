from base_pars_lib import WebDriverBaseParser
from base_pars_lib import BaseParser
from unittest.mock import Mock
import pytest


@pytest.fixture(scope="module")
def setup_module():
    # Код для настройки модуля
    yield
    # Код для очистки после тестов


@pytest.fixture
def mock_requests_session(mocker):
    """Создаем мок для requests.Session."""
    return mocker.patch('requests.Session')

@pytest.fixture
def base_parser(mock_requests_session):
    """Создаем экземпляр BaseParser с мок-сессией."""
    return BaseParser(requests_session=mock_requests_session)


@pytest.fixture
def mock_driver():
    """Создаем мок для WebDriver."""
    return Mock()


@pytest.fixture
def web_driver_base_parser(mock_driver):
    """Создаем экземпляр WebDriverBaseParser с мок-драйвером."""
    return WebDriverBaseParser(driver=mock_driver)
