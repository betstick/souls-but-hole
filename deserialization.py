import struct
import mathutils
from mathutils import Vector

def ReadInt(S):
	return struct.unpack("i", S.read(4))[0]

def ReadInt2(S):
	return struct.unpack("ii", S.read(8))

def ReadInt3(S):
	return struct.unpack("iii", S.read(12))

def ReadInt4(S):
	return struct.unpack("iiii", S.read(16))

def ReadFloat(S):
	return struct.unpack("f", S.read(4))[0]

def ReadFloat2(S):
	return mathutils.Vector(struct.unpack("ff", S.read(8)))

def ReadFloat3(S):
	return mathutils.Vector(struct.unpack("fff", S.read(12)))

def ReadFloat4(S):
	return mathutils.Vector(struct.unpack("ffff", S.read(16)))

def ReadBool(S):
	return struct.unpack("?", S.read(1))[0]

def ReadString(S):
	return S.read(struct.unpack("i", S.read(4))[0]).decode("utf-8")

def ReadArray(S, DeserializeElementFunc):
	return [DeserializeElementFunc(S) for i in range(ReadInt(S))]