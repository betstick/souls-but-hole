import struct
import mathutils
from mathutils import Vector

def ReadInt(S):
	return struct.unpack("i", S.read(4))[0]

def ReadInt2(S):
	x = ReadInt(S)
	y = ReadInt(S)
	return (x,y)

def ReadInt4(S):
	x = ReadInt(S)
	y = ReadInt(S)
	z = ReadInt(S)
	w = ReadInt(S)
	return (x,y,z,w)

def ReadFloat(S):
	return struct.unpack("f", S.read(4))[0]

def ReadFloat2(S):
	x = ReadFloat(S)
	y = ReadFloat(S)
	return mathutils.Vector((x, y))

def ReadFloat3(S):
	x = ReadFloat(S)
	y = ReadFloat(S)
	z = ReadFloat(S)
	return mathutils.Vector((x, y, z))

def ReadFloat4(S):
	x = ReadFloat(S)
	y = ReadFloat(S)
	z = ReadFloat(S)
	w = ReadFloat(S)
	return mathutils.Vector((x,y,z,w))

def ReadBool(S):
	return struct.unpack("?", S.read(1))[0]

def ReadString(S):
	Length = ReadInt(S)

	return S.read(Length).decode("utf-8")

def ReadArray(S, DeserializeElementFunc):
	Arr = []
	ArrCount = ReadInt(S)

	for i in range(ArrCount):
		Arr.append(DeserializeElementFunc(S))

	return Arr
