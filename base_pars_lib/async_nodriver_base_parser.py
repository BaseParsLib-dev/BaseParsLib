import asyncio
from typing import Callable

from nodriver.core.browser import Browser
from nodriver.core.tab import Tab

from base_pars_lib.config import logger


class BrowserIsNotInitError(Exception):
    def __init__(self) -> None:
        self.message = 'BrowserIsNotInitError'


class AsyncNodriverBaseParser:
    def __init__(self) -> None:
        self.browser: Browser | None = None

        self.debug: bool | None = None

    async def _backoff_open_new_page(
            self,
            url: str,
            check_page: Callable = None,  # type: ignore[assignment]
            check_page_args: dict | None = None,
            is_page_loaded_check: Callable = None,  # type: ignore[assignment]
            load_timeout: int = 30,
            increase_by_seconds: int = 10,
            iter_count: int = 10,
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

        :return:
            Объект страницы или None в случае, если за все попытки не удалось открыть
        """

        if not self.browser:
            raise BrowserIsNotInitError

        for i in range(1, iter_count + 1):
            page = None
            try:
                await self.browser.get('https://www.google.com')
                page = await self.browser.get(url, new_tab=True)

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
                    logger.backoff_exception(ex=Ex, iteration=i, print_logs=True, url=url)
            await asyncio.sleep(i * increase_by_seconds)

        return None
