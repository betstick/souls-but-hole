import bpy
import sys
import bmesh
import subprocess
import mathutils
import math
from mathutils import Vector
import time
import cProfile

#parses stride length arrays and returns outer array
def parse_float_arr(line,stride):
	values = line.split("\t")
	values.pop() #remove last element, its blank
	arr = []

	size = len(values) / stride

	for v in range(int(size)):
		floats = []
		for s in range(stride):
			floats.append(float(values[(v*stride)+s]))
		arr.append(floats)
		
	return arr

#parses stride length arrays and returns outer array
def parse_ints(line):
	values = line.split("\t")
	values.pop() #remove last element, its blank
	ints = []

	for i in values:
		ints.append(int(i))
		
	return ints