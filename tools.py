from langchain_core.tools import Tool


def search_resources(query: str) -> str:
    return f"Recommended resources for: {query}"


resource_tool = Tool(
    name="Learning Resource Finder",
    func=search_resources,
    description="Finds AI learning resources",
)

