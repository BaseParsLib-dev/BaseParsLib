import asyncio
from typing import Any, Callable

from playwright.async_api import Browser, Page

from base_pars_lib.config import logger
from base_pars_lib.exceptions.browser import BrowserIsNotInitError


class AsyncCamoufoxBaseParser:
    def __init__(self) -> None:
        self.browser: Browser | None = None

        self.debug: bool = False

        self.print_logs: bool = False

    async def _backoff_open_new_page(
        self,
        url: str,
        is_page_loaded_check: Callable,
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
        :param is_page_loaded_check: Callable = None
            Можно передать функцию проверки того, что страница загружена.
            В качестве первого параметра функция обязательно должна принимать объект страницы: Tab
        :param new_page_kwargs:
            Дополнительные аргументы для new_page()
        :return:
            Объект страницы или None в случае, если за все попытки не удалось открыть
        """

        if not self.browser:
            raise BrowserIsNotInitError

        for i in range(1, iter_count + 1):
            page = None
            try:
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
        request_body: str | dict | None = None,
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
        :return:
            Текст с запрашиваемой страницы
        """

        tasks: list = []
        if isinstance(url, list):
            for one_url in url:
                script = await self.__make_js_script(one_url, method, request_body)
                tasks.append(page.evaluate(script))
        else:
            script = await self.__make_js_script(url, method, request_body)
            tasks.append(page.evaluate(script))

        responses = await asyncio.gather(*tasks)  # type: ignore[return-value]
        if responses and len(responses) == 1 and not isinstance(url, list):
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
                """ % (  # noqa: UP031
            url,
            method,
        )
        if request_body is not None:
            script = script.replace(
                "REQUEST_BODY", f"body: JSON.stringify({request_body})"
            )
        else:
            script = script.replace("REQUEST_BODY,", "")

        if self.debug:
            logger.info_log(f"JS request\n\n{script}", print_logs=self.print_logs)

        return script
