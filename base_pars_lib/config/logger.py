import inspect
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - message: %(message)s")


def backoff_exception(ex: Exception, iteration: int, print_logs: bool, url: str = "") -> None:
    func_name = __get_caller_name()

    if print_logs:
        print(f"{datetime.now()} - info - {func_name} - {ex}: iter {iteration}: url {url}")
    else:
        logging.info(f"{func_name} - {ex}: iter {iteration}: url {url}")


def backoff_status_code(status_code: int, iteration: int, url: str, print_logs: bool) -> None:
    func_name = __get_caller_name()

    if print_logs:
        print(
            f"{datetime.now()} - "
            f"info - {func_name} - {status_code}: "
            f"iter {iteration}: "
            f"url {url}"
        )
    else:
        logging.info(f"{func_name} - {status_code}: iter {iteration}: url {url}")


def info_log(message: str, print_logs: bool) -> None:
    func_name = __get_caller_name()

    if print_logs:
        print(f"{datetime.now()} - info - {func_name} - {message}")
    else:
        logging.info(f"{func_name} - {message}")


def __get_caller_name() -> str:
    current_frame = inspect.currentframe()
    if current_frame is None:
        return ""

    caller_frame = current_frame.f_back
    if caller_frame is None:
        return ""

    caller_caller_frame = caller_frame.f_back
    if caller_caller_frame is None:
        return ""

    return caller_caller_frame.f_code.co_name
