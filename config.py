import os

# --- Environment ---
PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

# --- LLM (OpenAI) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1")
MAX_TOKENS = 4096

# --- Browser ---
HEADLESS = PRODUCTION or os.getenv("HEADLESS", "false").lower() == "true"
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 900
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
NAVIGATION_TIMEOUT = 30_000  # ms

# --- Chunking ---
MAX_CHUNK_CHARS = 1500

# --- Embeddings ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- Vector DB ---
CHROMA_COLLECTION = "page_elements"
TOP_K_RESULTS = 10

# --- Test Data ---
EMAIL_PREFIX = "vexel"
EMAIL_DOMAIN = "yopmail.com"

# --- Agent Loop ---
MAX_STEPS = 30
GOAL_QUERY = "Find the next interactive action: signup, login, payment, form submission, navigation, or button click"
