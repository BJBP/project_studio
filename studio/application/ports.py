# Port the use cases need: where the catalog, projects and their progress live. Infrastructure implements it.
from typing import Protocol


class StudioRepository(Protocol):
    def catalog(self) -> dict: ...                      # component id -> component
    def equipment(self) -> dict: ...                    # equipment id -> profile
    def models(self) -> list: ...                       # brand models with offers (local data only)
    def project_ids(self) -> list: ...
    def load_project(self, project_id: str) -> dict: ...    # raises KeyError when it does not exist
    def save_project(self, project: dict) -> None: ...
    def load_state(self, project_id: str) -> dict: ...      # {"done": [], "bought": [], "units": 1, "chosen": {}}
    def save_state(self, project_id: str, state: dict) -> None: ...
