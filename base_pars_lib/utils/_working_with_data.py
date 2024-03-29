def split_on_chunks_by_chunk_len(array: list | tuple, chunk_len: int):
    """
    Делит массив на чанки в зависимости от переданой длины чанка

    :param array: list | tuple
        Массив, который нужно разделить на чанки
    :param chunk_len: int
        Размер чанка
    """

    for i in range(0, len(array), chunk_len):
        yield array[i: i + chunk_len]


def split_on_chunks_by_count_chunks(array: list | tuple, count_chunks: int):
    """
    Делит массив на чанки в зависимости от переданого количества чанков

    :param array: list | tuple
        Массив, который нужно разделить на чанки
    :param count_chunks: int
        Количество чанков
    """

    chunk_len = -(-len(array) // count_chunks)

    for i in range(0, len(array), chunk_len):
        yield array[i: i + chunk_len]
