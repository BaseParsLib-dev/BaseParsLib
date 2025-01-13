import asyncio
import random
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Callable

from curl_cffi.requests.models import Response

from base_pars_lib.config import logger


@dataclass
class AiohttpResponse:
    text: str
    json: dict | None
    url: str
    status_code: int


class AsyncRequestsParserBase:
    def __init__(self) -> None:
        self.debug: bool = False

        self.print_logs: bool = False

        self.bad_urls: list[Any] = []

    async def _check_response(
            self,
            response: None | AiohttpResponse | Response,
            iteration: int,
            url: str,
            increase_by_seconds: int,
            iter_count: int,
            save_bad_urls: bool,
            ignore_404: bool,
            long_wait_for_50x: bool,
            iteration_for_50x: int,
            iter_count_for_50x_errors: int,
            increase_by_minutes_for_50x_errors: int
    ) -> tuple[bool, None | AiohttpResponse | Response]:
        """
        Метод выполняется в теле цикла и проверяет респонз. Позвращает кортеж, в котором:
            bool - завершать цикл или нет (валидный респонз или нет)
            AiohttpResponse | Response - сам респонз
        """

        if response is None:
            if self.debug:
                logger.info_log(f'response is None, iter: {iteration}, {url}', self.print_logs)
            await asyncio.sleep(iteration * increase_by_seconds)
            return False, None

        if response.status_code == HTTPStatus.OK or iteration == iter_count:
            if save_bad_urls:
                await self._delete_from_bad_urls(url)
            return True, response
        if save_bad_urls and response.status_code != HTTPStatus.NOT_FOUND:
            await self._append_to_bad_urls(url)
        if response.status_code == HTTPStatus.NOT_FOUND and ignore_404:
            return True, response

        if 599 >= response.status_code >= 500 and long_wait_for_50x:
            if iteration_for_50x > iter_count_for_50x_errors:
                return True, response
            iteration_for_50x += 1
            if self.debug:
                logger.backoff_status_code(
                    response.status_code, iteration, url, self.print_logs
                )
            await asyncio.sleep(iteration * increase_by_minutes_for_50x_errors * 60)
            return False, None

        if response.status_code != HTTPStatus.OK:
            if self.debug:
                logger.backoff_status_code(
                    response.status_code, iteration, url, self.print_logs
                )
            await asyncio.sleep(iteration * increase_by_seconds)

        return False, None

    async def _append_to_bad_urls(self, url: Any) -> None:
        if url not in self.bad_urls:
            self.bad_urls.append(url)

    async def _delete_from_bad_urls(self, url: Any) -> None:
        if url in self.bad_urls:
            self.bad_urls.remove(url)

    async def _get_by_random_index(
            self,
            item: list[dict] | dict,
            random_index: int,
            item_name: str
    ) -> dict:
        if type(item) is list:
            item = item[random_index]
            if self.debug:
                logger.info_log(f'{item_name} index: {random_index}', self.print_logs)
        return item  # type: ignore[return-value]

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
    async def _calculate_random_cookies_headers_index(
            cookies: list[dict] | dict,
            headers: list[dict] | dict
    ) -> int:
        upper_index = min(len(cookies), len(headers))
        if not upper_index:
            upper_index = max(len(cookies), len(headers))
        try:
            return random.randint(0, upper_index - 1)
        except ValueError:
            return 0
