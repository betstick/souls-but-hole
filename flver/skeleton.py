import bpy
import sys
import bmesh
import subprocess
import mathutils
import math
from mathutils import Vector
import time
import cProfile

# custom stuff ripped from YAVNE
from . import util

from ..tools.deserialization import *

class Bone:
	@staticmethod
	def Deserialize(p):
		self = Bone()

		self.name = ReadString(p)

		# transform
		self.translation = ReadFloat3(p)
		self.rotation = ReadFloat3(p)
		self.scale = ReadFloat3(p)

		#relation
		self.parent_index = ReadInt(p)
		self.child_index = ReadInt(p)
		self.next_sibling_index = ReadInt(p)
		self.previous_sibling_index = ReadInt(p)

		return self

class Skeleton:
	def __init__(self, bones):
		self.bones = bones

	#not thread safe, might not be possible to make it thread safe...
	def create_armature(self, armature_name, collection, connect_bones, axes):
		armature = bpy.data.objects.new(armature_name,bpy.data.armatures.new(armature_name))
		
		collection.objects.link(armature)
		
		armature.show_in_front = True
		armature.data.display_type = "WIRE"

		bpy.context.view_layer.objects.active = armature
		bpy.ops.object.mode_set(mode="EDIT", toggle=False)

		root_bones = []

		for flver_bone in self.bones:
			bone = armature.data.edit_bones.new(flver_bone.name)
			if flver_bone.parent_index < 0:
				root_bones.append(bone)

		def transform_bone_and_siblings(bone_index, parent_matrix):
			while bone_index != -1:
				flver_bone = self.bones[bone_index]
				bone = armature.data.edit_bones[bone_index]
				
				if flver_bone.parent_index >= 0:
					bone.parent = armature.data.edit_bones[flver_bone.parent_index]
					
				translation_vector = mathutils.Vector((
					flver_bone.translation[0],
					flver_bone.translation[1],
					flver_bone.translation[2],
				))
				
				rotation_matrix = ((
					mathutils.Matrix.Rotation(flver_bone.rotation[1], 4, 'Y') @
					mathutils.Matrix.Rotation(flver_bone.rotation[2], 4, 'Z') @
					mathutils.Matrix.Rotation(flver_bone.rotation[0], 4, 'X')
				))
				
				head = parent_matrix @ translation_vector
				tail = head + rotation_matrix @ mathutils.Vector((0,0.05,0))
				
				bone.head = (head[axes[0]], head[axes[1]], head[axes[2]])
				bone.tail = (tail[axes[0]], tail[axes[1]], tail[axes[2]])
				
				transform_bone_and_siblings(
					flver_bone.child_index, 
					parent_matrix @
					mathutils.Matrix.Translation(translation_vector) @
					rotation_matrix
				)
					
				bone_index = flver_bone.next_sibling_index
				
		transform_bone_and_siblings(0, mathutils.Matrix())
		
		def connect_bone(bone):
			children = bone.children
			if len(children) == 0:
				parent = bone.parent
				if parent is not None:
					direction = parent.tail - parent.head
					direction.normalize()
					length = (bone.tail - bone.head).magnitude
					bone.tail = bone.head + direction * length
				return
			if len(children) > 1:
				for child in children:
					connect_bone(child)
				return
			child = children[0]
			bone.tail = child.head
			child.use_connect = True
			connect_bone(child)
			
		if connect_bones:
			for bone in root_bones:
				connect_bone(bone)

		bpy.ops.object.mode_set(mode="OBJECT",toggle=False)
		return armature