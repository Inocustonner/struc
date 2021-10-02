from typing import Any, TypeVar, cast

from struc2.TagParser import TagParser

from .Serialized import AsyncReader, Reader, SerializedDecoder, SerializedFactory
import io

StructT = TypeVar("StructT", bound='Struct')

class Struct(SerializedFactory['Struct'], TagParser):
    # i don't use `instance`, because instance is suppused to be deserializable struct in current state
    # for some meta information for dynamic type resolution 
    def _unpack(self: StructT, stream: Reader, instance: StructT) -> tuple[StructT, int]:
        this = type(self)()
        total_size = 0
        for var, t in self._get_tags():
            field, size = t._unpack(stream, this)
            setattr(this, var, field)
            total_size += size
        return this, total_size

    async def _unpack_async(self: StructT, stream: AsyncReader, instance: StructT) -> tuple[StructT, int]:
        this = type(self)()
        total_size = 0
        for var, t in iter(self._get_tags()):
            field, size = await t._unpack_async(stream, this)
            setattr(this, var, field)
            total_size += size
        return this, total_size

    def _compose(self, ser: SerializedDecoder[Any]) -> None: 
        raise NotImplementedError

    @classmethod
    def unpack(cls, stream: Reader):
        i = cls()
        return cast(cls, i._unpack(stream, i)[0])

    @classmethod
    def unpack_b(cls, bytes_array: bytes):
        with io.BytesIO(bytes_array) as stream:
            i = cls()
            return cast(cls, i._unpack(stream, i)[0])

    @classmethod
    async def unpack_async(cls, stream: AsyncReader):
        i = cls()
        return cast(cls, (await i._unpack_async(stream, i))[0])
