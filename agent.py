from langchain_classic.agents import initialize_agent
from langchain_classic.agents import AgentType

from models.llm import llm
from tools.tools import resource_tool

agent = initialize_agent(
    tools=[resource_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)