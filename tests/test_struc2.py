from typing import Any, Optional
from struc2 import Struct, Tag, LittleEndian, DV, DTR
from struc2.Serialized import Serialized
from struc2.SerializedImpl import u16
import aiofiles.tempfile
import asyncio
import pytest

def test_pair():
    class Blank(Struct):
        x: Tag[int, "u8"]
        y: Tag[int, u16]

    inp = b"\x0A\xF0\x0A"
    p = Blank.unpack_b(inp)
    assert p.x == 0xA
    assert p.y == 0xF00A

def test_endian_pair():
    class Blank(Struct):
        x: Tag[int, "u8"]
        y: Tag[int, LittleEndian, "u16"]

    inp = b"\x0A\x0A\xF0"
    p = Blank.unpack_b(inp)
    assert p.x == 0xA
    assert p.y == 0xF00A


def test_sized_array():
    arr_t = "[]"

    class Blank(Struct):
        x: Tag[int, "u8"]
        arr: Tag[list[bytes], 2, arr_t, "char"]

    inp = b"\x0A\x31\x32"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0A
    assert p.arr == [b"\x31", b"\x32"]


def test_sized_array2():
    arr_t = "[]"

    class Blank(Struct):
        x: Tag[int, LittleEndian, "u16"]
        arr: Tag[list[bytes], 3, arr_t, "char"]

    inp = b"\x0A\xFF232"
    p = Blank.unpack_b(inp)
    assert p.x == 0xFF0A
    assert p.arr == [b"2", b"3", b"2"]

def test_predicate_array():
    class Blank(Struct):
        def _pred(self, read: int):
            return self.x > read

        x: Tag[int, LittleEndian, "u16"]
        arr: Tag[list[bytes], _pred, "predicate_array", "char"]

    inp = b"\x03\x00232"
    p = Blank.unpack_b(inp)
    assert p.x == 3
    assert p.arr == [b"2", b"3", b"2"]

def test_cstring_unsized():
    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[bytes, "cstring"]
        y: Tag[float, LittleEndian, "f64"]

    inp = b"\x0B\x70\x77\x72\x5F\x65\x78\x74\x00\x2B\x87\x16\xD9\xCE\x97\x3B\x40"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0B
    assert p.string == b"pwr_ext"
    assert p.y == 27.593

def test_cstring_sized():
    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[bytes, 3, "cstring"]
        string2: Tag[bytes, "cstring"]
        y: Tag[int, LittleEndian, "u16"]

    inp = b"\x0B232123\x00\xFA\xAF"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0B
    assert p.string == b"232"
    assert p.string2 == b"123"
    assert p.y == 0xAFFA
    inp = b"\x0B23212345\x00\xFA\xAF"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0B
    assert p.string == b"232"
    assert p.string2 == b"12345"
    assert p.y == 0xAFFA

def test_cstring_zero_size():
    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[bytes, 0, "cstring"]
        y: Tag[int, LittleEndian, "u16"]

    inp = b"\x0B\xFA\xAF"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0B
    assert p.string == b""
    assert p.y == 0xAFFA

def test_array_of_shorts():
    arr_t = "[]"

    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[list[int], 3, arr_t, LittleEndian, "u16"]
        y: Tag[int, "u16"]

    inp = b"\x0C\x30\x31\x32\x33\x34\x35\xAF\xFA"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0C
    assert p.string == [0x3130, 0x3332, 0x3534]
    assert p.y == 0xAFFA

def test_array_of_size_0():
    arr_t = "[]"

    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[list[int], 0, arr_t, LittleEndian, "u16"]
        y: Tag[int, "u16"]

    inp = b"\x0C\xAF\xFA"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0C
    assert p.y == 0xAFFA

