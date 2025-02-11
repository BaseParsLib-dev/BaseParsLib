import asyncio
import os
from typing import Any, Callable, Coroutine

from zendriver.core.browser import Browser
from zendriver.core.tab import Tab, cdp

from base_pars_lib.config import logger
from base_pars_lib.core.async_browsers_parser_base import AsyncBrowsersParserBase


class BrowserIsNotInitError(Exception):
    def __init__(self) -> None:
        self.message = "BrowserIsNotInitError"


class AsyncNodriverBaseParser(AsyncBrowsersParserBase):
    def __init__(
        self, debug: bool = False, print_logs: bool = False, check_exceptions: bool = False
    ) -> None:
        """
        :param debug: bool = False
            Дебаг - вывод в консоль параметров отправляемых запросов и ответов
        :param print_logs: bool = False
            Если False - логи выводятся модулем logging, что не отображается на сервере в journalctl
            Если True - логи выводятся принтами
        :param check_exceptions: bool = False
            Позволяет посмотреть внутренние ошибки библиотеки, отключает все try/except конструкции,
            кроме тех, на которых завязана логика
        """

        super().__init__()

        self.browser: Browser | None = None

        self.debug: bool = False

        self.print_logs: bool = False

        self.cdp_network_handler: Any = cdp.network.RequestWillBeSent

        self.ignore_exceptions = (Exception,)
        self.debug = debug
        self.print_logs = print_logs
        self.check_exceptions = check_exceptions

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
        iter_count: int = 10,
        increase_by_seconds: int = 10,
        ignore_exceptions: tuple | str = "default",
        timeout: int = 30,
    ) -> str | list[str] | None:
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
        :param iter_count: int = 10
            Количество попыток отправки запроса
        :param increase_by_seconds: int = 10
            Значение, на которое увеличивается время ожидания
            на каждой итерации
        :param ignore_exceptions: tuple | str = 'default'
            Возможность передать ошибки, которые будут обрабатываться в backoff.
            Если ничего не передано, обрабатываются дефолтные
        :return:
            Текст с запрашиваемой страницы
        """

        if ignore_exceptions == "default":
            ignore_exceptions = self.ignore_exceptions

        tasks: list = []
        if isinstance(url, list):
            for one_url in url:
                script = await self.__make_js_script(one_url, method, request_body)
                tasks.append(
                    self.__fetch_task(
                        task=page.evaluate(script, await_promise=True),
                        timeout=timeout,
                        iter_count=iter_count,
                        increase_by_seconds=increase_by_seconds,
                        ignore_exceptions=ignore_exceptions,  # type: ignore[arg-type]
                        url_for_logs=one_url,
                    )
                )
        else:
            script = await self.__make_js_script(url, method, request_body)
            tasks.append(
                self.__fetch_task(
                    task=page.evaluate(script, await_promise=True),
                    timeout=timeout,
                    iter_count=iter_count,
                    increase_by_seconds=increase_by_seconds,
                    ignore_exceptions=ignore_exceptions,  # type: ignore[arg-type]
                    url_for_logs=url,
                )
            )

        responses = await asyncio.gather(*tasks)  # type: ignore[return-value]
        if responses and len(responses) == 1:
            return responses[0]
        return responses

    async def __make_js_script(
        self, url: str | list[str], method: str, request_body: str | dict | None = None
    ) -> str:
        script = """
                    fetch("%s", {
                        method: "%s",
                        REQUEST_BODY,
                        headers: {
                            "Content-Type": "application/json;charset=UTF-8"
                        }
                    })
                    .then(response => response.text());
                """ % (url, method)  # noqa: UP031
        if request_body is not None:
            script = script.replace("REQUEST_BODY", f"body: JSON.stringify({request_body})")
        else:
            script = script.replace("REQUEST_BODY,", "")

        if self.debug:
            logger.info_log(f"JS request\n\n{script}", print_logs=self.print_logs)

        return script

    async def __fetch_task(
        self,
        task: Coroutine[Any, Any, Any],
        timeout: int,
        iter_count: int,
        increase_by_seconds: int,
        ignore_exceptions: tuple,
        url_for_logs: str,
    ) -> str | None:
        for i in range(1, iter_count + 1):
            try:
                return await asyncio.wait_for(task, timeout)
            except ignore_exceptions if not self.check_exceptions else () as Ex:
                if self.debug:
                    logger.backoff_exception(Ex, i, self.print_logs, url_for_logs)
                await asyncio.sleep(i * increase_by_seconds)
                continue
        return None

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
