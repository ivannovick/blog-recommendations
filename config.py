"""
Centralized configuration for blog recommendations project.
Loads configuration from environment variables with sensible defaults.
Supports both OpenAI API and local models via OpenAI-compatible endpoints.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
GP_HOST = os.getenv('GP_HOST', 'localhost')
GP_PORT = os.getenv('GP_PORT', '15432')
GP_USER = os.getenv('GP_USER', 'gpadmin')
DB_NAME = os.getenv('DB_NAME', 'blog_recommendations')

# API Configuration
USE_LOCAL_MODELS = os.getenv('USE_LOCAL_MODELS', 'true').lower() == 'true'
LOCAL_API_BASE = os.getenv('LOCAL_API_BASE', 'http://127.0.0.1:1234/v1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'local-key')  # Default for local models

# Validate API key for OpenAI (not needed for local)
if not USE_LOCAL_MODELS and not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable not set for OpenAI API!")

# Model Configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-nomic-embed-text-v2')
EMBEDDING_DIMENSIONS = int(os.getenv('EMBEDDING_DIMENSIONS', '1536'))
CHAT_MODEL = os.getenv('CHAT_MODEL', 'qwen/qwen3-4b-2507')
CLUSTER_SAMPLE_SIZE = int(os.getenv('CLUSTER_SAMPLE_SIZE', '40'))

# Web Application Configuration
WEB_PORT = int(os.getenv('WEB_PORT', '8080'))

# Connection string helper
def get_connection_string():
    """Returns psycopg2 connection string"""
    return f"dbname={DB_NAME} user={GP_USER} host={GP_HOST} port={GP_PORT}"

# Connection parameters helper
def get_connection_params():
    """Returns connection parameters as dict"""
    return {
        'host': GP_HOST,
        'port': GP_PORT,
        'user': GP_USER,
        'dbname': DB_NAME
    }

# OpenAI client configuration helper
def get_openai_client():
    """Returns configured OpenAI client for local or remote API"""
    import openai

    if USE_LOCAL_MODELS:
        return openai.OpenAI(
            base_url=LOCAL_API_BASE,
            api_key=OPENAI_API_KEY  # Can be anything for local models
        )
    else:
        return openai.OpenAI(api_key=OPENAI_API_KEY)

# Legacy compatibility - configure global openai module
def configure_openai():
    """Configure the global openai module (for legacy code compatibility)"""
    import openai

    openai.api_key = OPENAI_API_KEY
    if USE_LOCAL_MODELS:
        openai.base_url = LOCAL_API_BASE

# Display configuration on import (mask sensitive values)
def _display_config():
    """Display current configuration with masked sensitive values"""
    print("=" * 50)
    print("Configuration Loaded:")
    print("=" * 50)
    print(f"Database:")
    print(f"  GP_HOST: {GP_HOST}")
    print(f"  GP_PORT: {GP_PORT}")
    print(f"  GP_USER: {GP_USER}")
    print(f"  DB_NAME: {DB_NAME}")
    print(f"\nAPI:")
    print(f"  USE_LOCAL_MODELS: {USE_LOCAL_MODELS}")
    print(f"  LOCAL_API_BASE: {LOCAL_API_BASE}")
    print(f"  OPENAI_API_KEY: {'***' if OPENAI_API_KEY and not OPENAI_API_KEY == 'local-key' else OPENAI_API_KEY}")
    print(f"\nModels:")
    print(f"  EMBEDDING_MODEL: {EMBEDDING_MODEL}")
    print(f"  EMBEDDING_DIMENSIONS: {EMBEDDING_DIMENSIONS}")
    print(f"  CHAT_MODEL: {CHAT_MODEL}")
    print(f"  CLUSTER_SAMPLE_SIZE: {CLUSTER_SAMPLE_SIZE}")
    print(f"\nWeb:")
    print(f"  WEB_PORT: {WEB_PORT}")
    print("=" * 50)

# Display config when module is imported
_display_config()