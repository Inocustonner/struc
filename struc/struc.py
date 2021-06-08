from typing import Type, TypeVar, Generator, Any
from .Serializable import GenericSeril, ArraySeril, Serializable
from .register import TypeRegister, register_type
from .defs import *


@register_type
class char(GenericSeril[bytes]):
    data_len = 1
    struct_fmt = 'c'

@register_type
class i8(GenericSeril[int]):
    data_len = 1
    struct_fmt = 'b'

@register_type
class u8(GenericSeril[int]):
    data_len = 1
    struct_fmt = 'B'

@register_type
class i16(GenericSeril[int]):
    data_len = 2
    struct_fmt = 'h'

@register_type
class u16(GenericSeril[int]):
    data_len = 2
    struct_fmt = 'H'

@register_type
class i32(GenericSeril[int]):
    data_len = 4
    struct_fmt = 'i'

@register_type
class u32(GenericSeril[int]):
    data_len = 4
    struct_fmt = 'I'

@register_type
class i64(GenericSeril[int]):
    data_len = 8
    struct_fmt = 'q'

@register_type
class u64(GenericSeril[int]):
    data_len = 8
    struct_fmt = 'Q'

@register_type
class f32(GenericSeril[float]):
    data_len = 4
    struct_fmt = 'f'

@register_type
class f64(GenericSeril[float]):
    data_len = 8
    struct_fmt = 'd'

T = TypeVar('T')

@register_type
class _sized_array(ArraySeril[list[T], T]): # type: ignore
    _name = '[]'

    @staticmethod
    def transform(arr: list[T]) -> list[T]:
        return arr

@register_type
class cstring(ArraySeril[bytes, bytes]):
    length = 0
    stop_char = b'\0'
    def __init__(self, length: int = 0):
        if length < 0:
            raise ValueError(f'Length argument must be > 0, given {length}')
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


S = TypeVar('S', bound='Struct')

class Struct:
    @staticmethod
    def _find_type_and_args(tags: list[Any]) -> Generator[tuple[str, list[Any]], None, None]:
        # example
        # array of 5 i32 little-endian
        # 5,     '[]', LittleEndian, 'i32'
        #             |_____1.args_____1_|
        # 2.args  2   |_____2.ser________|
        tags.reverse()
        if not isinstance(tags[0], str):
            raise ValueError(f"Tag must end with a generic type. But got {tags[0]}")

        while tags:
            typ_name = tags[0]
            typ_args: list[Any] = []
            for i, tag in enumerate(tags[1:], 1):
                if isinstance(tag, str):
                    tags = tags[i:] # advance tags
                    break
                typ_args.append(tag)
            else:
                yield (typ_name, typ_args)
                break # tags end is reached, stop generator
            yield (typ_name, typ_args)

    @staticmethod
    def _type_from_tags(tags: list[Any]) -> Serializable[Any]:
        def pull_type_from_reg(type_name: str) -> Type[Serializable[Any]]:
            type_ = TypeRegister.get_type(type_name)
            if type_ is None:
                raise ValueError(f'Undefined type {type_name}. If you defined type, don\'t forget to @register_type')
            return type_

        typ_data_parser = Struct._find_type_and_args(tags)
        # unfold following loop for a iteration
        type_name, type_args = next(typ_data_parser)
        ser = pull_type_from_reg(type_name)(*type_args)

        for type_name, type_args in typ_data_parser:
            ser = pull_type_from_reg(type_name)(ser, *type_args)
        return ser

    @classmethod
    def _get_fields(cls) -> list[tuple[str, Serializable[Any]]]: 
        annotations: list[tuple[str, Serializable[Any]]] = []
        for var, ann in cls.__annotations__.items():
            tags = list(ann.__metadata__)
            annotations.append((var, Struct._type_from_tags(tags)))
        return annotations

    @classmethod
    # def unpack(cls: Type[S], bytes_array: bytes, endian: Endian = BigEndian) -> S:
    def unpack(cls: Type[S], bytes_array: bytes) -> S:
        fields = cls._get_fields()
        s = cls()
        for var, typ in fields:
            val, processed_len = typ._from_bytes(bytes_array)
            setattr(s, var, val)
            bytes_array = bytes_array[processed_len:]
        return s