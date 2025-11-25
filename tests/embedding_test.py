"""임베딩 모듈 테스트."""

import pytest

from mafm.rag.embedding import embedding


@pytest.fixture
def test_sentences() -> list[str]:
    """테스트용 문장 리스트를 반환합니다.

    Returns:
        테스트 문장 리스트.
    """
    return [
        "This is the first test sentence.",
        "Here is another example sentence.",
        "Sentence embeddings are useful.",
    ]


def test_embedding_output_shape(test_sentences: list[str]) -> None:
    """임베딩 출력 형태가 올바른지 테스트합니다.

    Args:
        test_sentences: 테스트 문장 리스트.
    """
    embeddings = embedding(test_sentences)
    assert embeddings is not None
    assert len(embeddings) == len(test_sentences)
