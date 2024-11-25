from typing import Any

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.expected_conditions import WebDriver, WebElement


class WebDriverBaseParser:
    def __init__(self, driver: WebDriver, timeout: int = 30) -> None:
        """
        :param driver: WebDriver
            Драйвер селениума или аппиума
        :param timeout:
            Таймаут, который можно использовать в коде,
            чтобы дожидаться появления каких-то объектов
        """

        self.driver = driver
        self.wait = WebDriverWait(self.driver, timeout)

    def _get_element_with_wait(self, by: str, element: str) -> WebElement:
        """
        Получает элемент по какому-либо селениум-тегу (ID, название и т.д.)
        :param by:
            Селениум-тег. Можно передать, например AppiumBy.ID из
            from appium.webdriver.common.appiumby import AppiumBy
        :param element:
            Сам тег
        :return:
            WebElement
        """

        return self.wait.until(
            expected_conditions.presence_of_element_located((by, element))
        )
