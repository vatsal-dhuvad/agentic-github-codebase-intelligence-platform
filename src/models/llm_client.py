import os

import streamlit as st
from dotenv import load_dotenv

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from langchain_mistralai import ChatMistralAI
except ImportError:
    ChatMistralAI = None

from src.config import GEMINI_MODEL, GROQ_MODEL, MISTRAL_MODEL


def get_secret(name: str) -> str:
    load_dotenv()
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def get_llm(temperature: float = 0.2):
    llms = []
    gemini_key = get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY")
    groq_key = get_secret("GROQ_API_KEY")
    mistral_key = get_secret("MISTRAL_API_KEY")

    if gemini_key and ChatGoogleGenerativeAI is not None:
        llms.append(
            ChatGoogleGenerativeAI(
                google_api_key=gemini_key,
                model=GEMINI_MODEL,
                temperature=temperature,
            )
        )
    if groq_key and ChatGroq is not None:
        llms.append(ChatGroq(groq_api_key=groq_key, model_name=GROQ_MODEL, temperature=temperature))
    if mistral_key and ChatMistralAI is not None:
        llms.append(ChatMistralAI(api_key=mistral_key, model=MISTRAL_MODEL, temperature=temperature))

    if not llms:
        return None
    if len(llms) == 1:
        return llms[0]
    return llms[0].with_fallbacks(llms[1:])


def available_llm_names() -> list[str]:
    names = []
    if get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY"):
        names.append("Gemini")
    if get_secret("GROQ_API_KEY"):
        names.append("Groq")
    if get_secret("MISTRAL_API_KEY"):
        names.append("Mistral")
    return names

