import asyncio
from typing import Any, Callable

from fake_useragent import UserAgent
from nodriver.core.tab import Tab
from playwright.async_api import Page


class AsyncBrowsersParserBase:
    def __init__(self) -> None:
        self.user_agent = UserAgent()

    async def _get_pc_user_agent(self) -> str:
        while True:
            user_agent = self.user_agent.random
            if (
                'Android' not in user_agent and
                'iPhone' not in user_agent and
                'iPad' not in user_agent
            ):
                return user_agent

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
            chunked_array: list | tuple,
            async_method: Callable,
            sleep_time: int = 0
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
