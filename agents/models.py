import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.fallback import FallbackModel
from dotenv import load_dotenv

load_dotenv()

# Agrinet Model
LLM_AGRINET_MODEL = OpenAIChatModel(
    os.getenv('LLM_AGRINET_MODEL_NAME', 'agrinet-model'),
    provider=OpenAIProvider(
        base_url=os.getenv('VLLM_AGRINET_MODEL_URL'),
        api_key="not-needed",
    ),
)

# Moderation Model
LLM_MODERATION_BASE_MODEL = OpenAIChatModel(
    os.getenv('LLM_MODERATION_MODEL_NAME', 'moderation-model'),
    provider=OpenAIProvider(
        base_url=os.getenv('VLLM_MODERATION_MODEL_URL'),
        api_key="not-needed",
    ),
)

# TODO: for production, we uncomment this and comment the line below
# Moderation Fallback: tries moderation model first, falls back to agrinet model
# LLM_MODERATION_MODEL = FallbackModel(LLM_MODERATION_BASE_MODEL, LLM_AGRINET_MODEL)
LLM_MODERATION_MODEL = LLM_MODERATION_BASE_MODEL