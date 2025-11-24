"""파일 시스템 감시 모듈.

Watchdog을 사용하여 파일 시스템 변경을 모니터링합니다.
"""

import argparse
import os
import time

import pdfplumber
from docx import Document
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from mafm.rag.embedding import initialize_model
from mafm.rag.fileops import get_file_data
from mafm.rag.sqlite import (
    change_directory_path,
    change_file_path,
    delete_directory_and_subdirectories,
    get_id_by_path,
    initialize_database,
    insert_directory_structure,
    insert_file_info,
)
from mafm.rag.vectorDb import (
    delete_vector_db,
    find_by_id,
    initialize_vector_db,
    insert_file_embedding,
    remove_by_id,
    save,
)

DEFAULT_CHUNK_SIZE = 500


def read_pdf(file_path: str) -> str:
    """PDF 파일을 읽어서 텍스트로 변환합니다.

    Args:
        file_path: PDF 파일 경로.

    Returns:
        추출된 텍스트 내용.
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text


def read_word(file_path: str) -> str:
    """Word 파일을 읽어서 텍스트로 변환합니다.

    Args:
        file_path: Word 파일 경로.

    Returns:
        추출된 텍스트 내용.
    """
    text = ""
    doc = Document(file_path)
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[str]:
    """텍스트를 주어진 크기의 청크로 분할합니다.

    Args:
        text: 분할할 텍스트.
        chunk_size: 각 청크의 최대 크기.

    Returns:
        텍스트 청크 리스트.
    """
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


class FileEventHandler(FileSystemEventHandler):
    """파일 시스템 이벤트 핸들러 클래스.

    파일 생성, 삭제, 이동 이벤트를 처리합니다.
    """

    IGNORED_PATTERNS = ["db-journal", ".db"]

    def __init__(self) -> None:
        """FileEventHandler를 초기화합니다."""
        super().__init__()

    def _is_dot_file(self, path: str) -> bool:
        """숨김 파일인지 확인합니다.

        Args:
            path: 확인할 파일 경로.

        Returns:
            숨김 파일이면 True.
        """
        return os.path.basename(path).startswith(".")

    def _is_ignored_file(self, path: str) -> bool:
        """무시할 파일인지 확인합니다.

        Args:
            path: 확인할 파일 경로.

        Returns:
            무시할 파일이면 True.
        """
        return any(pattern in path for pattern in self.IGNORED_PATTERNS)

    def _should_ignore(self, path: str) -> bool:
        """파일을 무시해야 하는지 확인합니다.

        Args:
            path: 확인할 파일 경로.

        Returns:
            무시해야 하면 True.
        """
        return self._is_dot_file(path) or self._is_ignored_file(path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """파일 또는 디렉토리 삭제 이벤트를 처리합니다.

        Args:
            event: 파일 시스템 이벤트.
        """
        if self._should_ignore(event.src_path):
            print(f"ignore deleted: {event.src_path}")
            return

        print("--deleted--")
        print(f"deleting: {event.src_path}")

        if event.is_directory:
            dir_path = event.src_path
            dir_name = os.path.basename(dir_path)

            db_name = f"{dir_path}/{dir_name}.db"
            delete_vector_db(db_name)
            delete_directory_and_subdirectories(dir_path)
            print(f"Deleted directory and associated VectorDB: {db_name}")
            return

        file_path = event.src_path
        dir_path = os.path.dirname(file_path)

        db_name = f"{dir_path}/{os.path.basename(dir_path)}.db"
        file_id = get_id_by_path(file_path, "filesystem.db")
        remove_by_id(file_id, db_name)
        print(f"Deleted file: {event.src_path}")

    def on_moved(self, event: FileSystemEvent) -> None:
        """파일 또는 디렉토리 이동 이벤트를 처리합니다.

        Args:
            event: 파일 시스템 이벤트.
        """
        if self._should_ignore(event.src_path) or self._should_ignore(event.dest_path):
            return

        print("--moved--")

        if event.is_directory:
            change_directory_path(event.src_path, event.dest_path, "filesystem.db")
            print(f"Moved directory: from {event.src_path} to {event.dest_path}")
        else:
            print(f"Moved file: from {event.src_path} to {event.dest_path}")
            self._move_file(event.src_path, event.dest_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """파일 생성 이벤트를 처리합니다.

        Args:
            event: 파일 시스템 이벤트.
        """
        print("--created--", flush=True)

        if self._should_ignore(event.src_path):
            return

        absolute_file_path = event.src_path
        dirpath = os.path.dirname(absolute_file_path)
        dirname = os.path.basename(dirpath)

        if event.is_directory:
            print("created directory")
            try:
                initialize_vector_db(f"{dirpath}/{dirname}.db")
                file_id = insert_file_info(absolute_file_path, 1, "filesystem.db")
                insert_directory_structure(
                    file_id, dirpath, os.path.dirname(dirpath), "filesystem.db"
                )
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
        else:
            print("created file")
            insert_file_info(absolute_file_path, 0, "filesystem.db")

            text_chunks = self._extract_file_content(absolute_file_path)

            save(
                f"{dirpath}/{dirname}.db",
                get_id_by_path(absolute_file_path, "filesystem.db"),
                text_chunks,
            )
            print(f"Created file: {event.src_path}")

    def _extract_file_content(self, file_path: str) -> list[str]:
        """파일 내용을 추출합니다.

        Args:
            file_path: 파일 경로.

        Returns:
            텍스트 청크 리스트.
        """
        if file_path.endswith(".pdf"):
            text_content = read_pdf(file_path)
            return split_text_into_chunks(text_content)
        elif file_path.endswith(".docx"):
            text_content = read_word(file_path)
            return split_text_into_chunks(text_content)
        else:
            file_chunks = get_file_data(file_path)
            return file_chunks[2:]

    def _move_file(self, file_src_path: str, file_dest_path: str) -> None:
        """파일 이동 시 벡터 DB를 업데이트합니다.

        Args:
            file_src_path: 원본 파일 경로.
            file_dest_path: 대상 파일 경로.
        """
        dir_path = os.path.dirname(file_src_path)
        db_name = f"{dir_path}/{os.path.basename(dir_path)}.db"
        file_id = get_id_by_path(file_src_path, "filesystem.db")
        file_data = find_by_id(file_id, db_name)
        if file_data:
            insert_file_embedding(file_data, db_name)
        remove_by_id(file_id, db_name)
        change_file_path(file_src_path, file_dest_path, db_name)


def start_command_c(root: str) -> None:
    """SQLite DB에 파일 및 디렉토리 데이터를 삽입합니다.

    Args:
        root: 루트 디렉토리 경로.
    """
    start_time = time.time()

    try:
        initialize_database("filesystem.db")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return

    try:
        initialize_vector_db(f"{root}/{os.path.basename(root)}.db")
    except Exception as e:
        print(f"Error initializing vector DB for root: {e}")
        return

    file_id = insert_file_info(root, 1, "filesystem.db")

    last_slash_index = root.rfind("/")
    root_parent = root[:last_slash_index] if last_slash_index != -1 else ""

    insert_directory_structure(file_id, root, root_parent, "filesystem.db")

    for dirpath, dirnames, filenames in os.walk(root):
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)
            print(f"디렉토리 경로: {full_path}")
            try:
                initialize_vector_db(f"{full_path}/{dirname}.db")
            except Exception as e:
                print(f"Error initializing vector DB for directory: {e}")
                continue

            dir_id = insert_file_info(full_path, 1, "filesystem.db")
            insert_directory_structure(dir_id, full_path, dirpath, "filesystem.db")

        for filename in filenames:
            if filename.startswith(".") or filename.endswith(".db"):
                continue

            full_path = os.path.join(dirpath, filename)
            print(f"Embedding 하는 파일의 절대 경로: {full_path}")

            file_id = insert_file_info(full_path, 0, "filesystem.db")

            if filename.endswith(".pdf"):
                text_content = read_pdf(full_path)
                text_chunks = split_text_into_chunks(text_content)
            elif filename.endswith(".docx"):
                text_content = read_word(full_path)
                text_chunks = split_text_into_chunks(text_content)
            else:
                file_chunks = get_file_data(full_path)
                text_chunks = file_chunks[2:]

            dirname = dirpath.split("/")[-1]
            save(f"{dirpath}/{dirname}.db", file_id, text_chunks)

    elapsed_time = time.time() - start_time
    print(f"작업에 걸린 시간: {elapsed_time:.4f} 초")


def start_watchdog(root_dir: str) -> None:
    """파일 시스템 감시를 시작합니다.

    Args:
        root_dir: 감시할 루트 디렉토리 경로.
    """
    initialize_model()
    try:
        start_command_c(root_dir)
    except IndexError:
        print("start: missing argument")
    except FileNotFoundError:
        print(f"start: no such file or directory: {root_dir}")

    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=root_dir, recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAFM watchdog")
    parser.add_argument("-r", "--root", help="Root directory path")
    args = parser.parse_args()

    if not args.root:
        print("Root directory path is required.")
    else:
        start_watchdog(args.root)