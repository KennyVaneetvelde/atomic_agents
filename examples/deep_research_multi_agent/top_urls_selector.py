from typing import List
import instructor
import openai
from pydantic import BaseModel, Field, HttpUrl
from atomic_agents.agents.base_chat_agent import BaseAgentIO, BaseChatAgent, BaseChatAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo

class TopUrlsSelectorInputSchema(BaseAgentIO):
    user_input: str = Field(..., description='The user input or question.')
    num_urls: int = Field(..., description='The number of top URLs to select.')

class TopUrlsSelectorOutputSchema(BaseAgentIO):
    top_urls: List[HttpUrl] = Field(..., description='The list of top URLs selected based on the user input.')

# Create the top URLs selector agent
top_urls_selector_agent = BaseChatAgent(
    BaseChatAgentConfig(
        client=instructor.from_openai(openai.OpenAI()), 
        model='gpt-3.5-turbo',
        system_prompt_generator=SystemPromptGenerator(
            SystemPromptInfo(
                background=[
                    "You are an intelligent URL selection expert.",
                    "Your task is to select the best URLs from a list of search results that are most relevant to the user input or question."
                ],
                steps=[
                    "You will receive the user input or question, the list of search results, and the number of best URLs to select.",
                    "Analyze the search results and select the best URLs that are most relevant to the user input or question.",
                ],
                output_instructions=[
                    "Ensure each selected URL is highly relevant to the user input or question.",
                    "Ensure the selected URLs are diverse yet as relevant as possible."
                ]
            )
        ),
        input_schema=TopUrlsSelectorInputSchema,
        output_schema=TopUrlsSelectorOutputSchema
    )
)