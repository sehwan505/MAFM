"""SQLite 데이터베이스 모듈.

파일 시스템 메타데이터를 SQLite에 저장하고 관리합니다.
"""

import os
import sqlite3


def initialize_database(db_name: str = "filesystem.db") -> None:
    """데이터베이스를 초기화합니다.

    기존 데이터베이스가 존재하면 삭제하고 새로 생성합니다.

    Args:
        db_name: 데이터베이스 파일 이름.
    """
    if os.path.exists(db_name):
        os.remove(db_name)

    connection = sqlite3.connect("filesystem.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS file_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            is_dir INTEGER NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS directory_structure (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT NOT NULL,
            dir_path TEXT NOT NULL,
            parent_dir_path TEXT
        )
    """
    )

    connection.commit()
    connection.close()


def insert_file_info(
    file_path: str,
    is_dir: int,
    db_name: str = "filesystem.db",
) -> int:
    """파일 정보를 데이터베이스에 삽입합니다.

    Args:
        file_path: 파일 또는 디렉토리의 절대 경로.
        is_dir: 디렉토리 여부 (1: 디렉토리, 0: 파일).
        db_name: 데이터베이스 파일 이름.

    Returns:
        삽입된 레코드의 ID.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO file_info (file_path, is_dir)
        VALUES (?, ?)
        """,
        (file_path, is_dir),
    )
    cursor.execute("SELECT last_insert_rowid()")
    rows = cursor.fetchall()
    connection.commit()
    connection.close()
    return rows[0][0]


def insert_directory_structure(
    dir_id: int,
    dir_path: str,
    parent_dir_path: str,
    db_name: str = "filesystem.db",
) -> None:
    """디렉토리 구조 정보를 삽입합니다.

    Args:
        dir_id: 디렉토리 ID.
        dir_path: 디렉토리 경로.
        parent_dir_path: 부모 디렉토리 경로.
        db_name: 데이터베이스 파일 이름.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO directory_structure (id, dir_path, parent_dir_path)
        VALUES (?, ?, ?)
    """,
        (dir_id, dir_path, parent_dir_path),
    )
    connection.commit()
    connection.close()


def get_file_info(db_name: str = "filesystem.db") -> list[tuple]:
    """모든 파일 정보를 조회합니다.

    Args:
        db_name: 데이터베이스 파일 이름.

    Returns:
        파일 정보 튜플 리스트.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM file_info")
    rows = cursor.fetchall()
    connection.close()
    return rows


def get_path_by_id(file_id: int, db_name: str = "filesystem.db") -> str:
    """ID로 파일 경로를 조회합니다.

    Args:
        file_id: 파일 ID.
        db_name: 데이터베이스 파일 이름.

    Returns:
        파일 경로.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT file_path FROM file_info WHERE id = ?", (file_id,))
    rows = cursor.fetchall()
    connection.close()
    return rows[0][0]


def get_id_by_path(path: str, db_name: str = "filesystem.db") -> int:
    """경로로 파일 ID를 조회합니다.

    Args:
        path: 파일 경로.
        db_name: 데이터베이스 파일 이름.

    Returns:
        파일 ID.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM file_info WHERE file_path = ?", (path,))
    rows = cursor.fetchall()
    connection.close()
    print(f"rows ======== {rows}")
    return rows[0][0]


def get_directory_structure(db_name: str = "filesystem.db") -> list[str]:
    """모든 디렉토리 경로를 조회합니다.

    Args:
        db_name: 데이터베이스 파일 이름.

    Returns:
        디렉토리 경로 리스트.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT dir_path FROM directory_structure")
    rows = cursor.fetchall()
    connection.close()
    return [row[0] for row in rows]


def update_file_info(
    file_id: int,
    new_file_path: str,
    db_name: str = "filesystem.db",
) -> None:
    """파일 경로를 업데이트합니다.

    Args:
        file_id: 업데이트할 파일 ID.
        new_file_path: 새 파일 경로.
        db_name: 데이터베이스 파일 이름.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE file_info
        SET file_path = ?
        WHERE id = ?
    """,
        (new_file_path, file_id),
    )
    connection.commit()
    connection.close()


def update_directory_structure(
    record_id: int,
    new_dir_path: str,
    db_name: str = "filesystem.db",
) -> None:
    """디렉토리 경로를 업데이트합니다.

    Args:
        record_id: 업데이트할 레코드 ID.
        new_dir_path: 새 디렉토리 경로.
        db_name: 데이터베이스 파일 이름.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE file_info
        SET dir_path = ?
        WHERE record_id = ?
    """,
        (new_dir_path, record_id),
    )
    connection.commit()
    connection.close()


def delete_file_info(record_id: int, db_name: str = "filesystem.db") -> None:
    """파일 정보를 삭제합니다.

    Args:
        record_id: 삭제할 레코드 ID.
        db_name: 데이터베이스 파일 이름.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        DELETE FROM file_info
        WHERE record_id = ?
    """,
        (record_id,),
    )
    connection.commit()
    connection.close()


def change_directory_path(
    dir_src_path: str,
    dir_dest_path: str,
    db_name: str = "filesystem.db",
) -> None:
    """디렉토리 경로를 변경합니다.

    Args:
        dir_src_path: 원본 디렉토리 경로.
        dir_dest_path: 대상 디렉토리 경로.
        db_name: 데이터베이스 파일 이름.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE directory_structure
        SET dir_path = ?
        WHERE dir_path = ?
    """,
        (dir_dest_path, dir_src_path),
    )
    cursor.execute(
        """
        SELECT file_path FROM file_info WHERE file_path LIKE ?
        """,
        (f"{dir_src_path}%",),
    )
    rows = cursor.fetchall()

    for (file_path,) in rows:
        new_file_path = file_path.replace(dir_src_path, dir_dest_path, 1)
        cursor.execute(
            """
            UPDATE file_info
            SET file_path = ?
            WHERE file_path = ?
            """,
            (new_file_path, file_path),
        )
    connection.commit()
    connection.close()


def change_file_path(
    file_src_path: str,
    file_dest_path: str,
    db_name: str,
) -> None:
    """파일 경로를 변경합니다.

    Args:
        file_src_path: 원본 파일 경로.
        file_dest_path: 대상 파일 경로.
        db_name: 데이터베이스 파일 이름.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE file_info
        SET file_path = ?
        WHERE file_path = ?
        """,
        (file_dest_path, file_src_path),
    )
    connection.commit()
    connection.close()


def delete_directory_and_subdirectories(dir_path: str) -> None:
    """디렉토리와 하위 디렉토리 정보를 삭제합니다.

    Args:
        dir_path: 삭제할 디렉토리 경로.
    """
    connection = sqlite3.connect("filesystem.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM directory_structure
        WHERE dir_path LIKE ?
        """,
        (f"{dir_path}%",),
    )

    cursor.execute(
        """
        DELETE FROM file_info
        WHERE file_path LIKE ?
        """,
        (f"{dir_path}%",),
    )

    connection.commit()
    connection.close()
    print(f"Deleted all records related to {dir_path} and its subdirectories.")
