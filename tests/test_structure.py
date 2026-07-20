from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_files_exist():
    required_files = [
        "app.py",
        "README.md",
        "requirements.txt",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        "src/agent/workflow.py",
        "src/tools/repo_loader.py",
        "src/tools/vector_store.py",
        "src/models/llm_client.py",
    ]
    for file_name in required_files:
        assert (ROOT / file_name).exists(), file_name


def test_project_structure_exists():
    required_dirs = [
        "src/agent",
        "src/tools",
        "src/models",
        "src/prompts",
        "src/utils",
        "src/api",
        "tests",
        "data",
        "logs",
    ]
    for dir_name in required_dirs:
        assert (ROOT / dir_name).is_dir(), dir_name

