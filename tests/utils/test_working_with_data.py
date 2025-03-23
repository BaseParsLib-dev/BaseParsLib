from base_pars_lib.utils._working_with_data import (
    split_on_chunks_by_chunk_len,
    split_on_chunks_by_count_chunks,
    split_dict_on_chunks_by_chunk_len,
)

# Тесты для split_on_chunks_by_chunk_len
def test_split_on_chunks_by_chunk_len():
    # Тестирование деления списка на чанки длиной 2
    result = list(split_on_chunks_by_chunk_len([1, 2, 3, 4, 5], 2))
    assert result == [[1, 2], [3, 4], [5]], "Ошибка при делении на чанки по длине"

    # Тестирование деления кортежа на чанки длиной 3
    result = list(split_on_chunks_by_chunk_len((1, 2, 3, 4, 5), 3))
    assert result == [(1, 2, 3), (4, 5)], "Ошибка при делении на чанки по длине для кортежа"

    # Тесты для пустого массива
    result = list(split_on_chunks_by_chunk_len([], 2))
    assert result == [], "Ошибка при делении пустого массива на чанки"

    # Тесты для длины чанка больше длины массива
    result = list(split_on_chunks_by_chunk_len([1, 2], 5))
    assert result == [[1, 2]], "Ошибка при делении на чанки, когда длина чанка больше длины массива"


# Тесты для split_on_chunks_by_count_chunks
def test_split_on_chunks_by_count_chunks():
    # Тестирование деления списка на 2 чанка
    result = list(split_on_chunks_by_count_chunks([1, 2, 3, 4, 5], 2))
    assert result == [[1, 2, 3], [4, 5]], "Ошибка при делении на чанки по количеству чанков"

    # Тестирование деления списка на 3 чанка
    result = list(split_on_chunks_by_count_chunks([1, 2, 3, 4, 5], 3))
    assert result == [[1, 2], [3, 4], [5]], "Ошибка при делении на чанки по количеству чанков"

    # Тесты для пустого массива
    result = list(split_on_chunks_by_count_chunks([], 2))
    assert result == [[], []], "Ошибка при делении пустого массива на чанки"

    # Тесты для количества чанков больше длины массива
    result = list(split_on_chunks_by_count_chunks([1, 2], 5))
    assert result == [[1], [2], [], [], []], "Ошибка при делении на чанки, когда количество чанков больше длины массива"


# Тесты для split_dict_on_chunks_by_chunk_len
def test_split_dict_on_chunks_by_chunk_len():
    # Тестирование деления списка на 2 чанка
    result = list(split_dict_on_chunks_by_chunk_len({'a': 1, 'b': 2, 'c': 3}, 2))
    assert result == [{'a': 1, 'b': 2}, {'c': 3}], "Ошибка при делении словаря на чанки по длине"

    # Тестирование деления списка на 3 чанка
    result = list(split_dict_on_chunks_by_chunk_len({'a': 1, 'b': 2, 'c': 3, 'd': 4}, 3))
    assert result == [{'a': 1, 'b': 2, 'c': 3}, {'d': 4}], "Ошибка при делении словаря на чанки по длине"

    # Тесты для пустого словаря
    result = list(split_dict_on_chunks_by_chunk_len({}, 2))
    assert result == [], "Ошибка при делении пустого словаря на чанки"

    # Тесты для длины чанка больше количества элементов в словаре
    result = list(split_dict_on_chunks_by_chunk_len({'a': 1, 'b': 2}, 5))
    assert result == [{'a': 1, 'b': 2}], "Ошибка при делении на чанки, когда длина чанка больше количества элементов в словаре"


# pytest tests/utils/test_working_with_data.py
