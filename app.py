import json
import time

import pandas as pd
import streamlit as st

from src.agent.workflow import analyze_repository, ask_repo_question
from src.config import APP_NAME, APP_TAGLINE, EMBEDDING_MODEL, MAX_FILE_KB, MAX_FILES, MAX_REPO_MB
from src.models.llm_client import available_llm_names
from src.tools.repo_loader import load_repo_files
from src.tools.vector_store import build_vector_store


st.set_page_config(
    page_title="GitHub codebase intelligence",
    page_icon=":material/code:",
    layout="wide",
)


def init_state() -> None:
    st.session_state.setdefault("metadata", None)
    st.session_state.setdefault("files", [])
    st.session_state.setdefault("report", None)
    st.session_state.setdefault("vector_store", None)
    st.session_state.setdefault("last_repo_url", "")


def report_to_markdown(report) -> str:
    return f"""# {report.repo_name} - Agentic codebase report

## Source summary
{report.source_summary}

## Architecture summary
{report.architecture_summary}

## Mermaid diagram
```mermaid
{report.mermaid_diagram}
```

## Setup guide
{report.setup_guide}

## Code walkthrough
{report.code_walkthrough}

## Risks and TODOs
{report.risks_and_todos}

## README draft
{report.readme_draft}
"""


def show_sidebar() -> None:
    with st.sidebar:
        st.header("Project stack")
        st.write("LangChain")
        st.write("LangGraph")
        st.write("FAISS")
        st.write("Hugging Face embeddings")
        st.write("Gemini / Groq / Mistral fallback")
        st.write("GitPython")
        st.write("NetworkX")
        st.write("FastAPI")
        st.write("Docker")
        st.caption("Local embeddings keep vector search free.")

        st.header("Free limits")
        st.write(f"Repo size: {MAX_REPO_MB} MB")
        st.write(f"Files indexed: {MAX_FILES}")
        st.write(f"File size: {MAX_FILE_KB} KB")

        providers = available_llm_names()
        if providers:
            st.success("LLM ready: " + " -> ".join(providers), icon=":material/check_circle:")
        else:
            st.warning("No API key found. Local analysis still works, AI sections will be limited.", icon=":material/warning:")


def show_metrics(metadata) -> None:
    cols = st.columns(4)
    cols[0].metric("Selected files", metadata.selected_files)
    cols[1].metric("Total files", metadata.total_files)
    cols[2].metric("Repo size", f"{metadata.total_size_mb} MB")
    cols[3].metric("Languages", len(metadata.languages))


def analyze_with_progress(repo_url: str):
    with st.status("Analyzing repository...", expanded=True) as status:
        st.write("Cloning public GitHub repository...")
        time.sleep(0.2)
        metadata, files = load_repo_files(repo_url)

        st.write("Reading important source files...")
        st.write(f"Selected {metadata.selected_files} files for analysis.")

        st.write("Building local embeddings and FAISS vector store...")
        vector_store = build_vector_store(metadata, files)

        st.write("Running LangGraph agents...")
        report = analyze_repository(metadata, files)

        status.update(label="Repository analysis complete.", state="complete", expanded=False)
        return metadata, files, vector_store, report


