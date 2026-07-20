from typing import TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from src.models.llm_client import get_llm
from src.models.schemas import AnalysisReport, RepoFile, RepoMetadata
from src.prompts.system_prompts import (
    ARCHITECTURE_PROMPT,
    MAIN_SYSTEM_PROMPT,
    README_PROMPT,
    RISK_PROMPT,
    SETUP_PROMPT,
)
from src.tools.code_parser import build_local_summary, build_setup_hints
from src.tools.dependency_graph import graph_to_mermaid
from src.tools.vector_store import build_vector_store, retrieve_context


class AgentState(TypedDict):
    metadata: RepoMetadata
    files: list[RepoFile]
    local_summary: str
    setup_hints: str
    mermaid_diagram: str
    vector_store: object
    architecture_summary: str
    setup_guide: str
    code_walkthrough: str
    risks_and_todos: str
    readme_draft: str
    final_report: AnalysisReport


def run_prompt(llm, task_prompt: str, context: str) -> str:
    if llm is None:
        return local_fallback_answer(task_prompt, context)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MAIN_SYSTEM_PROMPT),
            ("human", "{task_prompt}\n\nRepository context:\n{context}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"task_prompt": task_prompt, "context": context}).strip()


def local_fallback_answer(task_prompt: str, context: str) -> str:
    return (
        "AI API key is not configured, so this section is generated from local repository signals.\n\n"
        + context[:2500]
    )


def prepare_context_agent(state: AgentState) -> AgentState:
    metadata = state["metadata"]
    files = state["files"]
    state["local_summary"] = build_local_summary(metadata, files)
    state["setup_hints"] = build_setup_hints(files)
    state["mermaid_diagram"] = graph_to_mermaid(files)
    state["vector_store"] = build_vector_store(metadata, files)
    return state


def architecture_agent(state: AgentState) -> AgentState:
    llm = get_llm()
    context = retrieve_context(
        state["vector_store"],
        "architecture folders entry points dependencies project purpose",
    )
    context += "\n\nLocal summary:\n" + state["local_summary"]
    context += "\n\nMermaid diagram:\n" + state["mermaid_diagram"]
    state["architecture_summary"] = run_prompt(llm, ARCHITECTURE_PROMPT, context)
    return state


def setup_agent(state: AgentState) -> AgentState:
    llm = get_llm()
    context = retrieve_context(
        state["vector_store"],
        "requirements package json pyproject dockerfile env setup run commands",
    )
    context += "\n\nLocal setup hints:\n" + state["setup_hints"]
    state["setup_guide"] = run_prompt(llm, SETUP_PROMPT, context)
    return state


def walkthrough_agent(state: AgentState) -> AgentState:
    llm = get_llm()
    context = retrieve_context(
        state["vector_store"],
        "main files important functions classes app workflow",
    )
    state["code_walkthrough"] = run_prompt(
        llm,
        "Explain the most important files and how a beginner should read this codebase.",
        context,
    )
    return state


def risk_agent(state: AgentState) -> AgentState:
    llm = get_llm()
    context = retrieve_context(
        state["vector_store"],
        "todo fixme error auth env secrets config risks tests",
    )
    if state["metadata"].todos:
        context += "\n\nDetected TODO/FIXME lines:\n" + "\n".join(state["metadata"].todos)
    state["risks_and_todos"] = run_prompt(llm, RISK_PROMPT, context)
    return state


def readme_agent(state: AgentState) -> AgentState:
    llm = get_llm()
    context = (
        state["local_summary"]
        + "\n\nSetup hints:\n"
        + state["setup_hints"]
        + "\n\nArchitecture:\n"
        + state["architecture_summary"]
    )
    state["readme_draft"] = run_prompt(llm, README_PROMPT, context)
    return state


def final_report_agent(state: AgentState) -> AgentState:
    metadata = state["metadata"]
    source_summary = (
        f"Analyzed {metadata.selected_files} selected files from {metadata.total_files} total files. "
        f"Languages: {metadata.languages}."
    )
    state["final_report"] = AnalysisReport(
        repo_name=metadata.name,
        architecture_summary=state["architecture_summary"],
        setup_guide=state["setup_guide"],
        code_walkthrough=state["code_walkthrough"],
        risks_and_todos=state["risks_and_todos"],
        readme_draft=state["readme_draft"],
        mermaid_diagram=state["mermaid_diagram"],
        source_summary=source_summary,
    )
    return state


def create_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("prepare_context", prepare_context_agent)
    graph.add_node("architecture", architecture_agent)
    graph.add_node("setup", setup_agent)
    graph.add_node("walkthrough", walkthrough_agent)
    graph.add_node("risk", risk_agent)
    graph.add_node("readme", readme_agent)
    graph.add_node("final_report", final_report_agent)

    graph.set_entry_point("prepare_context")
    graph.add_edge("prepare_context", "architecture")
    graph.add_edge("architecture", "setup")
    graph.add_edge("setup", "walkthrough")
    graph.add_edge("walkthrough", "risk")
    graph.add_edge("risk", "readme")
    graph.add_edge("readme", "final_report")
    graph.add_edge("final_report", END)
    return graph.compile()


def analyze_repository(metadata: RepoMetadata, files: list[RepoFile]) -> AnalysisReport:
    workflow = create_workflow()
    result = workflow.invoke({"metadata": metadata, "files": files})
    return result["final_report"]


def ask_repo_question(vector_store, question: str) -> str:
    llm = get_llm()
    context = retrieve_context(vector_store, question)
    return run_prompt(
        llm,
        "Answer the user's codebase question directly using the repository context.",
        f"Question: {question}\n\n{context}",
    )

