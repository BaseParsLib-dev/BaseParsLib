from unittest.mock import MagicMock, Mock

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from base_pars_lib.webdriver_base_parser import WebDriverBaseParser


def test_initialization(web_driver_base_parser: WebDriverBaseParser, mock_driver: Mock) -> None:
    """Тестируем инициализацию WebDriverBaseParser."""
    assert web_driver_base_parser.driver == mock_driver
    assert isinstance(web_driver_base_parser.wait, WebDriverWait)


def test_get_element_with_wait_success(
    web_driver_base_parser: WebDriverBaseParser, mock_driver: Mock
) -> None:
    """Тестируем успешное получение элемента с ожиданием."""
    mock_element = MagicMock()
    mock_driver.find_element.return_value = mock_element

    # Создание мок для условия ожидания
    expected_condition = Mock(return_value=mock_element)
    ec.presence_of_element_located = Mock(return_value=expected_condition)

    # Настройка ожидания
    web_driver_base_parser.wait.until = Mock(return_value=mock_element)

    by = By.ID
    element = "test_id"

    result = web_driver_base_parser._get_element_with_wait(by, element)

    # Проверяем, что метод wait.until был вызван с правильными аргументами
    expected_call = expected_condition
    web_driver_base_parser.wait.until.assert_called_once_with(expected_call)
    assert result == mock_element


def test_get_element_with_wait_timeout(
    web_driver_base_parser: WebDriverBaseParser, mock_driver: Mock
) -> None:
    """Тестируем ситуацию, когда элемент не найден в течение таймаута."""
    by = By.ID
    element = "test_id"

    # Настраиваем ожидание, чтобы оно вызывало исключение TimeoutError
    web_driver_base_parser.wait.until = Mock(side_effect=TimeoutError)

    with pytest.raises(TimeoutError):
        web_driver_base_parser._get_element_with_wait(by, element)

    # Проверяем, что метод wait.until был вызван
    expected_call = ec.presence_of_element_located((by, element))
    web_driver_base_parser.wait.until.assert_called_once_with(expected_call)


# pytest tests/test_webdriver_base_parser.py
