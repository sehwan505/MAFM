"""멤버 에이전트 모듈.

디렉토리 내 파일 검색을 담당하는 에이전트를 정의합니다.
"""

import os
from typing import Any

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from mafm.agent.agents.llm_model import api_key
from mafm.rag.vectorDb import search


class QueryResponse(BaseModel):
    """사용자 입력에서 추출한 검색 쿼리 응답 모델.

    Attributes:
        query: 검색에 사용할 쿼리 문장.
    """

    query: str = Field(description="query sentence")


def _get_file_list(query: QueryResponse, directory_name: str) -> list[str]:
    """사용자 입력에서 파일 목록을 검색합니다.

    Args:
        query: 검색 쿼리 응답 객체.
        directory_name: 검색할 디렉토리 이름.

    Returns:
        검색된 파일 경로 목록.
    """
    print(f"current_directory_name: {directory_name}")
    print(f"query: {query}")
    db_path = f"{directory_name}/{os.path.basename(directory_name)}.db"
    return search(db_path, [query.query])


def agent_node(
    state: dict[str, Any],
    directory_name: str,
    output_list: list[str],
) -> dict[str, list[str]]:
    """파일 검색 에이전트 노드.

    주어진 디렉토리에서 사용자 요청에 맞는 파일을 검색합니다.

    Args:
        state: 현재 에이전트 상태 (메시지 포함).
        directory_name: 검색할 디렉토리 경로.
        output_list: 검색 결과를 추가할 출력 리스트.

    Returns:
        검색 결과 메시지를 포함한 딕셔너리.
    """
    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "current directory name: {directory_name} "
                "사용자에 요청에 따라서 디렉토리에서 파일을 검색하려고 합니다 쿼리를 문장으로 정리해주세요",
            ),
        ]
    ).partial(directory_name=directory_name)

    query_chain = prompt | llm.with_structured_output(QueryResponse)

    query_result = query_chain.invoke(state)
    file_list = _get_file_list(query_result, directory_name)

    if file_list:
        output_list.extend(file_list)
        return {"messages": file_list}
    return {"messages": []}