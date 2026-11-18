# Onion rule: an inner layer never imports an outer one (domain < application < infrastructure < presentation).
import ast
from pathlib import Path

LAYERS = ["domain", "application", "infrastructure", "presentation"]
STUDIO = Path(__file__).resolve().parents[2] / "studio"


def imported_layers(path: Path) -> set:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        names = [node.module] if isinstance(node, ast.ImportFrom) and node.module else \
            [a.name for a in node.names] if isinstance(node, ast.Import) else []
        found |= {n.split(".")[1] for n in names if n.startswith("studio.") and n.count(".") >= 1}
    return found & set(LAYERS)


def test_inner_layers_do_not_import_outer_ones():
    wrong = []
    for rank, layer in enumerate(LAYERS):
        for path in (STUDIO / layer).glob("*.py"):
            outer = {l for l in imported_layers(path) if LAYERS.index(l) > rank}
            wrong += [f"{path.name} -> {o}" for o in outer]
    assert wrong == []
