from langchain_classic.chains import LLMChain

from llm import llm
from roadmap_prompt import career_prompt

from output_parser import format_instructions


# Wire format instructions into the prompt so the model can output in the
# structured form expected by parsers/output_parser.py.
career_prompt_with_format = career_prompt.partial(
    format_instructions=format_instructions
)

career_chain = LLMChain(
    llm=llm,
    prompt=career_prompt_with_format,
    verbose=True,
)



