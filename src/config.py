from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPO_CACHE_DIR = DATA_DIR / "repos"
LOG_DIR = BASE_DIR / "logs"

APP_NAME = "Agentic GitHub Codebase Intelligence Platform"
APP_TAGLINE = (
    "Explain architecture, setup, risks, TODOs, and documentation from any public GitHub repository."
)

MAX_REPO_MB = 25
MAX_FILES = 120
MAX_FILE_KB = 220

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 180
RETRIEVAL_K = 8

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash-lite"
GROQ_MODEL = "llama-3.1-8b-instant"
MISTRAL_MODEL = "mistral-small-latest"

IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".exe",
    ".dll",
    ".so",
    ".mp4",
    ".mov",
}

IMPORTANT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".html",
    ".css",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".env.example",
    ".dockerfile",
}