def test_array_with_struct_type():
    arr_t = "[]"

    class A(Struct):
        x: Tag[int, 'u16']

    class Blank(Struct):
        x: Tag[int, "u8"]
        a: Tag[list[A], 2, arr_t, A]
        y: Tag[int, "u16"]

    inp = b"\x0C\x00\xFF\xFF\x00\xAF\xFA"
    p = Blank.unpack_b(inp)
    assert p.x == 0x0C
    assert p.a[0].x == 0x00FF
    assert p.a[1].x == 0xFF00
    assert p.y == 0xAFFA

def test_inheritance():
    class A(Struct):
        z: Tag[bytes, "cstring"]
        x: Tag[int, "u8"]

    class B(A):
        y: Tag[int, "u16"]

    inp = b"123\x00\x0A\xBB\xCC"
    p = B.unpack_b(inp)
    assert p.z == b"123"
    assert p.x == 0xA
    assert p.y == 0xBBCC

def test_dynamic_value():
    class A(Struct):
        a: Tag[int, 'u8']
        x: Tag[int, DV[lambda x: x + 1], "u8"] # type: ignore
        y: Tag[int, 'u8']

    inp = b"\x05\x03\x04"
    p = A.unpack_b(inp)

    assert p.a == 5
    assert p.x == 4
    assert p.y == 4

def test_ignore_non_tagged():
    class A(Struct):
        x: Tag[int, "u16"]
        y: int
        z: Tag[bytes, 'cstring']
        a: Tag[int, "u8"]

    inp = b'\xAB\xBA123\0\xAA'
    p = A.unpack_b(inp)
    assert p.x == 0xABBA
    assert p.z == b'123'
    assert p.a == 0xAA

def test_dtr():
    class A(Struct):
        def cstring_from_size(self) -> list[Any]:
            return [self.size, "cstring"]

        size: Tag[int, "u8"]
        arr: Tag[bytes, DTR[cstring_from_size]]

    inp = b"\x03123"
    p = A.unpack_b(inp)
    assert p.size == 3
    assert p.arr == b"123"

    inp = b"\x041234"
    p = A.unpack_b(inp)
    assert p.size == 4
    assert p.arr == b"1234"

    class B(Struct):
        def tags_from_size(self) -> list[Any]:
            return [f"u{self.size}"]

        size: Tag[int, "u8"]
        tags: Tag[int, DTR[tags_from_size]]

    inp = b"\x08\x0A"
    p = B.unpack_b(inp)
    assert p.size == 0x08
    assert p.tags == 0x0A

    inp = b"\x10\x0A\x0B"
    p = B.unpack_b(inp)
    assert p.size == 0x10
    assert p.tags == 0x0A0B

def test_dtr_optional():
    class A(Struct):
        def opt_cstring_from_size(self) -> Optional[Serialized[Any]]:
            return None
        def cstring_from_size(self) -> list[Any]:
            return [self.size, 'cstring']

        size: Tag[int, "u8"]
        opt: Tag[Optional[bytes], DTR[opt_cstring_from_size]]
        arr: Tag[bytes, DTR[cstring_from_size]]

    inp = b"\x03123"
    p = A.unpack_b(inp)
    assert p.size == 3
    assert p.opt is None
    assert p.arr == b'123'

def test_dtr_invalid_function_no_return_annotation():
    with pytest.raises(ValueError):
        class A(Struct):
            def cstring_from_size(self):
                return [self.size, "cstring"]

            size: Tag[int, "u8"]
            arr: Tag[bytes, DTR[cstring_from_size]]

        inp = b"\x03123"
        p = A.unpack_b(inp)
        assert p.size == 3
        assert p.arr == b"123"

def test_dtr_invalid_function_return_annotatnion():
    with pytest.raises(AssertionError):
        class A(Struct):
            def cstring_from_size(self) -> str:
                return "cstring"

            size: Tag[int, "u8"]
            arr: Tag[bytes, DTR[cstring_from_size]]

        inp = b"\x03123"
        p = A.unpack_b(inp)
        assert p.size == 3
        assert p.arr == b"123"


