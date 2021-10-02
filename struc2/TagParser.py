from .Serialized import Serialized, SerializedFactory
from .Registry import TypeRegistry

from typing import Annotated, Any, Optional, Union, get_type_hints, Generator

class TagType:
    ser: Serialized[Any]
    def __init__(self, ser: Serialized[Any]):
        self.ser = ser

    @classmethod
    def parse_tags(cls, params: tuple[Any, ...]):
        def get_type(t: Union[type[SerializedFactory[Any]], str, Any]) -> Optional[type[SerializedFactory[Any]]]:
            if isinstance(t, str):
                return TypeRegistry.get_type(t)
            elif isinstance(t, type) and issubclass(t, SerializedFactory):
                return t
            else:
                return None

        def ser_gen(params: tuple[Any, ...]) -> Generator[Serialized[Any], None, None]:
            args = list[Any]()
            start = 0
            while (ser := get_type(params[start])) is None:
                args.append(params[start])
                start += 1
            yield ser.create(*args)
            args = []

            for p in params[start + 1:]:
                if (ser := get_type(p)) is not None:
                    yield ser.create(*args)
                    args = []
                else:
                    args.append(p)
            # yield cast(SerializedFactory[Any], ser).create(*args)

        g = ser_gen(params)
        ser = next(g)
        top = ser
        for ser_ in g:
            ser._compose(ser_)
            ser = ser_
        return TagType(top)

    @classmethod
    def __class_getitem__(cls, params: tuple[Any]):
        return cls.parse_tags(params)


# class Tag:
#     @classmethod
#     def __class_getitem__(cls, params: Any):
#         return Annotated[params[0], TagType[params[1:]]]

Tag = Annotated

class TagParser:
    _ser_tags: Optional[list[tuple[str, Serialized[Any]]]] = None

    @staticmethod
    def _is_tag(ann: Any) -> bool:
        return getattr(ann, '__metadata__', None) is not None

    @classmethod
    def _get_tags_(cls) -> list[tuple[str, Serialized[Any]]]:
        ser_tags = list[tuple[str, Serialized[Any]]]()
        for var, ann in get_type_hints(cls, include_extras=True).items():
            if TagParser._is_tag(ann):
                ser_tags.append((var, TagType[ann.__metadata__].ser))
        return ser_tags
        
    @classmethod
    def _get_tags(cls) -> list[tuple[str, Serialized[Any]]]:
        if cls._ser_tags is None:
            cls._ser_tags = cls._get_tags_()
        return cls._ser_tags