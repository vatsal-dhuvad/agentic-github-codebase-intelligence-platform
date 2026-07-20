from pathlib import Path

from src.config import BINARY_EXTENSIONS, IGNORE_DIRS, IMPORTANT_EXTENSIONS, MAX_FILE_KB


def should_skip_path(path: Path) -> bool:
    parts = set(path.parts)
    if parts.intersection(IGNORE_DIRS):
        return True
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    return False


def is_supported_file(path: Path) -> bool:
    if path.name.lower() in {"dockerfile", "makefile", "requirements.txt", "package.json"}:
        return True
    if path.suffix.lower() in IMPORTANT_EXTENSIONS:
        return True
    return False


def read_text_file(path: Path) -> str:
    size_kb = path.stat().st_size / 1024
    if size_kb > MAX_FILE_KB:
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def language_from_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    mapping = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "React JSX",
        ".ts": "TypeScript",
        ".tsx": "React TSX",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".php": "PHP",
        ".rb": "Ruby",
        ".html": "HTML",
        ".css": "CSS",
        ".md": "Markdown",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
    }
    if Path(path).name.lower() == "dockerfile":
        return "Docker"
    return mapping.get(suffix, "Text")

