from typing import Iterator


def split_on_chunks_by_chunk_len(
    array: list | tuple,
    chunk_len: int
) -> Iterator:
    """
    Делит массив на чанки в зависимости от переданой длины чанка

    :param array: list | tuple
        Массив, который нужно разделить на чанки
    :param chunk_len: int
        Размер чанка
    """

    for i in range(0, len(array), chunk_len):
        yield array[i: i + chunk_len]


def split_on_chunks_by_count_chunks(
    array: list | tuple,
    count_chunks: int
) -> Iterator:
    """
    Делит массив на чанки в зависимости от переданого количества чанков

    :param array: list | tuple
        Массив, который нужно разделить на чанки
    :param count_chunks: int
        Количество чанков
    """

    array_length = len(array)
    chunk_size = array_length // count_chunks
    remainder = array_length % count_chunks

    start = 0
    for i in range(count_chunks):
        end = start + chunk_size
        if i < remainder:
            end += 1
        yield array[start:end]
        start = end


def split_dict_on_chunks_by_chunk_len(
    dictionary: dict,
    chunk_len: int
) -> Iterator[dict]:
    """
    Делит словарь на чанки в зависимости от переданой длины чанка

    :param dictionary: dict
        Словарь, который нужно разделить на чанки
    :param chunk_len: int
        Размер чанка
    """
    items = list(dictionary.items())
    for i in range(0, len(items), chunk_len):
        yield dict(items[i:i + chunk_len])
