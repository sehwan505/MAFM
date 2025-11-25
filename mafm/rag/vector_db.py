"""벡터 데이터베이스 모듈.

Milvus 벡터 데이터베이스 관리 기능을 제공합니다.
"""

import gc
import os
from typing import Any

from pymilvus import MilvusClient

from mafm.rag.embedding import embedding
from mafm.rag.sqlite import get_path_by_id

COLLECTION_NAME = "demo_collection"
VECTOR_DIMENSION = 384


def _delete_db_lock_file(db_name: str) -> None:
    """데이터베이스 잠금 파일을 삭제합니다.

    Args:
        db_name: 데이터베이스 파일 경로.
    """
    dir_path = os.path.dirname(db_name)
    base_name = os.path.basename(db_name)

    lock_file = f"{dir_path}/.{base_name}.lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)
    else:
        print(f"No lock file found for {lock_file}")


def initialize_vector_db(db_name: str) -> None:
    """벡터 데이터베이스를 초기화합니다.

    Args:
        db_name: 생성할 데이터베이스 파일 경로.

    Raises:
        Exception: 데이터베이스 초기화 중 오류가 발생한 경우.
    """
    client: MilvusClient | None = None
    try:
        client = MilvusClient(db_name)
        print(f"Connected to {db_name}")

        if client.has_collection(collection_name=COLLECTION_NAME):
            client.drop_collection(collection_name=COLLECTION_NAME)

        client.create_collection(
            collection_name=COLLECTION_NAME,
            dimension=VECTOR_DIMENSION,
        )
    except Exception as e:
        print(f"Error initializing vector DB for {db_name}: {e}")
        raise
    finally:
        if client is not None:
            client.close()
        gc.collect()
        _delete_db_lock_file(db_name)


def delete_vector_db(db_name: str) -> None:
    """벡터 데이터베이스를 삭제합니다.

    Args:
        db_name: 삭제할 데이터베이스 파일 경로.
    """
    client: MilvusClient | None = None
    try:
        client = MilvusClient(db_name)
        if client.has_collection(collection_name=COLLECTION_NAME):
            client.drop_collection(collection_name=COLLECTION_NAME)
            print(f"Collection '{COLLECTION_NAME}' in {db_name} has been deleted.")
        else:
            print(f"Collection '{COLLECTION_NAME}' does not exist in {db_name}")
    except Exception as e:
        print(f"Error deleting collection in {db_name}: {e}")
    finally:
        if client is not None:
            client.close()
        gc.collect()
        _delete_db_lock_file(db_name)


def save(db_name: str, file_id: int, queries: list[str]) -> None:
    """쿼리 데이터를 벡터 데이터베이스에 저장합니다.

    Args:
        db_name: 데이터베이스 파일 경로.
        file_id: 파일 고유 식별자.
        queries: 저장할 텍스트 쿼리 리스트.
    """
    client: MilvusClient | None = None
    try:
        client = MilvusClient(db_name)
        if not client.has_collection(collection_name=COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in {db_name}")
            return

        query_embeddings = embedding(queries)
        if query_embeddings is None:
            print("Failed to generate embeddings")
            return

        data = [
            {"id": file_id, "vector": query_embeddings[i], "word": queries[i]}
            for i in range(len(query_embeddings))
        ]

        res = client.insert(collection_name=COLLECTION_NAME, data=data)
        print(res)

    except MemoryError as me:
        print(f"MemoryError: {me}")
    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"Error occurred during saving data to Milvus: {e}")
    finally:
        if client is not None:
            client.close()
        gc.collect()
        _delete_db_lock_file(db_name)


def insert_file_embedding(file_data: list[dict[str, Any]], db_name: str) -> None:
    """파일 임베딩 데이터를 삽입합니다.

    Args:
        file_data: 삽입할 임베딩 데이터 리스트.
        db_name: 데이터베이스 파일 경로.
    """
    client: MilvusClient | None = None
    try:
        client = MilvusClient(db_name)
        if not client.has_collection(collection_name=COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in {db_name}")
            return

        client.insert(collection_name=COLLECTION_NAME, data=file_data)

    except MemoryError as me:
        print(f"MemoryError: {me}")
    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"Error occurred during saving data to Milvus: {e}")
    finally:
        if client is not None:
            client.close()
        gc.collect()
        _delete_db_lock_file(db_name)


def search(db_name: str, query_list: list[str]) -> list[str]:
    """벡터 데이터베이스에서 유사한 항목을 검색합니다.

    Args:
        db_name: 데이터베이스 파일 경로.
        query_list: 검색할 쿼리 텍스트 리스트.

    Returns:
        검색된 파일 경로 리스트.
    """
    client: MilvusClient | None = None
    try:
        client = MilvusClient(db_name)
        if not client.has_collection(collection_name=COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in {db_name}")
            return []

        query_vectors = embedding(query_list)
        if query_vectors is None:
            return []

        res = client.search(
            collection_name=COLLECTION_NAME,
            data=query_vectors,
            limit=2,
        )
        id_list = [item["id"] for item in res[0]]
        path_list = [get_path_by_id(file_id, "filesystem.db") for file_id in id_list]
        return path_list
    finally:
        if client is not None:
            client.close()
        gc.collect()
        _delete_db_lock_file(db_name)


def find_by_id(search_id: int, db_name: str) -> list[dict[str, Any]] | None:
    """ID로 벡터 데이터를 검색합니다.

    Args:
        search_id: 검색할 파일 ID.
        db_name: 데이터베이스 파일 경로.

    Returns:
        검색된 데이터 리스트. 없으면 None.
    """
    client: MilvusClient | None = None
    try:
        client = MilvusClient(db_name)

        if not client.has_collection(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist in {db_name}")
            return None

        res = client.query(
            collection_name=COLLECTION_NAME, filter=f"id in [{search_id}]"
        )

        if not res:
            print(f"No results found for ID: {search_id}")
            return None
        return res
    finally:
        if client is not None:
            client.close()
        gc.collect()
        _delete_db_lock_file(db_name)


def remove_by_id(remove_id: int, db_name: str) -> dict[str, Any] | None:
    """ID로 벡터 데이터를 삭제합니다.

    Args:
        remove_id: 삭제할 파일 ID.
        db_name: 데이터베이스 파일 경로.

    Returns:
        삭제 결과. 오류 시 None.

    Raises:
        Exception: 컬렉션이 존재하지 않는 경우.
    """
    client: MilvusClient | None = None
    try:
        client = MilvusClient(db_name)
        if not client.has_collection(COLLECTION_NAME):
            raise Exception(
                f"Collection '{COLLECTION_NAME}' does not exist in {db_name}"
            )

        res = client.delete(
            collection_name=COLLECTION_NAME, filter=f"id in [{remove_id}]"
        )

        print(f"Deleted records with ID: {remove_id}")
        return res
    finally:
        if client is not None:
            client.close()
        gc.collect()
        _delete_db_lock_file(db_name)
