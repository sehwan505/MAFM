"""임베딩 모듈.

SentenceTransformer를 사용한 텍스트 임베딩 기능을 제공합니다.
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

os.environ["TOKENIZERS_PARALLELISM"] = "false"

_model: "SentenceTransformer | None" = None


def initialize_model() -> None:
    """임베딩 모델을 초기화합니다.

    전역 모델 인스턴스를 생성하고 재사용합니다.

    Raises:
        Exception: 모델 초기화 중 오류가 발생한 경우.
    """
    global _model

    if _model is not None:
        return

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(
            # "dunzhang/stella_en_400M_v5",
            "avsolatorio/GIST-small-Embedding-v0",  # 33
            # "hkunlp/instructor-base",  # 110
            trust_remote_code=True,
            device="cpu",
            config_kwargs={
                "use_memory_efficient_attention": False,
                "unpad_inputs": False,
            },
        )
        print("모델이 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"모델 초기화 중 오류 발생: {e}")
        raise


def embedding(queries: list[str]) -> list[list[float]] | None:
    """텍스트 쿼리를 임베딩 벡터로 변환합니다.

    Args:
        queries: 임베딩할 텍스트 문자열 리스트.

    Returns:
        임베딩 벡터 리스트. 오류 발생 시 None.

    Raises:
        ValueError: 입력이 문자열 리스트가 아닌 경우.
    """
    global _model

    if _model is None:
        initialize_model()

    if _model is None:
        print("모델이 초기화되지 않았습니다.")
        return None

    try:
        if not isinstance(queries, list) or not all(
            isinstance(q, str) for q in queries
        ):
            raise ValueError("The input to encode() must be a list of strings.")

        query_embeddings = _model.encode(queries)
        return query_embeddings.tolist()

    except MemoryError as me:
        print(f"MemoryError: {me}")
        return None
    except ValueError:
        raise
    except Exception as e:
        print(f"embedding 중 오류 발생: {e}")
        return None
