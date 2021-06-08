import sys
sys.path.insert(0, '../struc')

from struc import Struct, Tag, LittleEndian

def test_pair():
    class Blank(Struct):
        x: Tag[int, 'u8']
        y: Tag[int, 'u16']
    inp = b'\x0A\xF0\x0A'
    p = Blank.unpack(inp)
    assert p.x == 0xA
    assert p.y == 0xF00A

def test_endian_pair():
    class Blank(Struct):
        x: Tag[int, 'u8']
        y: Tag[int, LittleEndian, 'u16']
    inp = b'\x0A\x0A\xF0'
    p = Blank.unpack(inp)
    assert p.x == 0xA
    assert p.y == 0xF00A

def test_sized_array():
    arr_t = '[]'
    class Blank(Struct):
        x: Tag[int, 'u8']
        arr: Tag[list[bytes], 2, arr_t, 'char']
    inp = b'\x0A\x31\x32'
    p = Blank.unpack(inp)
    assert p.x == 0x0A
    assert p.arr == [b'\x31', b'\x32']

def test_sized_array2():
    arr_t = '[]'
    class Blank(Struct):
        x: Tag[int, LittleEndian, 'u16']
        arr: Tag[list[bytes], 3, arr_t, 'char']
    inp = b'\x0A\xFF232'
    p = Blank.unpack(inp)
    assert p.x == 0xFF0A
    assert p.arr == [b'2', b'3', b'2']

def test_cstring_unsized():
    class Blank(Struct):
        x: Tag[int, 'u8']
        string: Tag[bytes, 'cstring']
        y: Tag[int, 'u16']
    inp = b'\x0B232\x00\xFA\xAF'
    p = Blank.unpack(inp)
    assert p.x == 0x0B
    assert p.string == b'232'
    assert p.y == 0xFAAF

def test_cstring_sized():
    class Blank(Struct):
        x: Tag[int, 'u8']
        string: Tag[bytes, 3, 'cstring']
        y: Tag[int, LittleEndian, 'u16']
    inp = b'\x0B232\xFA\xAF'
    p = Blank.unpack(inp)
    assert p.x == 0x0B
    assert p.string == b'232'
    assert p.y == 0xAFFA

def test_array_of_shorts():
    arr_t = '[]'
    class Blank(Struct):
        x: Tag[int, 'u8']
        string: Tag[list[int], 3, arr_t, LittleEndian, 'u16']
        y: Tag[int, 'u16']
    inp = b'\x0C\x30\x31\x32\x33\x34\x35\xAF\xFA'
    p = Blank.unpack(inp)
    assert p.x == 0x0C
    assert p.string == [0x3130, 0x3332, 0x3534]
    assert p.y == 0xAFFA