import asyncio
import random
from typing import Any, Callable

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, Page

from base_pars_lib.config import logger
from base_pars_lib.core.async_browsers_parser_base import AsyncBrowsersParserBase
from base_pars_lib.exceptions.browser import BrowserIsNotInitError


class AsyncCamoufoxBaseParser(AsyncBrowsersParserBase):
    def __init__(self) -> None:
        super().__init__()

        self.browser: Browser | None = None
        self.browser_manager: AsyncCamoufox | None = None

        self.debug: bool = False

        self.print_logs: bool = False

    async def _backoff_create_browser(
            self,
            proxy: list[dict] | dict[str, str] | None = None,
            headless: bool | str = "virtual",
            os: str = "linux",
            geoip: bool = True,
            increase_by_seconds: int = 10,
            iter_count: int = 10,
    ) -> Browser | None:
        """
        Создаёт браузер-менеджер и браузер

        :param proxy: list[dict[str, str]] | dict[str, str] | None
            Прокси в формате:
            {
                "server": f"http://<host>:<port>",
                "username": <login>,
                "password": <password>,
            }
        :param headless: bool | str = "virtual"
            Показывать или не показывать окно браузера, значение
            virtual (поддерживается только в linux)
            создаёт виртуальный дисплей, что позволяет эмулировать экран в системе
        :param os: str = "linux"
            Возможность подменить ОС
        :param geoip: bool = True
            Браузер будет использовать долготу, ширину, часовой пояс, страну,
            локаль переданного прокси
        :param increase_by_seconds: int = 10
            Кол-во секунд, на которое увеличивается задержка между попытками
        :param iter_count: int = 10
            Кол-во попыток
        :return: Объект браузера
        """

        if isinstance(proxy, list):
            proxy = random.choice(proxy)

        for i in range(1, iter_count + 1):
            try:
                self.browser_manager = AsyncCamoufox(
                    headless=headless,
                    os=os,
                    geoip=geoip,
                    proxy=proxy,
                )
                await self.browser_manager.__aenter__()
                self.browser = self.browser_manager.browser  # type: ignore[assignment]
                return self.browser  # type: ignore[return-value]
            except Exception as Ex:
                if self.debug:
                    logger.backoff_exception(Ex, iteration=i, print_logs=self.print_logs)
                await asyncio.sleep(i * increase_by_seconds)

        return None

    async def _close_browser(self) -> None:
        if self.browser_manager is not None:
            await self.browser_manager.__aexit__()
            self.browser_manager = None
        if self.browser is not None:
            await self.browser.close()
            self.browser = None
        return None

    async def _backoff_open_new_page(
            self,
            url: str,
            is_page_loaded_check: Callable,
            page: Page | None = None,
            check_page: Callable = None,  # type: ignore[assignment]
            check_page_args: dict | None = None,
            load_timeout: int = 30,
            increase_by_seconds: int = 10,
            iter_count: int = 10,
            **new_page_kwargs: Any,
    ) -> Page | None:
        """
        Открывает страницу по переданному url,
        в случае ошибки открывает повторно через время

        !!! Для работы требуются созданный объект self.browser: Browser
        Если не создан, будет получена ошибка BrowserIsNotInitException

        :param url: str
            Ссылка на страницу
        :param check_page: Callable = None
            Можно передать асинхронную функцию, в которой будут дополнительные проверки страницы
            (например на то, страница с капчей ли это)
            Функция обязательно должна принимать объект страницы плейрайт (Page) и возвращать
            True или False, где True - вернуть страницу, False - попытаться открыть заново
        :param check_page_args: dict = None
            Дополнительные параметры для check_page
        :param load_timeout: int = 30
            Таймаут для загрузки страницы
        :param increase_by_seconds: int = 10
            Кол-во секунд, на которое увеличивается задержка между попытками
        :param iter_count: int = 10
            Кол-во попыток
        :param is_page_loaded_check: Callable
            Можно передать функцию проверки того, что страница загружена.
            В качестве первого параметра функция обязательно должна принимать объект страницы: Tab
        :param new_page_kwargs:
            Дополнительные аргументы для new_page()
        :param page: Page | None = None
            Возможность передать страницу, чтобы открыть новую вместо неё
            (т.к. new_page создаёт новый объект браузера)
        :return:
            Объект страницы или None в случае, если за все попытки не удалось открыть
        """

        if not self.browser:
            raise BrowserIsNotInitError

        for i in range(1, iter_count + 1):
            try:
                if page is None:
                    page = await self.browser.new_page(**new_page_kwargs)
                await page.goto(url)

                for _ in range(load_timeout):
                    if await is_page_loaded_check(page):
                        break
                    await asyncio.sleep(1)

                if check_page is not None and check_page_args is not None:
                    if await check_page(page, **check_page_args):
                        return page
                    else:
                        await page.close()
                        continue
                else:
                    return page

            except Exception as Ex:
                if page:
                    await page.close()
                    page = None
                if self.debug:
                    logger.backoff_exception(
                        ex=Ex, iteration=i, print_logs=self.print_logs, url=url
                    )
            await asyncio.sleep(i * increase_by_seconds)

        return None

    async def _make_request_from_page(
            self,
            page: Page,
            url: str | list[str],
            method: str,
            request_body: str | dict | list | None = None,
            headers: str | dict | None = None,
            log_request: bool = False,
    ) -> str | list[str]:
        """
        Выполняет запрос через JS со страницы

        :param page: Tab
            Объект страницы
        :param url: str | list[str]
            Ссылка
            Если передан список ссылок, запросы отправятся асинхронно
        :param method: str
            HTTP-метод
        :param request_body: str | dict | None = None
            Тело запроса
        :param headers: str | dict | None = None
            Хедеры запроса
        :param log_request: bool = False
            Вывод JS-кода запроса
        :return:
            Текст с запрашиваемой страницы
        """

        tasks: list = []
        if isinstance(url, list):
            for one_url in url:
                script = await self._make_js_script(
                    url=one_url,
                    method=method,
                    request_body=request_body,
                    headers=headers,
                    log_request=log_request,
                )
                tasks.append(page.evaluate(script))
        else:
            script = await self._make_js_script(
                url=url,
                method=method,
                request_body=request_body,
                headers=headers,
                log_request=log_request,
            )
            tasks.append(page.evaluate(script))

        responses = await asyncio.gather(*tasks)  # type: ignore[return-value]
        if responses and len(responses) == 1 and not isinstance(url, list):
            return responses[0]
        return responses
