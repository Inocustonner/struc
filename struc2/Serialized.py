from asyncio import StreamReader as AsyncReader
from io import IOBase as Reader
from typing import Any, Generic, Protocol, TypeVar, cast, runtime_checkable

RetT = TypeVar("RetT", covariant=True)

@runtime_checkable
class SerializedDecoder(Protocol, Generic[RetT]):
    def _unpack(self, stream: Reader, instance: Any) -> tuple[RetT, int]: ...

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> tuple[RetT, int]: ...


InT = TypeVar("InT", contravariant=True) # python requires
@runtime_checkable
class SerializedCompositor(Protocol, Generic[InT]):
    def _compose(self, ser: SerializedDecoder[InT]) -> None: ...


class Serialized(
    SerializedDecoder[RetT], SerializedCompositor[RetT], Generic[RetT]
): ...

class SerializedFactory(Generic[RetT]):
    @classmethod
    def create(cls: type[Any], *args: Any, **kwargs: Any) -> Serialized[RetT]:
        return cast(Serialized[RetT], cls(*args, **kwargs))