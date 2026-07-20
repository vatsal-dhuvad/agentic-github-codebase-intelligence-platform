from pydantic import BaseModel, Field


class RepoFile(BaseModel):
    path: str
    language: str
    content: str
    size_kb: float


class RepoMetadata(BaseModel):
    repo_url: str
    local_path: str
    name: str
    total_files: int = 0
    selected_files: int = 0
    total_size_mb: float = 0.0
    languages: dict[str, int] = Field(default_factory=dict)
    package_files: list[str] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    todos: list[str] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    repo_name: str
    architecture_summary: str
    setup_guide: str
    code_walkthrough: str
    risks_and_todos: str
    readme_draft: str
    mermaid_diagram: str
    source_summary: str

