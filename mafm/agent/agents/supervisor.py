"""감독자 에이전트 모듈.

디렉토리 선택을 담당하는 감독자 에이전트를 정의합니다.
"""

from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from mafm.agent.agents.llm_model import api_key


def supervisor_agent(
    state: dict[str, Any],
    member_list: list[str],
) -> dict[str, str]:
    """감독자 에이전트.

    사용자 요청에 따라 다음에 실행할 디렉토리를 선택합니다.

    Args:
        state: 현재 에이전트 상태 (메시지 포함).
        member_list: 선택 가능한 디렉토리 목록.

    Returns:
        다음 노드 이름을 포함한 딕셔너리.
    """
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

    next_options = member_list + ["analyst"]

    class RouteResponse(BaseModel):
        """라우팅 응답 모델.

        Attributes:
            next: 다음으로 실행할 노드 이름.
        """

        next: Literal[*(next_options)]

    system_prompt = (
        "당신은 사용자의 요청에 따라 디렉토리를 선택하는 감독자입니다."
        "3번 디렉토리를 선택했으면 'analyst'를 선택해주세요."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "선택할 수 있는 디렉토리는 다음과 같습니다: {members}. "
                "디렉토리를 선택해주세요. "
                "절대로 같은 디렉토리를 두 번 선택하지 마세요.",
            ),
        ]
    ).partial(members=", ".join(member_list))

    supervisor_chain = prompt | llm.with_structured_output(RouteResponse)
    return supervisor_chain.invoke(state)
