import re

import networkx as nx

from src.models.schemas import RepoFile


def extract_import_names(file: RepoFile) -> list[str]:
    names = []
    for line in file.content.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            names.extend(part.split()[0].split(".")[0] for part in stripped.replace("import ", "").split(","))
        elif stripped.startswith("from "):
            parts = stripped.split()
            if len(parts) >= 2:
                names.append(parts[1].split(".")[0])
        elif "from " in stripped and " import " in stripped:
            match = re.search(r"from ['\"]([^'\"]+)['\"]", stripped)
            if match:
                names.append(match.group(1).split("/")[0])
    return [name for name in names if name and name not in {".", ".."}][:30]


def build_dependency_graph(files: list[RepoFile]) -> nx.DiGraph:
    graph = nx.DiGraph()
    local_modules = {file.path.rsplit(".", 1)[0].replace("/", "."): file.path for file in files}
    short_modules = {module.split(".")[-1]: path for module, path in local_modules.items()}

    for file in files:
        graph.add_node(file.path)
        for imported_name in extract_import_names(file):
            target = short_modules.get(imported_name)
            if target and target != file.path:
                graph.add_edge(file.path, target)
    return graph


def graph_to_mermaid(files: list[RepoFile]) -> str:
    graph = build_dependency_graph(files)
    lines = ["flowchart TD"]
    if graph.number_of_edges() == 0:
        for index, file in enumerate(files[:12], 1):
            lines.append(f'  N{index}["{file.path}"]')
        return "\n".join(lines)

    node_ids = {}
    for index, node in enumerate(graph.nodes, 1):
        node_ids[node] = f"N{index}"
        lines.append(f'  {node_ids[node]}["{node}"]')
    for source, target in list(graph.edges)[:40]:
        lines.append(f"  {node_ids[source]} --> {node_ids[target]}")
    return "\n".join(lines)

