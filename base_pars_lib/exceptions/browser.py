class BrowserIsNotInitError(Exception):
    def __init__(self) -> None:
        self.message = "BrowserIsNotInitError"
