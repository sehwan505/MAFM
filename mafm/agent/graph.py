"""에이전트 그래프 모듈.

LangGraph 기반 멀티 에이전트 워크플로우를 정의합니다.
"""

import functools
import operator
from typing import Annotated, Any, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from mafm.agent.agents import agent_node, analyst_agent, supervisor_agent
from mafm.rag.sqlite import get_directory_structure


class AgentState(TypedDict):
    """에이전트 상태 타입.

    Attributes:
        messages: 대화 메시지 시퀀스.
        next: 다음에 실행할 노드 이름.
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


def graph(directory_path: str, prompt: str) -> list[str]:
    """멀티 에이전트 그래프를 실행합니다.

    Args:
        directory_path: 검색할 루트 디렉토리 경로.
        prompt: 사용자 검색 요청.

    Returns:
        검색된 파일 경로 목록.
    """
    human_input = HumanMessage(content=prompt)

    members = get_directory_structure()
    output_list: list[str] = []

    print(members)
    print(human_input)

    # 워크플로우 그래프 생성
    workflow = StateGraph(AgentState)

    # 감독자 노드 추가
    supervisor_node = functools.partial(supervisor_agent, member_list=members)
    workflow.add_node("supervisor", supervisor_node)

    # 분석가 노드 추가
    analyst_node_partial = functools.partial(
        analyst_agent, input_prompt=human_input.content, output_list=output_list
    )
    workflow.add_node("analyst", analyst_node_partial)

    # 멤버 노드 추가
    for member in members:
        member_node = functools.partial(
            agent_node, directory_name=member, output_list=output_list
        )
        workflow.add_node(member, member_node)
        workflow.add_edge(member, "supervisor")

    # 조건부 엣지 설정
    conditional_map: dict[str, str] = {k: k for k in members}
    conditional_map["analyst"] = "analyst"

    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        conditional_map,
    )
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("analyst", END)

    app = workflow.compile()

    # 그래프 실행
    previous_output: dict[str, Any] | None = None
    for s in app.stream(
        {"messages": [human_input]},
        {"recursion_limit": 20},
    ):
        previous_output = s
        if "__end__" not in s:
            print(s)
            print("----")

    if previous_output is None:
        return []

    return previous_output["analyst"]["messages"]


if __name__ == "__main__":
    print(graph("", ""))