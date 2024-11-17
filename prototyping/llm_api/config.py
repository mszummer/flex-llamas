import dotenv
import os

dotenv.load_dotenv()

class Config:
    # MODEL_NAME: str = "meta-llama/Llama-3.2-11B-Vision-Instruct"
    MODEL_NAME: str = "meta-llama/Llama-3.2-3B-Instruct"
    PORT: int = 8000
    DEFAULT_MAX_TOKENS: int = 10000
    DEFAULT_TEMPERATURE: float = 1
    HUGGINGFACE_ACCESS_TOKEN: str = os.getenv("HUGGINGFACE_ACCESS_TOKEN", "")
