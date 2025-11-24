"""LLM 모델 설정 모듈.

OpenAI API 키 로드 및 LLM 설정을 담당합니다.
"""

import os

from dotenv import load_dotenv

load_dotenv()

api_key: str | None = os.getenv("OPENAI_API_KEY")