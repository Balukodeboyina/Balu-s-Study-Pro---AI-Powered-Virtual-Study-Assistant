# config/settings.py
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def get_secret(key, default=None):
    """Get secret from Streamlit secrets or environment variables"""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

# API Keys
GROQ_API_KEY = str(get_secret('GROQ_API_KEY')).strip() if get_secret('GROQ_API_KEY') else None
OPENAI_API_KEY = str(get_secret('OPENAI_API_KEY')).strip() if get_secret('OPENAI_API_KEY') else None

# Model Selection (Switch between Groq and OpenAI)
USE_GROQ = str(get_secret('USE_GROQ', 'true')).lower().strip() == 'true'

# Model Configuration
GROQ_MODEL = get_secret('GROQ_MODEL', 'llama-3.3-70b-versatile')
OPENAI_MODEL = get_secret('OPENAI_MODEL', 'gpt-4')
TEMPERATURE = float(get_secret('TEMPERATURE', 0.7))

# Available Groq Models (all FREE!)
GROQ_MODELS = {
    'llama-3.3-70b': 'llama-3.3-70b-versatile',      # BEST - Recommended!
    'llama-3.1-8b': 'llama-3.1-8b-instant',          # Fastest
    'llama-4-scout': 'meta-llama/llama-4-scout-17b-16e-instruct',  # Latest Llama 4
    'qwen-3-32b': 'qwen/qwen3-32b',                  # Alternative
    'whisper-turbo': 'whisper-large-v3-turbo'        # For audio transcription
}
# Paths
VECTOR_DB_PATH = 'data/vector_db'
STUDY_MATERIALS_PATH = 'data/study_materials'
USER_DATA_PATH = 'data/user_data'

# RAG Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TOP_K_RESULTS = 3

# Reminder Configuration
DEFAULT_REMINDER_HOUR = 9
DEFAULT_REMINDER_MINUTE = 0

# Helper function to get LLM
def get_llm():
    """Returns appropriate LLM based on configuration"""
    if USE_GROQ:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            temperature=TEMPERATURE,
            groq_api_key=GROQ_API_KEY
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=TEMPERATURE,
            openai_api_key=OPENAI_API_KEY
        )

def switch_to_openai():
    """Switch to OpenAI GPT-4 for final demo"""
    global USE_GROQ
    USE_GROQ = False
    print("✅ Switched to OpenAI GPT-4")

def switch_to_groq():
    """Switch back to Groq (free)"""
    global USE_GROQ
    USE_GROQ = True
    print("✅ Switched to Groq (FREE)")
