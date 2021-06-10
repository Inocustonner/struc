# from __future__ import annotations

import sys
from typing import Any

sys.path.insert(0, "../struc")

from struc import Struct, Tag, LittleEndian, DTR, DV


def test_pair():
    class Blank(Struct):
        x: Tag[int, "u8"]
        y: Tag[int, "u16"]

    inp = b"\x0A\xF0\x0A"
    p = Blank.unpack(inp)
    assert p.x == 0xA
    assert p.y == 0xF00A


def test_endian_pair():
    class Blank(Struct):
        x: Tag[int, "u8"]
        y: Tag[int, LittleEndian, "u16"]

    inp = b"\x0A\x0A\xF0"
    p = Blank.unpack(inp)
    assert p.x == 0xA
    assert p.y == 0xF00A


def test_sized_array():
    arr_t = "[]"

    class Blank(Struct):
        x: Tag[int, "u8"]
        arr: Tag[list[bytes], 2, arr_t, "char"]

    inp = b"\x0A\x31\x32"
    p = Blank.unpack(inp)
    assert p.x == 0x0A
    assert p.arr == [b"\x31", b"\x32"]


def test_sized_array2():
    arr_t = "[]"

    class Blank(Struct):
        x: Tag[int, LittleEndian, "u16"]
        arr: Tag[list[bytes], 3, arr_t, "char"]

    inp = b"\x0A\xFF232"
    p = Blank.unpack(inp)
    assert p.x == 0xFF0A
    assert p.arr == [b"2", b"3", b"2"]


def test_cstring_unsized():
    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[bytes, "cstring"]
        y: Tag[int, "u16"]

    inp = b"\x0B232\x00\xFA\xAF"
    p = Blank.unpack(inp)
    assert p.x == 0x0B
    assert p.string == b"232"
    assert p.y == 0xFAAF


def test_cstring_sized():
    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[bytes, 3, "cstring"]
        y: Tag[int, LittleEndian, "u16"]

    inp = b"\x0B232\xFA\xAF"
    p = Blank.unpack(inp)
    assert p.x == 0x0B
    assert p.string == b"232"
    assert p.y == 0xAFFA


def test_array_of_shorts():
    arr_t = "[]"

    class Blank(Struct):
        x: Tag[int, "u8"]
        string: Tag[list[int], 3, arr_t, LittleEndian, "u16"]
        y: Tag[int, "u16"]

    inp = b"\x0C\x30\x31\x32\x33\x34\x35\xAF\xFA"
    p = Blank.unpack(inp)
    assert p.x == 0x0C
    assert p.string == [0x3130, 0x3332, 0x3534]
    assert p.y == 0xAFFA


def test_inheritance():
    class A(Struct):
        z: Tag[bytes, "cstring"]
        x: Tag[int, "u8"]

    class B(A):
        y: Tag[int, "u16"]

    inp = b"123\x00\x0A\xBB\xCC"
    p = B.unpack(inp)
    assert p.z == b"123"
    assert p.x == 0xA
    assert p.y == 0xBBCC


def test_dtr():
    class A(Struct):
        def cstring_from_size(self) -> list[Any]:
            return [self.size, "cstring"]

        size: Tag[int, "u8"]
        arr: Tag[bytes, DTR[cstring_from_size]]

    inp = b"\x03123"
    p = A.unpack(inp)
    assert p.size == 3
    assert p.arr == b"123"

    inp = b"\x041234"
    p = A.unpack(inp)
    assert p.size == 4
    assert p.arr == b"1234"

    class B(Struct):
        def tags_from_size(self) -> list[Any]:
            return [f"u{self.size}"]

        size: Tag[int, "u8"]
        tags: Tag[int, DTR[tags_from_size]]

    inp = b"\x08\x0A"
    p = B.unpack(inp)
    assert p.size == 0x08
    assert p.tags == 0x0A

    inp = b"\x10\x0A\x0B"
    p = B.unpack(inp)
    assert p.size == 0x10
    assert p.tags == 0x0A0B

def test_sub_struct():
    class A(Struct):
        x: Tag[int, LittleEndian, 'u16']

    class B(Struct):
        def y_sized_array_from_a_x(self) -> list[Any]:
            return [self.a.x, '[]', LittleEndian, 'u16']

        x1: Tag[int, 'u16']
        a: Tag[A, A]
        y: Tag[list[int], DTR[y_sized_array_from_a_x]]

    inp = b'\xB0\xBA' # B.x1
    inp += b'\x03\x00' # B.a.x
    inp += b'\x01\x00\x02\x00\x03\x00'# B.y

    p = B.unpack(inp)

    assert p.x1 == 0xB0BA
    assert p.a.x == 0x0003
    assert p.y == [0x0001, 0x0002, 0x0003]

def test_dynamic_value():
    def add(x: int) -> int:
        return x + 1
    class A(Struct):
        x: Tag[int, DV[add], 'u8']
    inp = b'\x03'
    p = A.unpack(inp)

    assert p.x == 4