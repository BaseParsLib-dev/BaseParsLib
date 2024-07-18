import asyncio
from typing import Any, Callable


class AsyncPlaywrightBaseParser:

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
