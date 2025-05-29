import asyncio
import os
from typing import Any, Callable

from zendriver.core.browser import Browser
from zendriver.core.tab import Tab, cdp

from base_pars_lib.config import logger
from base_pars_lib.core.async_browsers_parser_base import AsyncBrowsersParserBase
from base_pars_lib.exceptions.browser import BrowserIsNotInitError


class AsyncNodriverBaseParser(AsyncBrowsersParserBase):
    def __init__(self) -> None:
        super().__init__()

        self.browser: Browser | None = None

        self.debug: bool = False

        self.print_logs: bool = False

        self.cdp_network_handler: Any = cdp.network.RequestWillBeSent

    async def _backoff_open_new_page(
        self,
        url: str,
        is_page_loaded_check: Callable,
        check_page: Callable = None,  # type: ignore[assignment]
        check_page_args: dict | None = None,
        load_timeout: int = 30,
        increase_by_seconds: int = 10,
        iter_count: int = 10,
        catch_requests_handler: Callable = None,  # type: ignore[assignment]
        new_tab: bool = True,
        new_window: bool = False,
    ) -> Tab | None:
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
        :param is_page_loaded_check: Callable = None
            Можно передать функцию проверки того, что страница загружена.
            В качестве первого параметра функция обязательно должна принимать объект страницы: Tab
        :param catch_requests_handler: Callable = None
            Если передать метод, он будет срабатывать при каждом запросе от страницы.
            В качестве аргумента принимает request.
            По дефолту запросы перехватывает cdp.network.RequestWillBeSent, но можно
            поменять на другой через параметр self.cdp_network_handler
        :param new_tab: bool = True
            Открыть в новой вкладке
        :param new_window: bool = False
            Открыть в новом окне браузера

        :return:
            Объект страницы или None в случае, если за все попытки не удалось открыть
        """

        if not self.browser:
            raise BrowserIsNotInitError

        for i in range(1, iter_count + 1):
            page = None
            try:
                page = await self.browser.get(url, new_tab=new_tab, new_window=new_window)
                if catch_requests_handler is not None:
                    page.add_handler(self.cdp_network_handler, catch_requests_handler)

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
                if self.debug:
                    logger.backoff_exception(
                        ex=Ex, iteration=i, print_logs=self.print_logs, url=url
                    )
            await asyncio.sleep(i * increase_by_seconds)

        return None

    async def _make_request_from_page(
            self,
            page: Tab,
            url: str | list[str],
            method: str,
            request_body: str | dict | None = None,
            headers: str | dict | None = None,
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
        :return:
            Текст с запрашиваемой страницы
        """

        tasks: list = []
        if isinstance(url, list):
            for one_url in url:
                script = await self._make_js_script(one_url, method, request_body, headers)
                tasks.append(page.evaluate(script, await_promise=True))
        else:
            script = await self._make_js_script(url, method, request_body, headers)
            tasks.append(page.evaluate(script, await_promise=True))

        responses = await asyncio.gather(*tasks)  # type: ignore[return-value]
        if responses and len(responses) == 1 and not isinstance(url, list):
            return responses[0]
        return responses

    @staticmethod
    async def _make_chrome_proxy_extension(host: str, port: int, login: str, password: str) -> str:
        """
        Создаёт расширение с прокси для Nodriver

        :param host: str
            IP-адрес прокси
        :param port: int
            Порт прокси
        :param login: str
            Логин прокси
        :param password: str
            Пароль прокси
        :return:
            возвращает путь к папке с расширением, который
            после нужно зарегистрировать при старте браузера:
            browser_args=['--load-extension=<<PATH>>']
        """

        background_js = """
        var config = {
             mode: "fixed_servers",
             rules: {
             singleProxy: {
                 scheme: "http",
                 host: "%s",
                 port: parseInt(%s)
             },
            bypassList: ["localhost"]
             }
         };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
         return {
             authCredentials: {
                 username: "%s",
                 password: "%s"
             }
         };
        }
        chrome.webRequest.onAuthRequired.addListener(
                 callbackFn,
                 {urls: ["<all_urls>"]},
                 ['blocking']
        );
        """ % (host, port, login, password)  # noqa: UP031

        manifest_json = """
        {
          "version": "1.0.0",
          "manifest_version": 3,
          "name": "Chrome Proxy",
          "permissions": [
            "proxy",
            "tabs",
            "storage",
            "webRequest",
            "webRequestAuthProvider"
          ],
          "host_permissions": [
            "<all_urls>"
          ],
          "background": {
            "service_worker": "background.js"
          },
          "minimum_chrome_version": "22.0.0"
        }
        """

        current_directory = os.path.dirname(os.path.abspath(__file__))
        with open(f"{current_directory}/nodriver_proxy_extension/background.js", "w") as f:
            f.write(background_js)
        with open(f"{current_directory}/nodriver_proxy_extension/manifest.json", "w") as f:
            f.write(manifest_json)

        return f"{current_directory}/nodriver_proxy_extension"
