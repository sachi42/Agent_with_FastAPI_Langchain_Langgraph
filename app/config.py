# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     AGENT_APP_NAME: str = "Research Agent Service"
#     AGENT_CHROMA_DIR: str = "./chroma_db"
#     AGENT_EMBED_MODEL: str = "all-MiniLM-L6-v2"
#     AGENT_LLM_MODEL: str = "gpt-4o"  # Or ollama / anthropic equivalent
#     AGENT_MAX_ITERATIONS: int = 5
#     AGENT_TOOL_BUDGET: int = 3

#     class Config:
#         env_file = ".env"
#         env_prefix = "AGENT_"

# settings = Settings()

from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Pydantic matches case-insensitively by default with .env keys.
    # We declare these exactly to match your project variables.
    AGENT_APP_NAME: str = "Research Agent Service"
    AGENT_CHROMA_DIR: str = "./chroma_db"
    AGENT_EMBED_MODEL: str = "all-MiniLM-L6-v2"
    AGENT_LLM_MODEL: str = "gpt-4o"
    AGENT_MAX_ITERATIONS: int = 5
    AGENT_TOOL_BUDGET: int = 3
    
    # Explicitly add the OpenAI key so Pydantic knows it is expected
    OPENAI_API_KEY: str = "sk-proj-test-key"

    # Modern Pydantic V2 Configuration Style
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore" # Safely ignores any other system variables in your shell
    )

settings = Settings()
