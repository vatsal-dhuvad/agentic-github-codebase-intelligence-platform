import ast
import json
from pathlib import Path

from src.models.schemas import RepoFile, RepoMetadata


def extract_python_symbols(content: str) -> dict[str, list[str]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"classes": [], "functions": []}

    classes = []
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
    return {"classes": classes[:30], "functions": functions[:50]}


def summarize_file(file: RepoFile) -> str:
    symbols = ""
    if file.language == "Python":
        parsed = extract_python_symbols(file.content)
        if parsed["classes"] or parsed["functions"]:
            symbols = (
                f"\nClasses: {', '.join(parsed['classes']) or 'None'}"
                f"\nFunctions: {', '.join(parsed['functions']) or 'None'}"
            )

    return (
        f"File: {file.path}\n"
        f"Language: {file.language}\n"
        f"Size KB: {file.size_kb}"
        f"{symbols}\n"
        f"Content:\n{file.content}"
    )


def build_local_summary(metadata: RepoMetadata, files: list[RepoFile]) -> str:
    language_text = ", ".join(f"{lang}: {count}" for lang, count in metadata.languages.items())
    important_files = [file.path for file in files[:25]]
    return (
        f"Repository: {metadata.name}\n"
        f"URL: {metadata.repo_url}\n"
        f"Selected files: {metadata.selected_files} / {metadata.total_files}\n"
        f"Repository size: {metadata.total_size_mb} MB\n"
        f"Languages: {language_text or 'Unknown'}\n"
        f"Entry points: {', '.join(metadata.entry_points) or 'Not detected'}\n"
        f"Package/config files: {', '.join(metadata.package_files) or 'Not detected'}\n"
        f"Important files: {', '.join(important_files)}\n"
        f"TODO/FIXME findings: {len(metadata.todos)}"
    )


def build_setup_hints(files: list[RepoFile]) -> str:
    hints = []
    file_map = {Path(file.path).name.lower(): file.content for file in files}

    if "requirements.txt" in file_map:
        hints.append("Python project detected from requirements.txt.")
        hints.append("Install dependencies with: pip install -r requirements.txt")
    if "pyproject.toml" in file_map:
        hints.append("Python pyproject.toml detected.")
        hints.append("Install with a modern Python package manager such as uv or pip.")
    if "package.json" in file_map:
        hints.append("Node.js project detected from package.json.")
        try:
            package_data = json.loads(file_map["package.json"])
            scripts = package_data.get("scripts", {})
            if scripts:
                hints.append("Available npm scripts: " + ", ".join(scripts.keys()))
        except json.JSONDecodeError:
            pass
        hints.append("Install dependencies with: npm install")
    if "dockerfile" in file_map:
        hints.append("Dockerfile detected. Project can be containerized.")
    if not hints:
        hints.append("No standard dependency file was detected. Review README and entry points manually.")

    return "\n".join(f"- {hint}" for hint in hints)

