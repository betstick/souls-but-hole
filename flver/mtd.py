import bpy
import sys
import bmesh
import subprocess
import mathutils
import math
from mathutils import Vector
import time
import cProfile

from . import util

from ..tools.deserialization import *

class Mtd:
	def __init__(self, index, count, params):
		self.index = index
		self.paramCount = count
		self.params = params

	def print(self):
		print("MTD: " + str(self.index) + ", " + str(self.paramCount) + " params")

	def printParams(self):
		for param in self.params:
			param.print()

# Needs to be precisely matched to SoulsFormats enum
MTDParamTypeFuncs = [ReadBool, ReadInt, ReadInt2, ReadFloat, ReadFloat2, ReadFloat3, ReadFloat4]

class MtdParam:
	@staticmethod
	def Deserialize(p):
		self = MtdParam()
		self.name = ReadString(p)
		self.type = ReadInt(p)
		self.value = MTDParamTypeFuncs[self.type](p)
		return self

	def print(self):
		print(self.name + "," + self.type + "," + self.value)