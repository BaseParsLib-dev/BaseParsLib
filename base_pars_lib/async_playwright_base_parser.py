import asyncio
from typing import Any, Callable

from fake_useragent import UserAgent
from playwright.async_api import Browser, BrowserContext, Page, Playwright

from base_pars_lib.config import logger


class AsyncPlaywrightBaseParser:

    def __init__(
        self,
        debug: bool = False,
        print_logs: bool = False
    ) -> None:

        self.debug = debug
        self.print_logs = print_logs

        self.user_agent = UserAgent()

        self.context: BrowserContext | None = None
        self.browser: Browser | None = None
        self.playwright: Playwright | None = None

    async def _backoff_open_new_page_on_context(
        self,
        url: str,
        check_page: Callable = None,  # type: ignore[assignment]
        check_page_args: dict | None = None,
        load_timeout: int = 30,
        increase_by_seconds: int = 10,
        iter_count: int = 10,
        with_new_context: bool = False,
        load_img_mp4_mp3: bool = False,
        headless_browser: bool = False,
        load_for_state: str | None = "networkidle",
        load_by_time: float = 0,
        catch_requests_handler: Callable = None,  # type: ignore[assignment]
        viewport_size: dict | None = None,
    ) -> Page | None:
        """
        Открывает страницу по переданному url,
        в случае ошибки открывает повторно через время

        !!! Для работы требуются созданный объект self.playwright: Playwright
        Также, если объекты self.browser: Browser и self.context: BrowserContext
        не созданы, автоматически примется with_new_context, и они создадутся

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
        :param with_new_context: bool = False
            Создать новый контекст для открытия страницы
            (новый браузер с новым плейрайт-контекстом)
        :param load_img_mp4_mp3: bool = False
            Загружать картинки, видео, аудио
        :param headless_browser: bool = False
            Режим отображения браузера
        :param load_for_state: str = "networkidle"
            Загружать страницу до:
            networkidle - прекращения сетевой активности
            load - полной загрузки страницы
            domcontentloaded - загрузки dom
            None - сразу отдаёт страницу
        :param load_by_time: int = 0
            Количество секунд, сколько нужно ждать при переходе по ссылке
        :param catch_requests_handler: Callable = None
            Если передать метод, он будет срабатывать при каждом запросе от страницы.
            В качестве аргумента принимает request
        :param viewport_size: dict | None = None
            Размер окна в формате {"width": 1920, "height": 1080}

        :return:
            Объект страницы или None в случае, если за все попытки не удалось открыть
        """

        if with_new_context or self.context is None:
            await self._generate_new_context(headless_browser)

        old_page: Page | None = None
        for i in range(1, iter_count + 1):
            page: Page | None = None
            try:
                page = await self.context.new_page()  # type: ignore[union-attr]
                if old_page:
                    await old_page.close()
                if viewport_size:
                    await page.set_viewport_size(viewport_size)  # type: ignore[arg-type]

                if catch_requests_handler is not None:
                    page.on('request', catch_requests_handler)
                if not load_img_mp4_mp3:
                    await page.route(
                        '**/*.{png,jpg,jpeg,mp4,mp3}',
                        lambda route: route.abort()
                    )
                await page.goto(url, timeout=load_timeout * 1000)

                if load_for_state is not None:
                    await page.wait_for_load_state(
                        load_for_state,  # type: ignore[arg-type]
                        timeout=load_timeout * 1000
                    )
                await asyncio.sleep(load_by_time)

                if check_page is not None and check_page_args is not None:
                    if await check_page(page, **check_page_args):
                        return page
                    else:
                        old_page = page
                else:
                    return page
            except Exception as Ex:
                if page:
                    await page.close()
                if self.debug:
                    logger.backoff_exception(
                        Ex, print_logs=self.print_logs, iteration=i, url=url
                    )
            await asyncio.sleep(i * increase_by_seconds)

        return None

    async def _generate_new_context(
        self,
        headless_browser: bool,
        user_agent: str | None = None
    ) -> None:
        """
        Создаёт playwright-контекст - открывает браузер с начальной страницей поиска гугл
        (может быть полезно для некоторых сайтов, которые смотрят,
        откуда пользователь перешёл на их сайт)
        :param headless_browser: bool
            Булево значение, в скрытом ли режиме работает браузер
        :param user_agent:
            Можно передать собственный юзер-агент, в противном случае выберится случайный
            юзер-агент для пользователя на ПК
        :return:
            None
        """

        if not user_agent:
            user_agent = await self._get_pc_user_agent()
        if self.debug:
            logger.info_log(user_agent, print_logs=self.print_logs)
        self.browser = await self.playwright.chromium.launch(  # type: ignore[union-attr]
            proxy=self.proxy,  # type: ignore[arg-type]
            headless=headless_browser
        )
        self.context = await self.browser.new_context(user_agent=user_agent)
        page = await self.context.new_page()
        await page.goto('https://www.google.com')

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
        page: Page,
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
