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

T = TypeVar("T")


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


OutT = TypeVar("OutT")


@serialized_dynamic
class DynamicValue(SerializedFactory[OutT], Generic[RetT, OutT]):
    _ser: SerializedDecoder[RetT]
    _f: Callable[[RetT], OutT]

    def __init__(self, f: Callable[[RetT], OutT]):
        self._f = f

    def _unpack(self, stream: Reader, instance: Any) -> tuple[OutT, int]:
        res, read = self._ser._unpack(stream, instance)
        return self._f(res), read

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> tuple[OutT, int]:
        res, read = await self._ser._unpack_async(stream, instance)
        return self._f(res), read

    def _compose(self, ser: SerializedDecoder[RetT]) -> None:
        self._ser = ser


InstT = TypeVar("InstT")

SerF_RetT = TypeVar("SerF_RetT", list[Any], Serialized[Any], None)


@serialized_dynamic
class DynamicTypeResolution(SerializedFactory[Any], Generic[InstT, SerF_RetT, RetT]):
    _f: Callable[[InstT], SerF_RetT]
    _composition_ser: Optional[SerializedDecoder[RetT]] = None

    def __init__(self, f: Callable[[InstT], SerF_RetT]):
        self._f = f
        self._check_signature(f)

    def _check_signature(self, f: Callable[..., Any]):
        sign = inspect.signature(f)
        ret = sign.return_annotation
        if isinstance(ret, type(Union[Any, str])):
            for arg in ret.__args__:
                assert self._is_supported_return(
                    arg
                ), f"{arg} is not supported type for DTR"
        elif ret is not Any and ret is not inspect._empty:
            assert self._is_supported_return(ret), f"Is not supported return {ret}"
        else:
            raise ValueError("DTR function must have return signature")

    def _is_supported_return(self, t: Any) -> bool:
        # return t == GenericAlias(list, Any) or self._is_Serialized(t)
        return t is type(None) or get_origin(t) is list or get_origin(t) is Serialized or self._is_Serialized(t)

    def _is_Serialized(self, t: type):
        return issubclass(t, SerializedDecoder) and issubclass(t, SerializedCompositor)

    def _get_serialized(self, instance: InstT) -> Optional[Serialized[Any]]:
        r = self._f(instance)
        if type(r) is list:
            return TagType.parse_tags(tuple(cast(list[Any], self._f(instance)))).ser
        # isinstance checks take alot of time
        # and i will to rely on type checking of input function, that must have type annotations
        return cast(Optional[Serialized[Any]], r)
        # elif isinstance(r, SerializedDecoder) and isinstance(r, SerializedCompositor):
        #     return cast(Serialized[Any], r)
        # else:
        #     raise ValueError("Unexpected type from dynamic resolution")

    def _unpack(self, stream: Reader, instance: InstT) -> tuple[Any, int]:
        ser = self._get_serialized(instance)
        if ser is None:
            return None, 0
        if self._composition_ser is not None:
            ser._compose(self._composition_ser)
        return ser._unpack(stream, instance)

    async def _unpack_async(self, stream: AsyncReader, instance: Any) -> tuple[Any, int]:
        ser = self._get_serialized(instance)
        if ser is None:
            return None, 0
        if self._composition_ser is not None:
            ser._compose(self._composition_ser)
        return await ser._unpack_async(stream, instance)

    def _compose(self, ser: SerializedDecoder[RetT]) -> None:
        self._composition_ser = ser
