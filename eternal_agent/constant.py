import logging
import os

logger = logging.getLogger(__name__)

def get_env_and_warning(key: str, default=None):
    if key not in os.environ:
        logger.warning(f"{key} not found in environment")
        return default
    
    return os.getenv(key)

# TODO: break this file into smaller parts and assign to each package
ETERNAL_X_API = get_env_and_warning("ETERNAL_X_API", "").rstrip("/")
ETERNAL_X_API_APIKEY = get_env_and_warning("ETERNAL_X_API_APIKEY")
IS_SANDBOX = get_env_and_warning("IS_SANDBOX", "0") == "1"

ETERNAL_BACKEND_API = get_env_and_warning("ETERNAL_BACKEND_API", "").rstrip("/")
ETERNAL_BACKEND_API_APIKEY = get_env_and_warning("ETERNAL_BACKEND_API_APIKEY") 

ETERNAL_API_CHAIN_ID = os.getenv("ETERNAL_API_CHAIN_ID", "8453")

# for trading, not available in the current version
CHAIN_ID=None
CONTRACT_ID=None 

AUTO_SERVICE_SLEEP_TIME = 10

DEFAULT_TOP_K = 3
DEFAULT_BIO_MAX_LENGTH = 20
DEFAULT_LORE_MAX_LENGTH = 20
DEFAULT_KNOWLEDGE_MAX_LENGTH = 30
DEFAULT_EXAMPLE_POSTS_MAX_LENGTH = 15
DEFAULT_INTERESTED_TOPICS_MAX_LENGTH = 10

APP_NAME = "Eternal Agent"