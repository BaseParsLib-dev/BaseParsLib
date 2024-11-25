from typing import Any

from selenium.webdriver.support.ui import WebDriverWait


class WebDriverBaseParser:
    def __init__(self, driver: Any, timeout: int = 30) -> None:
        """
        :param driver: Any
            Драйвер селениума или аппиума
        :param timeout:
            Таймаут, который можно использовать в коде,
            чтобы дожидаться появления каких-то объектов
        """

        self.driver = driver
        self.wait = WebDriverWait(self.driver, timeout)
