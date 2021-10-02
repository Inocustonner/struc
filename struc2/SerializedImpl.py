import struct
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional, TypeVar

from .defs import Endian
from .Serialized import AsyncReader, Generic, Reader, SerializedFactory, SerializedDecoder
from .Registry import register_type

# if TYPE_CHECKING:
from .Serialized import RetT


# class SerializedFactory(Generic["RetT"]):
#     @classmethod
#     def create(cls, *args: Any, **kwargs: Any) -> Serialized["RetT"]:
#         return cls(*args, **kwargs)  # type: ignore


class SerializedSimple(SerializedFactory["RetT"], Generic[RetT]):
    struct_type: str
    struct_type_size: int
    _endian: Endian

    def __init__(self, endian: Endian = Endian.Big):
        self._endian = endian

    def _unpack(self, stream: Reader, instance: Any) -> tuple[RetT, int]:
        return struct.unpack(
            f"{self._endian.value}{self.struct_type}", stream.read(self.struct_type_size)
        )[0], self.struct_type_size

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> tuple[RetT, int]:
        return struct.unpack(
            f"{self._endian.value}{self.struct_type}",
            await stream.read(self.struct_type_size),
        )[0], self.struct_type_size

    def _compose(self, ser: SerializedDecoder[Any]) -> None:
        pass

@register_type
class SerializedString(SerializedFactory[bytes]):
    _name = "cstring"

    _length: Optional[int]
    _eof_char: Annotated[bytes, "must be 1 character"] = b"\0"

    def __init__(self, length: Optional[int] = None):
        self._length = length

    def _unpack(self, stream: Reader, instance: Any) -> tuple[bytes, int]:
        if self._length is not None:
            return stream.read(self._length), self._length
        s = b""
        while (ch := stream.read(1)) != self._eof_char:
            s += ch
        return s, len(s) + 1

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> tuple[bytes, int]:
        if self._length is not None:
            return await stream.read(self._length), self._length
        s = b""
        while (ch := await stream.read(1)) != self._eof_char:
            s += ch
        return s, len(s) + 1

    def _compose(self, ser: SerializedDecoder[Any]) -> None:
        pass

@register_type
class SerializedArray(SerializedFactory[list[RetT]], Generic[RetT]):
    _name = "[]"

    _length: int
    _ser: SerializedDecoder[RetT]

    def __init__(self, length: int):
        self._length = length

    def _unpack(self, stream: Reader, instance: Any) -> tuple[list[RetT], int]:
        r = list["RetT"]()
        size: int = 0
        for _ in range(self._length):
            res, read = self._ser._unpack(stream, instance)
            r.append(res)
            size += read
        return r, size

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> tuple[list[RetT], int]:
        r = list["RetT"]()
        size: int = 0
        for _ in range(self._length):
            res, read = await self._ser._unpack_async(stream, instance)
            r.append(res)
            size += read
        return r, size

    def _compose(self, ser: SerializedDecoder[RetT]) -> None:
        self._ser = ser

InstT = TypeVar('InstT')
_Pred = Callable[[InstT, int], bool]
@register_type
class SerializedArrayWithPredicate(SerializedFactory[list[RetT]], Generic[RetT, InstT]):
    _name = "predicate_array"

    _predicate: _Pred[InstT]
    _ser: SerializedDecoder[RetT]

    def __init__(self, predicate: _Pred[InstT]):
        self._predicate = predicate

    def _unpack(self, stream: Reader, instance: InstT) -> tuple[list[RetT], int]:
        r = list["RetT"]()
        size: int = 0
        while self._predicate(instance, size):
            res, read = self._ser._unpack(stream, instance)
            r.append(res)
            size += read
        return r, size

    async def _unpack_async(self, stream: AsyncReader, instance: InstT) -> tuple[list[RetT], int]:
        r = list["RetT"]()
        size: int = 0
        while self._predicate(instance, size):
            res, read = await self._ser._unpack_async(stream, instance)
            r.append(res)
            size += read
        return r, size

    def _compose(self, ser: SerializedDecoder[RetT]) -> None:
        self._ser = ser

@register_type
class char(SerializedSimple[bytes]):
    struct_type_size = 1
    struct_type = "c"


@register_type
class i8(SerializedSimple[int]):
    struct_type_size = 1
    struct_type = "b"


@register_type
class u8(SerializedSimple[int]):
    struct_type_size = 1
    struct_type = "B"


@register_type
class i16(SerializedSimple[int]):
    struct_type_size = 2
    struct_type = "h"


@register_type
class u16(SerializedSimple[int]):
    struct_type_size = 2
    struct_type = "H"


@register_type
class i32(SerializedSimple[int]):
    struct_type_size = 4
    struct_type = "i"


@register_type
class u32(SerializedSimple[int]):
    struct_type_size = 4
    struct_type = "I"


@register_type
class i64(SerializedSimple[int]):
    struct_type_size = 8
    struct_type = "q"


@register_type
class u64(SerializedSimple[int]):
    struct_type_size = 8
    struct_type = "Q"


@register_type
class f32(SerializedSimple[float]):
    struct_type_size = 4
    struct_type = "f"


@register_type
class f64(SerializedSimple[float]):
    struct_type_size = 8
    struct_type = "d"
