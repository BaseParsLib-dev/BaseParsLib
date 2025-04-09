from base_pars_lib.utils import get_data_from_text


def test_get_data_from_text() -> None:
    # Тестирование стандартного случая
    text = "Hello, this is a sample text. Start here. This is the data we want. End here."
    start_row = "Start here."
    end_row = "End here."
    result = get_data_from_text(text, start_row, end_row)
    assert result == " This is the data we want. ", "Ошибка при вырезании подстроки"

    # Тестирование без обрезки левой границы
    result = get_data_from_text(text, start_row, end_row, cut_start_row=False)
    assert (
        result == "Start here. This is the data we want. "
    ), "Ошибка при вырезании подстроки без обрезки левой границы"

    # Тестирование без обрезки правой границы
    result = get_data_from_text(text, start_row, end_row, cut_end_row=False)
    assert (
        result == " This is the data we want. End here."
    ), "Ошибка при вырезании подстроки без обрезки правой границы"

    # Тестирование без обрезки обеих границ
    result = get_data_from_text(text, start_row, end_row, cut_start_row=False, cut_end_row=False)
    assert (
        result == "Start here. This is the data we want. End here."
    ), "Ошибка при вырезании подстроки без обрезки обеих границ"

    # Тестирование случая, когда границы не найдены
    result = get_data_from_text(text, "Not found", "End here.")
    assert result == "", "Ошибка при вырезании подстроки, когда левая граница не найдена"

    result = get_data_from_text(text, "Start here.", "Not found")
    assert (
        result == " This is the data we want. End here"
    ), "Ошибка при вырезании подстроки, когда правая граница не найдена"

    # Тестирование случая, когда обе границы не найдены
    result = get_data_from_text(text, "Not found", "Not found")
    assert result == "", "Ошибка при вырезании подстроки, когда обе границы не найдены"

    # Тестирование пустого текста
    result = get_data_from_text("", "Start", "End")
    assert result == "", "Ошибка при вырезании подстроки из пустого текста"


# pytest tests/utils/test_parser_utils.py
