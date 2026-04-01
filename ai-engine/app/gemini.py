from langchain_mistralai import ChatMistralAI
import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

llm = ChatMistralAI(
    model=MISTRAL_MODEL,
    api_key=os.getenv("MISTRAL_API_KEY"),
    temperature=0.3
)
