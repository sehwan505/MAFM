"""파일 연산 모듈.

C 라이브러리를 사용한 파일 연산 기능을 제공합니다.
"""

import ctypes
from tempfile import TemporaryDirectory
from typing import Any

lib = ctypes.CDLL("./rag/C_library/libfileops.so")

lib.make_soft_links.argtypes = [
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.c_int,
    ctypes.c_char_p,
]
lib.make_soft_links.restype = ctypes.c_char_p


def make_soft_links(paths: list[str], temp_dir: TemporaryDirectory[str]) -> str:
    """소프트 링크를 생성합니다.

    Args:
        paths: 링크를 생성할 파일 경로 리스트.
        temp_dir: 링크를 생성할 임시 디렉토리.

    Returns:
        생성 결과 메시지.
    """
    path_array = (ctypes.c_char_p * len(paths))(
        *[path.encode("utf-8") for path in paths]
    )
    result = lib.make_soft_links(path_array, len(paths), temp_dir.name.encode("utf-8"))
    return result.decode("utf-8")


lib.get_file_data.argtypes = [ctypes.c_char_p]
lib.get_file_data.restype = ctypes.POINTER(ctypes.c_char_p)


def get_file_data(path: str) -> list[str]:
    """파일 데이터를 읽습니다.

    Args:
        path: 읽을 파일의 경로.

    Returns:
        파일 데이터 문자열 리스트.
    """
    result = lib.get_file_data(path.encode("utf-8"))
    data_list: list[str] = []
    idx = 0

    while result[idx] is not None:
        string = ctypes.string_at(result[idx]).decode("utf-8")
        data_list.append(string)
        idx += 1
    return data_list


lib.get_all_file_data.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
lib.get_all_file_data.restype = ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))

lib.free_file_data_array.restype = None
lib.free_file_data_array.argtypes = [
    ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p)),
    ctypes.c_int,
]


def get_all_file_data(directory: str) -> list[list[Any]]:
    """디렉토리 내 모든 파일 데이터를 읽습니다.

    Args:
        directory: 읽을 디렉토리 경로.

    Returns:
        각 파일의 데이터 리스트.
    """
    num_files = ctypes.c_int(0)
    result = lib.get_all_file_data(directory.encode("utf-8"), ctypes.byref(num_files))
    files: list[list[Any]] = []
    try:
        for i in range(num_files.value):
            idx = 0
            data_list: list[Any] = []
            while result[i][idx] is not None:
                try:
                    string = ctypes.string_at(result[i][idx]).decode("utf-8")
                except UnicodeDecodeError:
                    string = ctypes.string_at(result[i][idx])
                data_list.append(string)
                idx += 1
            files.append(data_list)
        return files
    finally:
        result_casted = ctypes.cast(
            result, ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
        )
        lib.free_file_data_array(result_casted, num_files.value)