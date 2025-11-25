"""Milvus 벡터 데이터베이스 테스트."""

from typing import Any

import pytest
from pymilvus import Collection, connections, utility

from mafm.rag.embedding import embedding
from mafm.rag.vector_db import (
    delete_vector_db,
    find_by_id,
    initialize_vector_db,
    insert_file_embedding,
    remove_by_id,
    save,
    search,
)

DB_NAME = "test_db"
TEST_ID = 123
TEST_QUERIES = ["test query one", "test query two"]


def _get_test_file_data() -> list[list[Any]]:
    """테스트용 파일 데이터를 생성합니다.

    Returns:
        테스트 파일 데이터.
    """
    embedding_result = embedding(["file data sample"])
    if embedding_result is None:
        return []
    return [[TEST_ID, embedding_result[0], "file data sample"]]


@pytest.fixture(scope="module")
def setup_milvus() -> Any:
    """Milvus 테스트 환경을 설정합니다.

    Yields:
        None.
    """
    initialize_vector_db(DB_NAME)
    yield
    delete_vector_db(DB_NAME)


def test_initialize_vector_db() -> None:
    """벡터 데이터베이스 초기화를 테스트합니다."""
    initialize_vector_db(DB_NAME)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    assert utility.has_collection(collection_name)
    connections.disconnect(alias="default")


def test_save(setup_milvus: Any) -> None:
    """데이터 저장을 테스트합니다.

    Args:
        setup_milvus: Milvus 설정 픽스처.
    """
    save(DB_NAME, TEST_ID, TEST_QUERIES)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    collection = Collection(name=collection_name)
    collection.load()
    res = collection.query(expr=f"id in [{TEST_ID}]", output_fields=["id", "word"])
    assert len(res) > 0
    collection.release()
    connections.disconnect(alias="default")


def test_insert_file_embedding(setup_milvus: Any) -> None:
    """파일 임베딩 삽입을 테스트합니다.

    Args:
        setup_milvus: Milvus 설정 픽스처.
    """
    test_file_data = _get_test_file_data()
    insert_file_embedding(test_file_data, DB_NAME)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    collection = Collection(name=collection_name)
    collection.load()
    res = collection.query(expr=f"id in [{TEST_ID}]", output_fields=["id", "word"])
    assert len(res) > 0
    collection.release()
    connections.disconnect(alias="default")


def test_search(setup_milvus: Any, mocker: Any) -> None:
    """검색 기능을 테스트합니다.

    Args:
        setup_milvus: Milvus 설정 픽스처.
        mocker: pytest-mock mocker.
    """
    mocker.patch(
        "mafm.rag.vector_db.get_path_by_id",
        return_value="path/to/file",
    )

    save(DB_NAME, TEST_ID, TEST_QUERIES)

    results = search(DB_NAME, ["test query one"])
    assert results is not None
    assert len(results) == 2
    assert all(result == "path/to/file" for result in results)


def test_find_by_id(setup_milvus: Any) -> None:
    """ID로 검색 기능을 테스트합니다.

    Args:
        setup_milvus: Milvus 설정 픽스처.
    """
    save(DB_NAME, TEST_ID, TEST_QUERIES)

    res = find_by_id(TEST_ID, DB_NAME)
    assert res is not None
    assert len(res) > 0
    assert res[0]["id"] == TEST_ID


def test_remove_by_id(setup_milvus: Any) -> None:
    """ID로 삭제 기능을 테스트합니다.

    Args:
        setup_milvus: Milvus 설정 픽스처.
    """
    save(DB_NAME, TEST_ID, TEST_QUERIES)

    remove_by_id(TEST_ID, DB_NAME)

    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    collection = Collection(name=collection_name)
    collection.load()
    res = collection.query(expr=f"id in [{TEST_ID}]", output_fields=["id", "word"])
    assert len(res) == 0
    collection.release()
    connections.disconnect(alias="default")


def test_delete_vector_db() -> None:
    """벡터 데이터베이스 삭제를 테스트합니다."""
    initialize_vector_db(DB_NAME)
    delete_vector_db(DB_NAME)
    connections.connect(alias="default", host="localhost", port="19530")
    collection_name = f"{DB_NAME}_demo_collection"
    assert not utility.has_collection(collection_name)
    connections.disconnect(alias="default")
