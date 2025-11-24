"""파일 연산 모듈.

파일 읽기 및 소프트 링크 생성 기능을 제공합니다.
"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

DEFAULT_CHUNK_SIZE = 500
BINARY_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".mp4", ".avi", ".mp3", ".wav", ".pdf"}


def _is_binary_file(path: str) -> bool:
    """바이너리 파일인지 확인합니다.

    Args:
        path: 확인할 파일 경로.

    Returns:
        바이너리 파일이면 True.
    """
    ext = Path(path).suffix.lower()
    return ext in BINARY_EXTENSIONS


def make_soft_links(paths: list[str], temp_dir: TemporaryDirectory[str]) -> str:
    """소프트 링크를 생성합니다.

    Args:
        paths: 링크를 생성할 파일 경로 리스트.
        temp_dir: 링크를 생성할 임시 디렉토리.

    Returns:
        임시 디렉토리 경로.
    """
    for path in paths:
        filename = os.path.basename(path)
        link_path = os.path.join(temp_dir.name, filename)
        try:
            os.symlink(path, link_path)
        except FileExistsError:
            pass
        except OSError as e:
            print(f"Failed to create symlink for {path}: {e}")

    return temp_dir.name


def get_file_data(path: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[str]:
    """파일 데이터를 읽고 청크로 분할합니다.

    파일을 읽어서 [파일경로, 파일명, 청크1, 청크2, ...] 형태로 반환합니다.
    바이너리 파일(이미지, 비디오 등)은 청크 없이 [파일경로, 파일명]만 반환합니다.

    Args:
        path: 읽을 파일의 경로.
        chunk_size: 각 청크의 크기 (기본값: 500).

    Returns:
        파일 데이터 리스트. [경로, 파일명, 청크들...]
    """
    filename = os.path.basename(path)
    data: list[str] = [path, filename]

    if _is_binary_file(path):
        return data

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
        data.extend(chunks)

    except OSError as e:
        print(f"Failed to read file {path}: {e}")

    return data


def get_all_file_data(
    directory: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_depth: int = 3,
) -> list[list[str]]:
    """디렉토리 내 모든 파일 데이터를 읽습니다.

    Args:
        directory: 읽을 디렉토리 경로.
        chunk_size: 각 청크의 크기.
        max_depth: 탐색할 최대 깊이.

    Returns:
        각 파일의 데이터 리스트.
    """
    files: list[list[str]] = []

    def _collect_recursive(dir_path: str, depth: int) -> None:
        if depth > max_depth:
            return

        try:
            with os.scandir(dir_path) as entries:
                for entry in entries:
                    if entry.name.startswith("."):
                        continue

                    if entry.is_file():
                        file_data = get_file_data(entry.path, chunk_size)
                        files.append(file_data)
                    elif entry.is_dir():
                        _collect_recursive(entry.path, depth + 1)
        except OSError as e:
            print(f"Failed to read directory {dir_path}: {e}")

    _collect_recursive(directory, 1)
    return files