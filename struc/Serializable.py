import struct
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from struc.defs import BigEndian, Endian

T = TypeVar('T')
U = TypeVar('U')

SSC = TypeVar('SSC', bound='_SimpleSerializable') # type: ignore

class Serializable(ABC, Generic[T]):
    _name: str
    _data: T
    def __init__(*args):
        pass
    # MUST work even if number of bytes more then needed
    @abstractmethod
    def _from_bytes(self, byte_array: bytes) -> tuple[T, int]:
        pass
    @abstractmethod
    def __bytes__(self) -> bytes:
        pass


class _SimpleSerializable(Serializable[T]):
    # data: T
    data_len: int # in bytes
    struct_fmt: str
    endian: str

    def __init__(self, endian: Endian = BigEndian):
        self.endian = endian.value

    def _from_bytes(self, byte_array: bytes) -> tuple[T, int]:
        self._data = struct.unpack(f'{self.endian}{self.struct_fmt}', byte_array[:self.data_len])[0]
        return self._data, self.data_len

    def __bytes__(self) -> bytes:
        return struct.pack(f'{self.endian}{self.struct_fmt}', self._data)

class _ModifierSerializable(Serializable[T], Generic[T, U]):
    ser: Serializable[U]
    def __init__(self, ser: Serializable[U]):
        self.ser = ser

class _ArraySerializable(_ModifierSerializable[U, T]):
    length: int # number of elements
    def __init__(self, ser: Serializable[T], length: int):
        self.length = length
        super().__init__(ser)
    
    def _from_bytes(self, byte_array: bytes) -> tuple[U, int]:
        data: list[T] = []
        processed_len = 0 # bytes processed
        for _ in range(self.length):
            # val_len may be dynamic
            val, val_len = self.ser._from_bytes(byte_array)
            byte_array = byte_array[val_len:]
            data.append(val)
            processed_len += val_len
        return type(self).transform(data), processed_len

    @staticmethod
    @abstractmethod
    def transform(arr: list[T]) -> U:
        pass

    def __bytes__(self) -> bytes: ...

GenericSeril = _SimpleSerializable
ArraySeril = _ArraySerializable