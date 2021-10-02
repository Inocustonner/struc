from typing import Any, Callable, Generic, Optional, TypeVar, Union, cast, get_origin
from types import GenericAlias
from .Serialized import (
    RetT,
    SerializedCompositor,
    SerializedDecoder,
    SerializedFactory,
    Reader,
    AsyncReader,
    Serialized,
)
import inspect
from .TagParser import TagType
T = TypeVar('T')

def serialized_dynamic(cls_: type):
    class DynamicSerialized:
        @classmethod
        def __class_getitem__(cls, params: Callable[[Any], Any]):
            class DynamicSerializedFactory(SerializedFactory[RetT], Generic[RetT]):
                @classmethod
                def create(cls: type, *args: Any, **kwargs: Any) -> Serialized[RetT]:
                    return cls_(params)
            return type(DynamicSerializedFactory[Any]())
    return DynamicSerialized

OutT = TypeVar('OutT')
@serialized_dynamic
class DynamicValue(SerializedFactory[OutT], Generic[RetT, OutT]):
    _ser: SerializedDecoder[RetT]
    _f: Callable[[RetT], OutT]

    def __init__(self, f: Callable[[RetT], OutT]):
        self._f = f

    def _unpack(self, stream: Reader, instance: Any) -> OutT:
        return self._f(self._ser._unpack(stream, instance))

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> OutT:
        return self._f(await self._ser._unpack_async(stream, instance))

    def _compose(self, ser: SerializedDecoder[RetT]) -> None:
        self._ser = ser

InstT = TypeVar('InstT')

SerF_RetT = TypeVar('SerF_RetT', list[Any], Serialized[Any])

@serialized_dynamic
class DynamicTypeResolution(SerializedFactory[Any], Generic[InstT, SerF_RetT, RetT]):
    _f: Callable[[InstT], list[SerF_RetT]]
    _ser: Optional[SerializedDecoder[RetT]] = None

    def __init__(self, f: Callable[[InstT], list[Any]]):
        self._f = f
        self._check_signature(f)

    def _check_signature(self, f: Callable[..., Any]):
        sign = inspect.signature(f)
        ret = sign.return_annotation
        if ret is not Any and ret is not inspect._empty:
            assert self._is_supported_return(ret), f"Is not supported return {ret}"
        elif isinstance(type(ret), type(Union[Any])):
            for arg in ret.__args__:
                assert self._is_supported_return(arg), f"{arg} is not supported type for DTR"
        else:
            raise ValueError("DTR function must have return signature")

    def _is_supported_return(self, t: Any) -> bool:
        # return t == GenericAlias(list, Any) or self._is_Serialized(t)
        return get_origin(t) is list or self._is_Serialized(t)

    def _is_Serialized(self, t: type):
        return issubclass(t, SerializedDecoder) and issubclass(t, SerializedCompositor)

    def _get_serialized(self, instance: InstT) -> Serialized[Any]:
        r = self._f(instance)
        if type(r) is list:
            return TagType.parse_tags(tuple(self._f(instance))).ser
        # isinstance checks take alot of time
        # and i will to rely on type checking of input function, that must have type annotations
        return cast(Serialized[Any], r)
        # elif isinstance(r, SerializedDecoder) and isinstance(r, SerializedCompositor):
        #     return cast(Serialized[Any], r)
        # else:
        #     raise ValueError("Unexpected type from dynamic resolution")

    def _unpack(self, stream: Reader, instance: InstT) -> Any:
        ser = self._get_serialized(instance)
        if self._ser is not None:
            ser._compose(self._ser)
        return ser._unpack(stream, instance)

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> Any:
        ser = self._get_serialized(instance)
        if self._ser is not None:
            ser._compose(self._ser)
        return await ser._unpack_async(stream, instance)

    def _compose(self, ser: SerializedDecoder[RetT]) -> None:
        self._ser = ser