from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MODEL = os.getenv("MODEL")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file.")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in .env file.")