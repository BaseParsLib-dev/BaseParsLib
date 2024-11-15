def get_data_from_text(
        text: str,
        start_row: str,
        end_row: str,
        cut_start_row: bool = True,
        cut_end_row: bool = True,
) -> str:
    """
    Функция вырезает нужную подстроку из строки

    :param text: str
        Основной текст
    :param start_row: str
        Левая граница, по которой вырезать
    :param end_row: str
        Правая граница, по которой вырезать
    :param cut_start_row: bool = True
        Обрезать левую границу
    :param cut_end_row: bool = True
        Обрезать правую границу
    :return: str
    """

    raw_data = text[text.find(start_row):]
    if cut_start_row:
        raw_data = raw_data[len(start_row):]
    if cut_end_row:
        return raw_data[:raw_data.find(end_row)]
    else:
        return raw_data[:raw_data.find(end_row) + len(end_row)]
