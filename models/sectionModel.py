from typing import List

from config import OPENAI_API_KEY
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    AIMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.pydantic_v1 import BaseModel, Field


# Output data structure
class PageSection(BaseModel):
    section: str = Field(description="The section details in markdown format")


# output parser
parser = PydanticOutputParser(pydantic_object=PageSection)

# Prompt Templates
SECTION_SYSTEM_TEMPLATE = "You are a analyst assistant. You take summaries from web pages and create a detailed section for the company summary."
SECTION_HUMAN_TEMPLATE = """\
You are a analyst that writes reports on companies
You are creating a detailed section for the {section_name} section of the company summary.

For example, if you are creating a section for the Company History section of the company summary, you will write a detailed section about the company history.
This section will include details such as when the company was founded, who founded the company, and any other details that are important to the company history.

You will write this section in markdown format.
You will use any knowledge you currently have about the company, industry, and any other relevant information to write this section.
Below this are the page summaries that you will use as external sources to write this section.
{page_summaries}\n\n
{format_instructions}\n
"""

# Prompts
system_prompt_template = SystemMessagePromptTemplate.from_template(
    SECTION_SYSTEM_TEMPLATE
)
human_prompt_template_original = PromptTemplate(
    template=SECTION_HUMAN_TEMPLATE,
    input_variables=["section_name", "page_summaries"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)
human_prompt_template = HumanMessagePromptTemplate(
    prompt=human_prompt_template_original
)
chat_prompt = ChatPromptTemplate.from_messages(
    [system_prompt_template, human_prompt_template]
)


# LlMs
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo-16k", temperature=0.3
)

# Chains
section_chain = LLMChain(llm=llm, prompt=chat_prompt, output_parser=parser)
