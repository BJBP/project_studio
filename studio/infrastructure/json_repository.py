# Stores the Studio on disk. The catalog and the example projects come from the program folder; the user's
# projects, progress and brand models live in the data folder (passed in, never inside the program).
# JsonRepository(program_dir, data_dir) implements studio.application.ports.StudioRepository.
import json
from pathlib import Path

DEFAULT_STATE = {"done": [], "bought": [], "units": 1, "chosen": {}, "names": {}}


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)  # never leaves a half-written file


class JsonRepository:
    def __init__(self, program_dir: Path, data_dir: Path):
        self.program_dir, self.data_dir = Path(program_dir), Path(data_dir)
        self.projects_dir = self.data_dir / "projects"
        self._seed_examples()

    def _seed_examples(self) -> None:
        """First run: the user's data folder starts with the neutral example projects."""
        if self.projects_dir.exists() and any(self.projects_dir.iterdir()):
            return
        for example in sorted((self.program_dir / "examples" / "projects").glob("*.json")):
            project = _read(example)
            for choice in project["slots"].values():
                choice.setdefault("default", choice["component"])
            self.save_project(project)

    def _folder(self, name: str) -> dict:
        return {data["id"]: data for data in map(_read, sorted((self.program_dir / "catalog" / name).glob("*.json")))}

    def catalog(self) -> dict:
        return self._folder("components")

    def equipment(self) -> dict:
        return self._folder("equipment")

    def models(self) -> list:
        path = self.data_dir / "catalog" / "models.json"
        return _read(path)["models"] if path.exists() else []

    def project_ids(self) -> list:
        if not self.projects_dir.exists():
            return []
        return sorted(p.name for p in self.projects_dir.iterdir() if (p / "project.json").exists())

    def load_project(self, project_id: str) -> dict:
        path = self.projects_dir / project_id / "project.json"
        if "/" in project_id or "\\" in project_id or ".." in project_id or not path.exists():
            raise KeyError(project_id)
        return _read(path)

    def save_project(self, project: dict) -> None:
        _write(self.projects_dir / project["id"] / "project.json", project)

    def load_state(self, project_id: str) -> dict:
        path = self.projects_dir / project_id / "state.json"
        return {**DEFAULT_STATE, **(_read(path) if path.exists() else {})}

    def save_state(self, project_id: str, state: dict) -> None:
        _write(self.projects_dir / project_id / "state.json", state)
