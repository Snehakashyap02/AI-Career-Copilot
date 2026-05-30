from langchain_classic.output_parsers import StructuredOutputParser
from langchain_classic.output_parsers import ResponseSchema

response_schemas = [
    ResponseSchema(
        name="roadmap",
        description="Learning roadmap"
    ),
    ResponseSchema(
        name="projects",
        description="Recommended projects"
    ),
    ResponseSchema(
        name="timeline",
        description="Learning timeline"
    ),
    ResponseSchema(
        name="interview_questions",
        description="Interview questions"
    ),
    ResponseSchema(
        name="resources",
        description="Recommended resources"
    ),
    ResponseSchema(
        name="missing_skills",
        description="Missing skills as bullet list items"
    )
]


parser = StructuredOutputParser.from_response_schemas(
    response_schemas
)

format_instructions = parser.get_format_instructions()