def test_dtr_and_strings_and_dv():
    def from_type_dtr(d: 'DataBlock') -> list[Any]:
        return [LittleEndian, 'f64']

    class DataBlock(Struct):
        const: Tag[int, 'u16']
        size: Tag[int, 'i32']
        stealth_attr: Tag[int, 'i8']
        type: Tag[int, 'i8']
        name: Tag[bytes, 'cstring']
        value: Tag[Any, DV[lambda v: v / 10], DTR[from_type_dtr]]

    inp = b'\x0b\xbb\x00\x00\x00\x12\x00\x04pwr_ext\x00+\x87\x16\xd9\xce\x97;@\x0b\xbb\x00\x00\x00\x11\x01\x03avl_inputs\x00\x00\x00\x00\x01'
    p = DataBlock.unpack_b(inp)
    p = DataBlock.unpack_b(inp)
    assert p.value == 27.593 / 10

def test_dtr_and_strings_and_dv_async():
    def from_type_dtr(d: 'DataBlock') -> list[Any]:
        return [LittleEndian, 'f64']

    class DataBlock(Struct):
        const: Tag[int, 'u16']
        size: Tag[int, 'i32']
        stealth_attr: Tag[int, 'i8']
        type: Tag[int, 'i8']
        name: Tag[bytes, 'cstring']
        value: Tag[Any, DV[lambda v: v / 10], DTR[from_type_dtr]]

    async def main():
        async with aiofiles.tempfile.TemporaryFile() as f: # type: ignore
            inp = b'\x0b\xbb\x00\x00\x00\x12\x00\x04pwr_ext\x00+\x87\x16\xd9\xce\x97;@\x0b\xbb\x00\x00\x00\x11\x01\x03avl_inputs\x00\x00\x00\x00\x01'
            await f.write(inp) # type: ignore
            await f.seek(0) # type: ignore
            p = await DataBlock.unpack_async(f) # type: ignore
            assert p.value == 27.593 / 10 # type: ignore
    asyncio.run(main())

def test_benchmark_normal(benchmark: Any):
    class A(Struct):
        x: Tag[int, "u16"]
        y: Tag[int, "u16"]
        z: Tag[bytes, 'cstring']
        a: Tag[int, "u8"]

    inp = b'\xAB\xBA\xAB\xBA123\0\xAA'
    benchmark.pedantic(A.unpack_b, args=(inp,), iterations=4, rounds=1000)

def test_benchmark_dv(benchmark: Any):
    class A(Struct):
        x: Tag[int, "u16"]
        y: Tag[int, DV[lambda v: v // 10], "u16"]
        z: Tag[bytes, 'cstring']
        a: Tag[int, "u8"]

    inp = b'\xAB\xBA\xAB\xBA123\0\xAA'
    benchmark.pedantic(A.unpack_b, args=(inp,), iterations=4, rounds=1000)

def test_benchmark_dtr(benchmark: Any):
    def from_type_dtr(d: 'A') -> list[str]:
        return ['u16']

    class A(Struct):
        x: Tag[int, "u16"]
        y: Tag[int, DTR[from_type_dtr]]
        z: Tag[bytes, 'cstring']
        a: Tag[int, "u8"]

    inp = b'\xAB\xBA\xAB\xBA123\0\xAA'
    benchmark.pedantic(A.unpack_b, args=(inp,), iterations=4, rounds=1000)

def test_benchmark_dv_dtr(benchmark: Any):
    def from_type_dtr(d: 'A') -> u16:
        return u16()

    class A(Struct):
        x: Tag[int, "u16"]
        y: Tag[int, DV[lambda v: v // 10], DTR[from_type_dtr]]
        z: Tag[bytes, 'cstring']
        a: Tag[int, "u8"]

    inp = b'\xAB\xBA\xAB\xBA123\0\xAA'
    benchmark.pedantic(A.unpack_b, args=(inp,), iterations=4, rounds=1000)