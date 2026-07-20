import hashlib
import shutil
from pathlib import Path
from urllib.parse import urlparse

from git import Repo

from src.config import MAX_FILES, MAX_REPO_MB, REPO_CACHE_DIR
from src.models.schemas import RepoFile, RepoMetadata
from src.utils.file_utils import is_supported_file, language_from_path, read_text_file, should_skip_path
from src.utils.text import clean_text


def normalize_github_url(repo_url: str) -> str:
    repo_url = repo_url.strip()
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    parsed = urlparse(repo_url)
    if parsed.netloc.lower() != "github.com":
        raise ValueError("Please enter a public GitHub repository URL.")
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        raise ValueError("GitHub URL must include owner and repository name.")
    return f"https://github.com/{path_parts[0]}/{path_parts[1]}"


def clone_public_repo(repo_url: str) -> Path:
    normalized_url = normalize_github_url(repo_url)
    REPO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    repo_key = hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:12]
    target_dir = REPO_CACHE_DIR / repo_key

    if target_dir.exists():
        shutil.rmtree(target_dir)

    Repo.clone_from(normalized_url, target_dir, depth=1)
    return target_dir


def get_repo_size_mb(repo_path: Path) -> float:
    total_size = 0
    for file_path in repo_path.rglob("*"):
        if file_path.is_file() and not should_skip_path(file_path.relative_to(repo_path)):
            total_size += file_path.stat().st_size
    return round(total_size / (1024 * 1024), 2)


def load_repo_files(repo_url: str) -> tuple[RepoMetadata, list[RepoFile]]:
    local_path = clone_public_repo(repo_url)
    repo_size = get_repo_size_mb(local_path)
    if repo_size > MAX_REPO_MB:
        raise ValueError(f"Repository is too large for free analysis. Limit is {MAX_REPO_MB} MB.")

    selected_files = []
    package_files = []
    entry_points = []
    todos = []
    imports = []
    languages = {}

    all_files = [path for path in local_path.rglob("*") if path.is_file()]
    for file_path in all_files:
        relative_path = file_path.relative_to(local_path)
        if should_skip_path(relative_path) or not is_supported_file(relative_path):
            continue
        if len(selected_files) >= MAX_FILES:
            break

        content = clean_text(read_text_file(file_path))
        if not content:
            continue

        path_text = str(relative_path).replace("\\", "/")
        language = language_from_path(path_text)
        languages[language] = languages.get(language, 0) + 1
        selected_files.append(
            RepoFile(
                path=path_text,
                language=language,
                content=content,
                size_kb=round(file_path.stat().st_size / 1024, 2),
            )
        )

        lower_name = file_path.name.lower()
        if lower_name in {"requirements.txt", "package.json", "pyproject.toml", "dockerfile"}:
            package_files.append(path_text)
        if lower_name in {"app.py", "main.py", "streamlit_app.py", "server.py", "index.js"}:
            entry_points.append(path_text)
        for line_no, line in enumerate(content.splitlines(), 1):
            line_lower = line.lower()
            if "todo" in line_lower or "fixme" in line_lower:
                todos.append(f"{path_text}:{line_no} - {line.strip()[:140]}")
            if line.strip().startswith(("import ", "from ", "require(", "const ", "import{")):
                imports.append(f"{path_text}: {line.strip()[:140]}")

    repo_name = normalize_github_url(repo_url).split("/")[-1]
    metadata = RepoMetadata(
        repo_url=normalize_github_url(repo_url),
        local_path=str(local_path),
        name=repo_name,
        total_files=len(all_files),
        selected_files=len(selected_files),
        total_size_mb=repo_size,
        languages=languages,
        package_files=package_files[:20],
        entry_points=entry_points[:20],
        todos=todos[:40],
        imports=imports[:80],
    )
    return metadata, selected_files

