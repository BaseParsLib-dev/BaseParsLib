import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - func: %(funcName)s - message: %(message)s'
)


def backoff_exception(ex: Exception, iteration: int, print_logs: bool, url: str = "") -> None:
    if print_logs:
        print(f'{datetime.now()} - info - backoff_exception - {ex}: iter {iteration}: url {url}')
    else:
        logging.info(f'{ex}: iter {iteration}: url {url}')


def backoff_status_code(status_code: int, iteration: int, url: str, print_logs: bool) -> None:
    if print_logs:
        print(
            f'{datetime.now()} - '
            f'info - backoff_status_code - {status_code}: '
            f'iter {iteration}: '
            f'url {url}'
        )
    else:
        logging.info(f'{status_code}: iter {iteration}: url {url}')


def info_log(message: str, print_logs: bool) -> None:
    if print_logs:
        print(f'{datetime.now()} - info - info_log - {message}')
    else:
        logging.info(message)
