from collections import defaultdict
import bpy
import sys
import bmesh
import subprocess
import mathutils
import math
from mathutils import Vector
import time
import cProfile
import struct
import numpy

from . import util

from ..tools.deserialization import *

class Vertex:
	@staticmethod
	def Deserialize(p):
		self = Vertex()
		self.position = ReadFloat3(p)
		self.bone_indices = ReadInt4(p)
		self.bone_weights = ReadFloat4(p)
		self.uvs = ReadArray(p, ReadFloat3)
		self.normal = ReadFloat3(p)
		self.normalw = ReadFloat(p)

		self.colors = ReadArray(p, ReadFloat4)
		#self.tangents = []
		#	self.bitangent = None
		return self

class Faceset:
	@staticmethod
	def Deserialize(p):
		self = Faceset()
		self.flags = ReadInt(p)
		self.indices = ReadArray(p, ReadInt)
		self.lod = 0
		return self

	def get_tri_list(self):
		return (numpy.array(self.indices)).reshape(-1,3).tolist()

class Mesh:
	@staticmethod
	def Deserialize(p):
		self = Mesh()
		self.name = ""
		self.full_name = ""
		self.bone_indices = ReadArray(p, ReadInt)
		self.defaultBoneIndex = ReadInt(p)
		self.material_index = ReadInt(p)
		self.vertices = ReadArray(p, Vertex.Deserialize)
		self.facesets = Faceset.Deserialize(p)

		self.bm = bmesh.new()
		return self
	
	def add_faceset(self,line):
		self.facesets.append(Faceset(line))

	def get_vert_list(self):
		vertpos = [] #return variable

		for vert in self.vertices:
			vertpos.append(vert.position)

		return vertpos

	#use specific faceset to build up a blender mesh
	#returns handle to mesh obj, for use with bone rigging
	def create_mesh(self,model_name,faceset):
		self.full_name = model_name + "_" + self.name + "_f" + str(faceset.lod)

		#list_start = time.time()
		verts = self.get_vert_list()
		faces = faceset.get_tri_list()
		#list_time = str(round(time.time() - list_start, 3))

		#bmesh_start = time.time()
		mesh = bpy.data.meshes.new("mesh")
		mesh.from_pydata(verts,[],faces)        
		mesh.update
		obj = bpy.data.objects.new(self.full_name,mesh)
		bpy.context.collection.objects.link(obj)
		self.bm.from_mesh(obj.data)
		#bmesh_time = str(round(time.time() - bmesh_start, 3))

		#totals = "\tl:" + list_time + "s\tb:" + bmesh_time + "s\tn:" + norm_time + "s"
		#print("\tMesh: " + self.name + ": " + totals )

		return obj

	def apply_normals(self,obj):
		self.bm.verts.ensure_lookup_table()
		
		norms = []
		for v in range(len(obj.data.vertices)):
			norms.append(self.vertices[v].normal * -1)

		obj.data.use_auto_smooth = True
		obj.data.calc_normals_split()
		obj.data.normals_split_custom_set_from_vertices(norms)
		obj.data.free_normals_split()

		self.bm.normal_update()

		#need to flip the faces for some reason.
		#probably related to axis flipping...?
		#bpy.ops.mesh.select_all()
		#bpy.ops.mesh.flip_normals()

	#thread safe!
	def apply_uvs_colors(self,obj):
		vertex_map = None
		colors_done = False
		for uv_index in range(len(self.vertices[0].uvs)):
			if uv_index == (len(self.vertices[0].uvs) - 1) and uv_index > 0:
				#last one is for light map use
				uv_layer = obj.data.uv_layers.new(name="lit_uv") 
			else:
				#naming them all the same thing allows for easier merging of meshes...
				uv_layer = obj.data.uv_layers.new(name="UV Map")

			obj.data.uv_layers.active = uv_layer
			
			if colors_done == False:
				obj.data.vertex_colors.new(name="Color")
				vertex_map = defaultdict(list)

			#TODO: optimize this, its kinda slow
			for face in obj.data.polygons:
				for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
					#making this one assignment seems to be MUCH faster
					uv_layer.data[loop_idx].uv = [
						self.vertices[vert_idx].uvs[uv_index][0],
						0 - self.vertices[vert_idx].uvs[uv_index][1]
					]
					#y has to be inverted for some reason idk why
					if colors_done == False:
						vertex_map[vert_idx].append(loop_idx)
			
			#a FOREACH might work here...
			# obj.data.vertex_colors['Color'].data.foreach_set(color, vi.colors[0] in vertexmap)???
			if colors_done == False:
				for vi in range(len(self.vertices)):
					for l_i in vertex_map[vi]:
						obj.data.vertex_colors['Color'].data[l_i].color = self.vertices[vi].colors[0]

			colors_done = True #the color code only needs to run once