import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("LLM_MODEL_NAME"),
    temperature=0.5
)