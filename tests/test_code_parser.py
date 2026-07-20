from src.models.schemas import RepoFile, RepoMetadata
from src.tools.code_parser import build_local_summary, extract_python_symbols


def test_extract_python_symbols():
    content = """
class Demo:
    pass

def run_app():
    return True
"""
    result = extract_python_symbols(content)
    assert "Demo" in result["classes"]
    assert "run_app" in result["functions"]


def test_build_local_summary():
    metadata = RepoMetadata(
        repo_url="https://github.com/example/demo",
        local_path="data/repos/demo",
        name="demo",
        total_files=2,
        selected_files=1,
        total_size_mb=0.1,
        languages={"Python": 1},
    )
    files = [RepoFile(path="app.py", language="Python", content="print('hi')", size_kb=1)]
    summary = build_local_summary(metadata, files)
    assert "demo" in summary
    assert "Python" in summary

