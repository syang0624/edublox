import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    BUTTERBASE_API_KEY = os.getenv("BUTTERBASE_API_KEY", "")
    BUTTERBASE_AI_BASE_URL = os.getenv(
        "BUTTERBASE_AI_BASE_URL",
        "https://api.butterbase.ai/v1/app_abc123",
    )
    LLM_MODEL_LARGE = os.getenv("LLM_MODEL_LARGE", "anthropic/claude-sonnet-4.6")
    LLM_MODEL_SMALL = os.getenv("LLM_MODEL_SMALL", "anthropic/claude-sonnet-4.6")
    EVEROS_API_KEY = os.getenv("EVEROS_API_KEY", "")
    EVEROS_BASE_URL = os.getenv("EVEROS_BASE_URL", "https://api.evermind.ai/api/v1")
    ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

settings = Settings()