def main() -> None:
    init_state()
    show_sidebar()

    st.title(APP_NAME)
    st.caption(APP_TAGLINE)

    top_cols = st.columns([2, 1], vertical_alignment="center")
    with top_cols[0]:
        with st.form("repo_form", border=False):
            repo_url = st.text_input(
                "GitHub repository URL",
                placeholder="https://github.com/owner/repository",
                value=st.session_state["last_repo_url"],
            )
            submitted = st.form_submit_button("Analyze repository", type="primary", icon=":material/play_arrow:")
    with top_cols[1]:
        st.container(border=True).write(
            f"Embedding model: `{EMBEDDING_MODEL}`\n\n"
            "The app indexes code locally with FAISS, then uses agent workflow for explanations."
        )

    if submitted:
        if not repo_url.strip():
            st.warning("Please enter a GitHub repository URL.", icon=":material/warning:")
        else:
            try:
                metadata, files, vector_store, report = analyze_with_progress(repo_url)
                st.session_state["metadata"] = metadata
                st.session_state["files"] = files
                st.session_state["vector_store"] = vector_store
                st.session_state["report"] = report
                st.session_state["last_repo_url"] = repo_url
                st.toast("Repository analysis completed.", icon=":material/check_circle:")
            except Exception as error:
                st.error(str(error), icon=":material/error:")

    metadata = st.session_state["metadata"]
    report = st.session_state["report"]
    files = st.session_state["files"]

    if metadata is None or report is None:
        st.subheader("What this project does")
        c1, c2, c3 = st.columns(3)
        with c1.container(border=True):
            st.markdown("**Analyze architecture**")
            st.caption("Find entry points, folders, dependencies, and code flow.")
        with c2.container(border=True):
            st.markdown("**Generate docs**")
            st.caption("Create setup guide, README draft, and Mermaid diagrams.")
        with c3.container(border=True):
            st.markdown("**Ask code questions**")
            st.caption("Use RAG over selected repo files with FAISS retrieval.")
        return

    show_metrics(metadata)

    lang_rows = [{"Language": lang, "Files": count} for lang, count in metadata.languages.items()]
    if lang_rows:
        st.bar_chart(pd.DataFrame(lang_rows).set_index("Language"))

    tabs = st.tabs(
        [
            "Overview",
            "Architecture",
            "Setup",
            "Code walkthrough",
            "Risks and TODOs",
            "README draft",
            "Ask codebase",
            "Files",
        ]
    )

    with tabs[0]:
        st.subheader("Repository overview")
        st.markdown(report.source_summary)
        st.markdown("**Entry points**")
        st.write(metadata.entry_points or "No standard entry point detected.")
        st.markdown("**Package/config files**")
        st.write(metadata.package_files or "No package/config files detected.")

    with tabs[1]:
        st.subheader("Architecture")
        st.markdown(report.architecture_summary)
        st.code(report.mermaid_diagram, language="mermaid")

    with tabs[2]:
        st.subheader("Setup guide")
        st.markdown(report.setup_guide)

    with tabs[3]:
        st.subheader("Code walkthrough")
        st.markdown(report.code_walkthrough)

    with tabs[4]:
        st.subheader("Risks and TODOs")
        st.markdown(report.risks_and_todos)
        if metadata.todos:
            with st.expander("Detected TODO/FIXME lines", icon=":material/search:"):
                st.write(metadata.todos)

    with tabs[5]:
        st.subheader("README draft")
        st.markdown(report.readme_draft)

    with tabs[6]:
        st.subheader("Ask codebase")
        question = st.text_area(
            "Your question",
            placeholder="Example: How does this project start? Which files should I read first?",
            height=120,
        )
        if st.button("Ask", type="primary", icon=":material/send:"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.status("Retrieving code context...", expanded=False) as status:
                    answer = ask_repo_question(st.session_state["vector_store"], question)
                    status.update(label="Answer ready.", state="complete")
                st.markdown(answer)

    with tabs[7]:
        st.subheader("Indexed files")
        file_rows = [
            {"Path": file.path, "Language": file.language, "Size KB": file.size_kb}
            for file in files
        ]
        st.dataframe(pd.DataFrame(file_rows), width="stretch", hide_index=True)

    report_markdown = report_to_markdown(report)
    st.download_button(
        "Download full report",
        data=report_markdown,
        file_name=f"{metadata.name}_agentic_codebase_report.md",
        mime="text/markdown",
        icon=":material/download:",
    )
    st.download_button(
        "Download metadata JSON",
        data=json.dumps(metadata.model_dump(), indent=2),
        file_name=f"{metadata.name}_metadata.json",
        mime="application/json",
        icon=":material/database:",
    )


main()

