import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from the nearest .env file
load_dotenv(find_dotenv())

# Core service configuration
RAG_URL = os.getenv("RAG_URL", "http://127.0.0.1:8000")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Slack integration configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Dify (optional) – kept for parity with prior integrations
DIFY_API_KEY = os.getenv("DIFY_API_KEY")



