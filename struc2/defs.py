from enum import Enum

class Endian(Enum):
    Little = '<'
    Big = '>'

LittleEndian: Endian = Endian.Little
BigEndian: Endian = Endian.Big