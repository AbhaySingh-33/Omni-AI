from langchain_mistralai import ChatMistralAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatMistralAI(
    model="mistral-large-latest",
    api_key=os.getenv("MISTRAL_API_KEY"),
    temperature=0.3
)
