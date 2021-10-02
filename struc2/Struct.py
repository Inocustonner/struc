from typing import Any, TypeVar, cast

from struc2.TagParser import TagParser

from .Serialized import AsyncReader, Reader, SerializedDecoder, SerializedFactory
import io

StructT = TypeVar("StructT", bound='Struct')

class Struct(SerializedFactory['Struct'], TagParser):
    # i don't use `instance`, because instance is suppused to be deserializable struct in current state
    # for some meta information for dynamic type resolution 
    def _unpack(self: StructT, stream: Reader, instance: StructT) -> StructT:
        this = type(self)()
        for var, t in iter(self._get_tags()): # type: ignore
            setattr(this, var, t._unpack(stream, this))
        return this

    async def _unpack_async(self: StructT, stream: AsyncReader, instance: StructT) -> StructT:
        this = type(self)()
        for var, t in iter(self._get_tags()):
            setattr(this, var, await t._unpack_async(stream, this))
        return this

    def _compose(self, ser: SerializedDecoder[Any]) -> None: 
        raise NotImplementedError

    @classmethod
    def unpack(cls, stream: Reader):
        i = cls()
        return cast(type(cls), i._unpack(stream, i))

    @classmethod
    def unpack_b(cls, bytes_array: bytes):
        with io.BytesIO(bytes_array) as stream:
            i = cls()
            return cast(cls, i._unpack(stream, i))

    @classmethod
    async def unpack_async(cls, stream: AsyncReader):
        i = cls()
        return cast(cls, await i._unpack_async(stream, i))
