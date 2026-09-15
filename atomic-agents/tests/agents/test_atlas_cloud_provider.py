"""Unit tests for Atlas Cloud's OpenAI-compatible client setup."""

from unittest.mock import Mock

import instructor
from openai import OpenAI

from atomic_agents import AgentConfig, AtomicAgent, BasicChatInputSchema, BasicChatOutputSchema


def _create_atlas_cloud_client(api_key: str = "test-key") -> instructor.Instructor:
    return instructor.from_openai(OpenAI(base_url="https://api.atlascloud.ai/v1", api_key=api_key))


def test_atlas_cloud_client_uses_openai_compatible_endpoint():
    raw_client = OpenAI(base_url="https://api.atlascloud.ai/v1", api_key="test-key")

    assert str(raw_client.base_url) == "https://api.atlascloud.ai/v1/"
    assert isinstance(_create_atlas_cloud_client(), instructor.Instructor)


def test_atlas_cloud_client_runs_through_atomic_agent():
    client = Mock(spec=instructor.Instructor)
    client.chat.completions.create.return_value = BasicChatOutputSchema(chat_message="Atlas Cloud response")
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](AgentConfig(client=client, model="openai/gpt-5.6-luna"))

    response = agent.run(BasicChatInputSchema(chat_message="Hello"))

    assert response.chat_message == "Atlas Cloud response"
    assert client.chat.completions.create.call_args.kwargs["model"] == "openai/gpt-5.6-luna"
