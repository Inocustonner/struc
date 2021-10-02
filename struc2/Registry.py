# from typing import 
from .Serialized import SerializedFactory
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    T = TypeVar('T', bound='SerializedFactory[Any]')

class TypeRegistry:
    @staticmethod
    def register_type(name: str, type_: type[SerializedFactory[Any]]) -> None:
        setattr(TypeRegistry, name, type_)

    @staticmethod
    def get_type(name: str) -> type[SerializedFactory[Any]]:
        if TypeRegistry.has_type(name):
            return getattr(TypeRegistry, name)
        raise ValueError(f"Unknown struc type `{name}`")
    
    @staticmethod
    def has_type(name: str) -> bool:
        return getattr(TypeRegistry, name, None) is not None


def register_type(c: type['T']) -> type['T']:
    name = getattr(c, '_name', c.__name__)
    TypeRegistry.register_type(name, c)
    return c