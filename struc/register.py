# from typing import 
from .Serializable import Serializable
from typing import Any, Optional, cast, Type

class TypeRegister:
    @staticmethod
    def register_type(name: str, type_: Type[Serializable[Any]]) -> None:
        setattr(TypeRegister, name, type_)

    @staticmethod
    def get_type(name: str) -> Optional[Type[Serializable[Any]]]:
        return cast(Optional[Type[Serializable[Any]]], getattr(TypeRegister, name))


def register_type(c: Type[Serializable[Any]]) -> Type[Serializable[Any]]:
    if getattr(c, '_name', None) is None:
        setattr(c, '_name', c.__name__)
    TypeRegister.register_type(getattr(c, '_name'), c)
    return c