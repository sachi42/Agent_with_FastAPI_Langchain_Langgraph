from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import os
from dotenv import load_dotenv

def summarize_text(text_to_summarize: str) -> str:
    if "ERROR_OR_EMPTY" in text_to_summarize:
        return "Cannot summarize. Context is completely empty."
    try:
        llm = ChatOpenAI(model=settings.AGENT_LLM_MODEL, api_key=os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY, temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the following text accurately based ONLY on provided text. Do not hallucinate."),
            ("user", "{text}")
        ])
        chain = prompt | llm
        res = chain.invoke({"text": text_to_summarize})
        return str(res.content)
    except Exception as e:
        # Graceful failure boundary tracking
        return f"TOOL_FAILURE: Summarization failed due to operational issue: {str(e)}"
