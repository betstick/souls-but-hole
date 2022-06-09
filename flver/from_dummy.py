import bpy
import sys
import bmesh
import subprocess
import mathutils
import math
from mathutils import Vector
import time
import cProfile

from ..tools.deserialization import *

class Dummy:
	@staticmethod
	def Deserialize(p):
		self = Dummy()
		self.refid = ReadInt(p)
		self.position = ReadFloat3(p)
		self.upward = ReadFloat3(p)
		self.use_upward = ReadBool(p)
		self.attach_bone_index = ReadInt(p)
		self.parent_bone_index = ReadInt(p)
		return self


	def print(self):
		s = "Dummy: " + str(self.type) + " "  + str(self.position) + " " 
		s += str(self.attach_bone_index) + " " + str(self.parent_bone_index)
		print(s)

	#TODO: make this code suck less. its messy and i don't understand why it works
	#TODO: make the upward bit do something as well
	def create(self,parent_name,collection,armature):
		#print(bpy.data.objects[parent_name + "_armature"].data)

		empty = bpy.data.objects.new(str(parent_name) + "_d" + str(self.index) + "_" + str(self.refid), None)
		#actually spawn it in, needs to happen before we modify anything in it?
		collection.objects.link(empty)
		
		empty.empty_display_size = 0.15
		empty.empty_display_type = 'SINGLE_ARROW'
		
		#this is stupid. to parent an object you need the OBJECT reference.
		empty.parent = armature

		empty.parent_type = "BONE"
		empty.parent_bone = armature.data.bones[self.attach_bone_index].name
		
		proper_location = mathutils.Matrix.Translation((-self.position[0],self.position[2],-self.position[1]))
		proper_scale = mathutils.Matrix.Scale(1.0, 4, (0.0, 0.0, 1.0))
		proper_rotation = mathutils.Matrix.Rotation(math.radians(0.0), 4, 'X')

		#TODO: fix this, it clearly does not work
		#if self.use_upward:
		#	proper_rotation = mathutils.Matrix.Rotation(math.radians(self.upward[0]), 4, 'X')
		#	proper_rotation.Rotation(math.radians(self.upward[1]), 4, 'Y')
		#	proper_rotation.Rotation(math.radians(self.upward[2]), 4, 'Z')
		
		proper_matrix = proper_location @ proper_scale @ proper_rotation
		
		#apply the correct matrix and also rotate it so it points up for now
		empty.matrix_world = proper_matrix #@ mathutils.Euler((-1.570797,0.0,0.0),'XYZ').to_matrix().to_4x4()
		#TODO: figure out how to rotate with a euler...

		#use clear parent and keep transform in order to get the actual location :fatcat:
		#might even dupe it, clear apply the ops to the duplicate, pull nums, then delete the dupe?