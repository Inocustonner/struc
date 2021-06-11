from __future__ import annotations
from abc import ABC, abstractmethod
import struc

from typing import (
    Callable,
    Generator,
    Type,
    TypeVar,
    Any,
    Union,
    get_type_hints,
)
from .Serializable import (
    Serializable,
    GenericSeril,
    ArraySeril,
    DynamicValue,
    SerializableFactory,
)
from .register import TypeRegister, register_type
from .defs import *
from .Dynamic import DynAction, DynamicTypeResolution


@register_type
class char(GenericSeril[bytes]):
    data_len = 1
    struct_fmt = "c"


@register_type
class i8(GenericSeril[int]):
    data_len = 1
    struct_fmt = "b"


@register_type
class u8(GenericSeril[int]):
    data_len = 1
    struct_fmt = "B"


@register_type
class i16(GenericSeril[int]):
    data_len = 2
    struct_fmt = "h"


@register_type
class u16(GenericSeril[int]):
    data_len = 2
    struct_fmt = "H"


@register_type
class i32(GenericSeril[int]):
    data_len = 4
    struct_fmt = "i"


@register_type
class u32(GenericSeril[int]):
    data_len = 4
    struct_fmt = "I"


@register_type
class i64(GenericSeril[int]):
    data_len = 8
    struct_fmt = "q"


@register_type
class u64(GenericSeril[int]):
    data_len = 8
    struct_fmt = "Q"


@register_type
class f32(GenericSeril[float]):
    data_len = 4
    struct_fmt = "f"


@register_type
class f64(GenericSeril[float]):
    data_len = 8
    struct_fmt = "d"


T = TypeVar("T")
U = TypeVar("U")


@register_type
class _sized_array(ArraySeril[list[T], T]):  # type: ignore
    _name = "[]"

    @staticmethod
    def transform(arr: list[T]) -> list[T]:
        return arr


@register_type
class cstring(ArraySeril[bytes, bytes]):
    length = 0
    stop_char = b"\0"

    def __init__(self, length: int = 0):
        if length < 0:
            raise ValueError(f"Length argument must be > 0, given {length}")
        self.length = length
        super().__init__(char(), length)

    def _from_bytes(self, byte_array: bytes) -> tuple[bytes, int]:
        dynamic = False
        if self.length <= 0:
            dynamic = True
            self.length = byte_array.index(self.stop_char)
        val, len = super()._from_bytes(byte_array)
        if dynamic:
            len += 1
        return val, len

    @staticmethod
    def transform(arr: list[bytes]) -> bytes:
        return b"".join(arr)

    def __len__(self) -> int:
        return self.length


class DTR:
    @classmethod
    def __class_getitem__(cls, param: DynAction):
        # if isinstance(param, DynAction):
        return DynamicTypeResolution(param)
        # else:
        #     raise ValueError(f'DTR only accepts arguments of type {DynAction}')


class DV:
    @classmethod
    def __class_getitem__(cls, param: Callable[[T], U]):  # type: ignore
        def DynamicFactory(ser: Serializable[T]) -> DynamicValue[T, U]:
            return DynamicValue(ser, param)  # type: ignore

        return SerializableFactory(DynamicFactory)


class StructBase(ABC):
    @classmethod
    @abstractmethod
    def unpack_sized(cls, bytes_array: bytes) -> tuple[StructBase, int]:
        pass

    @classmethod
    @abstractmethod
    def unpack(cls, bytes_array: bytes) -> StructBase:
        pass


S = TypeVar("S", bound="Struct")


TagBaseType = Union[
    str, SerializableFactory[Any], DynamicTypeResolution, Type[StructBase]
]
BaseType = Union[Serializable[Any], DynamicTypeResolution, Type[StructBase]]

def is_tag(t: type) -> bool:
    tag_t = type(struc.Tag[int, ...])
    return t is tag_t

class Struct(StructBase):
    @staticmethod
    def find_type_and_args(
        tags: list[Any],
    ) -> Generator[tuple[TagBaseType, list[Any]], None, None]:
        # example
        # array of 5 i32 little-endian
        # 5,     '[]', LittleEndian, 'i32'
        #             |_____1.args_____1_|
        # 2.args  2   |_____2.ser________|

        def is_base(tag: Any) -> bool:
            if not isinstance(tag, type):
                return (
                    isinstance(tag, str)
                    or isinstance(tag, DynamicTypeResolution)
                    or isinstance(tag, SerializableFactory)
                )
            else:
                return issubclass(tag, Struct)

        def validate_base(tag: Any):
            if not is_base(tag):
                raise ValueError(f"Tag must end with a generic type. But got {tags[0]}")

        tags.reverse()
        validate_base(tags[0])

        while tags:
            typ_name = tags[0]
            typ_args: list[Any] = []
            for i, tag in enumerate(tags[1:], 1):
                if is_base(tag):
                    tags = tags[i:]  # advance tags
                    break
                typ_args.append(tag)
            else:
                yield (typ_name, typ_args)
                break  # tags end is reached, stop generator
            yield (typ_name, typ_args)

    @staticmethod
    def type_from_tags(tags: list[Any]) -> BaseType:
        def make_type(type_name: TagBaseType, *type_args: Any) -> BaseType:
            if isinstance(type_name, DynamicTypeResolution):
                type_name.set_args(*type_args)
                return type_name
            elif isinstance(type_name, str):
                type_ = TypeRegister.get_type(type_name)
                if type_ is None:
                    raise ValueError(
                        f"Undefined type {type_name}. If you defined type, don't forget to @register_type"
                    )
                return type_(*type_args)
            elif isinstance(type_name, SerializableFactory):
                return type_name(*type_args)
            elif issubclass(type_name, StructBase):  # type: ignore
                return type_name


        typ_data_parser = Struct.find_type_and_args(tags)
        # unfold following loop for a iteration
        type_name, type_args = next(typ_data_parser)

        ser = make_type(type_name, *type_args)

        for type_name, type_args in typ_data_parser:
            ser = make_type(type_name, ser, *type_args)
        return ser

    @classmethod
    def _get_fields(cls) -> list[tuple[str, BaseType]]:
        annotations: list[tuple[str, BaseType]] = []
        for var, ann in get_type_hints(cls, include_extras=True).items():
            tags = list(ann.__metadata__)
            typ = Struct.type_from_tags(tags)
            annotations.append((var, typ))
        return annotations

    def dynamic_extract(
        self, typ: DynamicTypeResolution, bytes_array: bytes
    ) -> tuple[Any, int]:
        tags = typ(self)
        return self.extract(Struct.type_from_tags(tags), bytes_array)

    def extract(self, typ: BaseType, bytes_array: bytes) -> tuple[Any, int]:
        if isinstance(typ, DynamicTypeResolution):
            return self.dynamic_extract(typ, bytes_array)
        elif isinstance(typ, Serializable):
            return typ._from_bytes(bytes_array)
        elif issubclass(typ, StructBase):  # type: ignore
            return typ.unpack_sized(bytes_array)

    @classmethod
    def unpack_sized(cls: Type[S], bytes_array: bytes) -> tuple[S, int]:
        s = cls()
        fields = s._get_fields()
        sum_processed = 0
        for var, typ in fields:
            val, processed_len = s.extract(typ, bytes_array)
            setattr(s, var, val)
            bytes_array = bytes_array[processed_len:]
            sum_processed += processed_len
        return s, sum_processed

    @classmethod
    def unpack(cls: Type[S], bytes_array: bytes) -> S:
        return cls.unpack_sized(bytes_array)[0]
