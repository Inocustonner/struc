# type: ignore | pylint erros cyclic import
from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from struc import Struct

DynAction = Callable[["Struct"], list[Any]]


class DynamicTypeResolution:
    action: DynAction
    args: list[Any] = []
    def __init__(self, action: DynAction):
        self.action = action

    def set_args(self, *args: Any):
        self.args = args

    def __call__(self, inst: Struct) -> list[Any]:
        return self.action(inst, *self.args)
