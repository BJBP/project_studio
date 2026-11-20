# Builds the repository from the environment: STUDIO_DATA is the user's data folder (default: the sibling
# folder project_studio_data). The program folder is this repository.
import os
from pathlib import Path

from studio.infrastructure.json_repository import JsonRepository
from studio.infrastructure.module_store import JsonModuleStore

PROGRAM_DIR = Path(__file__).resolve().parents[2]


def default_data_dir() -> Path:
    return Path(os.environ.get("STUDIO_DATA", PROGRAM_DIR.parent / "project_studio_data"))


def build_repo(data_dir: str | Path | None = None) -> JsonRepository:
    return JsonRepository(PROGRAM_DIR, Path(data_dir) if data_dir else default_data_dir())


def build_modules(repo: JsonRepository) -> JsonModuleStore:
    return JsonModuleStore(repo.program_dir, repo.data_dir)
