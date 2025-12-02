# ruff: noqa: UP031

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from fake_useragent import UserAgent
from playwright.async_api import Page
from zendriver.core.tab import Tab

from base_pars_lib.config import logger


@dataclass
class JsResponse:
    text: str | None
    url: str
    exception: Exception | None = None


class AsyncBrowsersParserBase:
    def __init__(self) -> None:
        self.user_agent = UserAgent()

        self.debug = False
        self.print_logs = False

    async def _get_pc_user_agent(self) -> str:
        while True:
            user_agent = self.user_agent.random
            if (
                "Android" not in user_agent
                and "iPhone" not in user_agent
                and "iPad" not in user_agent
            ):
                return user_agent

    async def _make_js_script(
        self,
        url: str,
        method: str,
        request_body: str | dict | list | None = None,
        headers: str | dict | None = None,
        log_request: bool = False,
    ) -> str:
        """
        Возвращает JS-скрипт запроса в виде строки. Для запросов через браузер

        :param url: str
            Ссылка для запроса
        :param method: str
            Метод запроса
        :param request_body: str | dict | list | None = None
            Тело запроса
        :param headers: str | dict | None = None
            Хедеры запроса
        :param log_request: bool = False
            Вывод кода JS-запроса
        :return: str
            JS-скрипт запроса в виде строки
        """
        script = """
                    fetch("%s", {
                        method: "%s",
                        REQUEST_BODY,
                        HEADERS
                    })
                    .then(response => response.text());
                """ % (
            url,
            method,
        )

        if request_body is not None:
            script = script.replace("REQUEST_BODY", f"body: JSON.stringify({request_body})")
        else:
            script = script.replace("REQUEST_BODY,", "")

        if headers is not None:
            script = script.replace("HEADERS", f"headers: {headers}")
        else:
            script = script.replace(
                "HEADERS", 'headers: {"Content-Type": "application/json;charset=UTF-8"}'
            )

        if log_request:
            logger.info_log(f"JS request\n\n{script}", print_logs=self.print_logs)

        return script

    @staticmethod
    async def _async_pages(pages_urls: list | tuple, page_method: Callable) -> tuple[Any]:
        """
        :param pages_urls:
            Страницы, которые будут обрабатываться асинхронно
        :param page_method:
            Метод, который будет применяться для каждой странице
            (например, сбор каких-то данных)
            Обязательно должен принимать url в качестве аргумента
        :return:
        """

        tasks = [page_method(url) for url in pages_urls]
        return await asyncio.gather(*tasks)  # type: ignore[return-value]

    @staticmethod
    async def _method_in_series(
        chunked_array: list | tuple, async_method: Callable, sleep_time: int = 0
    ) -> None:
        """
        Выполняет метод method для каждого чанка последовательно

        :param chunked_array: list | tuple
            Массив из чанков с url-ами или другими данными для запроса
            Чанки созданы для того, чтобы не отправлять слишком много запросов одновременно,
            чанки обрабатываются последовательно, запросы по ссылкам внутри них - одновременно
        :param async_method:
            Асинхронный метод, который работает с чанком из переданного массива
            и сохраняет результаты во внешний массив
        :param sleep_time: int = 0
            Задержка между чанками запросов

        :return:
            None
        """

        for chunk in chunked_array:
            await async_method(chunk)
            await asyncio.sleep(sleep_time)

    @staticmethod
    async def _scroll_to(
        page: Page | Tab,
        from_: int = 0,
        to: int | None = None,
        full_page: bool = False,
        custom_js_code: str | None = None,
    ) -> None:
        """
        Прокручивает страницу вниз на указанное количество пикселов или полностью

        :param page: Page
            Объект страницы
        :param from_: int = 0
            Старт, откуда начинаем прокрутку
        :param to: int | None = None:
            Количество пикселей, на которые скроллим
        :param full_page: bool = False
            Если True, страница прокрутится до конца
        :custom_js_code: str | None = None
            Есть возможность написать собственную логику скроллинга
        :return:
            None
        """

        if custom_js_code:
            await page.evaluate(custom_js_code)
            return None

        smooth = "{behavior: 'smooth'}"
        if full_page:
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight, {smooth})")
            return None
        await page.evaluate(f"window.scrollTo({from_}, {to}, {smooth})")
        return None

    async def _make_request_from_page(
        self,
        page: Page | Tab,
        url: str | list[str],
        method: str,
        request_body: str | dict | list | None = None,
        headers: str | dict | None = None,
        log_request: bool = False,
        return_response_object: bool = False,
        iter_count: int = 10,
        increase_by_seconds: int = 10,
    ) -> str | list[str] | JsResponse | list[JsResponse]:
        """
        Выполняет запрос через JS со страницы

        :param page: Page | Tab
            Объект страницы
        :param url: str | list[str]
            Ссылка
            Если передан список ссылок, запросы отправятся асинхронно
        :param method: str
            HTTP-метод
        :param request_body: str | dict | list | None = None
            Тело запроса
        :param headers: str | dict | None = None
            Хедеры запроса
        :param log_request: bool = False
            Вывод JS-кода запроса
        :param return_response_object: bool = False
            Если True — возвращает список объектов JsResponse(text, url)
        :param iter_count: int = 10
            Кол-во попыток
        :param increase_by_seconds: int = 10
            Кол-во секунд, на которое увеличивается задержка между попытками
        :return:
            Текст с запрашиваемой страницы или объекты JsResponse
        """

        urls: list[str] = url if isinstance(url, list) else [url]

        if isinstance(request_body, list):
            requests_bodies = request_body
        else:
            requests_bodies = [request_body]

        tasks = []
        for i, url in enumerate(urls):
            tasks.append(
                self.__evaluate_with_backoff(
                    one_url=url,
                    iter_count=iter_count,
                    method=method,
                    page=page,
                    increase_by_seconds=increase_by_seconds,
                    request_body=requests_bodies[i] if i < len(requests_bodies) else None,
                    headers=headers,
                    log_request=log_request,
                )
            )

        responses: list[str | Exception | BaseException | None] = list(
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )
        )

        results = []
        for resp, u in zip(responses, urls):
            if isinstance(resp, str):
                results.append(JsResponse(text=resp, url=u))
            elif isinstance(resp, Exception):
                results.append(JsResponse(text=None, url=u, exception=resp))
            else:
                results.append(JsResponse(text=None, url=u))

        if not return_response_object:
            results = [r.text for r in results]

        if isinstance(url, str):
            return results[0]
        return results

    async def __evaluate_with_backoff(
        self,
        one_url: str,
        iter_count: int,
        method: str,
        page: Page | Tab,
        increase_by_seconds: int,
        request_body: str | dict | list | None = None,
        headers: str | dict | None = None,
        log_request: bool = False,
    ) -> str | Exception | None:
        """
        Выполняет JS-запрос через page.evaluate() с повторными попытками.

        :param one_url: str
            URL, на который выполняется запрос.
        :param iter_count: int = 10
            Кол-во попыток
        :param method: str
            HTTP-метод
        :param page: Page | Tab
            Объект страницы
        :param increase_by_seconds: int = 10
            Кол-во секунд, на которое увеличивается задержка между попытками
        :param request_body: str | dict | None = None
            Тело запроса
        :param headers: str | dict | None = None
            Хедеры запроса
        :param log_request: bool = False
            Вывод JS-кода запроса
        :return:
            Текст ответа от JS-запроса или None, если после всех попыток не удалось
            получить результат, `Exception`: если все попытки завершились с ошибкой.
        """
        last_exception: Exception | None = None

        for i in range(1, iter_count + 1):
            try:
                script = await self._make_js_script(
                    url=one_url,
                    method=method,
                    request_body=request_body,
                    headers=headers,
                    log_request=log_request,
                )
                if isinstance(page, Tab):
                    return await page.evaluate(script, await_promise=True)
                else:
                    return await page.evaluate(script)
            except Exception as Ex:
                last_exception = Ex
                if self.debug:
                    logger.backoff_exception(
                        Ex, url=one_url, iteration=i, print_logs=self.print_logs
                    )
            if i < iter_count:
                await asyncio.sleep(i * increase_by_seconds)
        return last_exception
