"""분석가 에이전트 모듈.

파일 경로 결과를 정리하는 분석가 에이전트를 정의합니다.
"""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from mafm.agent.agents.llm_model import api_key


class ListResponse(BaseModel):
    """분석 결과 응답 모델.

    Attributes:
        messages: 필터링된 파일 경로 목록.
    """

    messages: list[str]


def analyst_agent(
    state: dict[str, Any],
    input_prompt: str,
    output_list: list[str],
) -> dict[str, list[str]]:
    """분석가 에이전트.

    구성원들이 검색한 파일 경로들을 정리하고 필터링합니다.

    Args:
        state: 현재 에이전트 상태 (메시지 포함).
        input_prompt: 사용자의 원본 요청.
        output_list: 구성원들이 검색한 파일 경로 목록.

    Returns:
        필터링된 파일 경로 목록을 포함한 딕셔너리.
    """
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    system_prompt = "당신은 구성원들이 답변한 파일의 경로들을 받고 정리하는 감독자입니다."

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "주어진 파일 경로들 안에서 사용자 요청에 맞는 파일 경로만 뽑아주세요. "
                "주어지지 않은 파일 경로는 뽑으면 안됩니다."
                "사용자 요청: {input_prompt}"
                "파일 경로: {output_list}",
            ),
        ]
    ).partial(input_prompt=input_prompt, output_list=", ".join(output_list))

    print(output_list)
    analyst_chain = prompt | llm.with_structured_output(ListResponse)
    return analyst_chain.invoke(state)