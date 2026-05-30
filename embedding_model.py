import os

from langchain_openai import OpenAIEmbeddings

embedding_model = OpenAIEmbeddings(
    model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)
