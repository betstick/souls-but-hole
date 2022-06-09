import bpy
import sys
import bmesh
import subprocess
import mathutils
import math
from mathutils import Vector
import time
import cProfile
import io
from contextlib import redirect_stdout
from threading import Thread
import numpy
import bmesh

# custom stuff ripped from YAVNE is in normals
#from . import util
from . import mesh
from . import skeleton
from . import material
from . import from_dummy
from . import mtd

from ..tools.deserialization import *

class Header:
	def __init__(self, bone_count, mesh_count, mat_count, dummy_count, gxlist_count):
		self.bone_count = bone_count
		self.mesh_count = mesh_count
		self.mat_count = mat_count
		self.dummy_count = dummy_count
		self.gxlist_count = gxlist_count

	def print(self):
		print("Header Info:")
		print(self.bone_count)
		print(self.mesh_count)
		print(self.mat_count)
		print(self.dummy_count)
		print(self.gxlist_count)

class Flver:
	@staticmethod
	def Deserialize(p):
		self = Flver()

		self.name = ReadString(p)

		self.headerinfo = Header(ReadInt(p), ReadInt(p), ReadInt(p), ReadInt(p), ReadInt(p))

		self.skeleton = skeleton.Skeleton(ReadArray(p, skeleton.Bone.Deserialize))
		self.materials = ReadArray(p, material.Material.Deserialize)

		self.meshes = ReadArray(p, mesh.Mesh.Deserialize)
		for i in range(len(self.meshes)):
			self.meshes[i].name = "m" + str(i)

		self.dummies = ReadArray(p, from_dummy.Dummy.Deserialize)
		for i in range(len(self.dummies)):
			self.dummies[i].index = i

		self.armature = None
		self.collection = bpy.context.collection

		return self

	def add_header_info(self,line):
		self.headerinfo = Header(line)

	def add_mesh(self,lines):
		self.meshes.append(mesh.Mesh(lines))

	def add_skeleton(self,lines):
		self.skeleton = skeleton.Skeleton(lines)
	
	def add_material(self,lines,index):
		self.materials.append(material.Material(lines,index))

	def add_dummy(self,lines,index):
		self.dummies.append(from_dummy.Dummy(lines,index))
	
	#is this even used?
	def add_path(self,lines):
		self.path = lines[0]

	def add_texture_paths(self,lines):
		for line in lines:
			self.texture_paths.append(line)

	def add_mtd(self,lines,index):
		self.mtds.append(mtd.Mtd(lines,index))
	
	# newer less slow mesh bone weighting system. no clue how it works. i did write it though.
	def weight_mesh_obj(self,mesh,obj):
		#for bi in mesh.bone_indices:
		for bone in self.skeleton.bones:
			#obj.vertex_groups.new(name=self.skeleton.bones[bi].name)
			obj.vertex_groups.new(name=bone.name)

		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode = 'EDIT')
		mesh.bm = bmesh.from_edit_mesh(obj.data)
		mesh.bm.verts.ensure_lookup_table()
		ld = mesh.bm.verts.layers.deform.active
		assert ld is not None

		for vi in range(len(mesh.vertices)):
			for bi in range(4): # bone_index count, its always 4
				#bone_name = self.skeleton.bones[mesh.bone_indices[mesh.vertices[vi].bone_indices[bi]]].name
				#obj.vertex_groups[bone_name].add([int(vi)],mesh.vertices[vi].bone_weights[bi],'ADD')
				key = int(mesh.vertices[vi].bone_indices[bi])
				print(vi)
				print(key)
				mesh.bm.verts[vi][ld][key] = float(mesh.vertices[vi].bone_weights[bi])
		
		#mesh.bm.update_mesh()

	# experimental, doesn't set the weights to the correct values.... 10x faster
	def weight_mesh_obj_exp(self,mesh,obj):
		vg_v = {}
		vg_w = {}

		for bi in range(len(mesh.bone_indices)):
			obj.vertex_groups.new(name=self.skeleton.bones[mesh.bone_indices[bi]].name)
			vg_v[mesh.bone_indices[bi]] = []
			vg_w[mesh.bone_indices[bi]] = []

		#print(len(vg_v))

		for vi in range(len(mesh.vertices)):
			for bi in range(4): # bone_index count, its always 4
				vg_v[mesh.bone_indices[mesh.vertices[vi].bone_indices[bi]]].append(int(vi))
				vg_w[mesh.bone_indices[mesh.vertices[vi].bone_indices[bi]]].append(mesh.vertices[vi].bone_weights[bi])

		for bi in range(len(mesh.bone_indices)):
			bone_name = self.skeleton.bones[mesh.bone_indices[bi]].name
			obj.vertex_groups[bone_name].add(vg_v[mesh.bone_indices[bi]],1.0,'ADD')

	def weight_mesh_obj_3(self,mesh,obj):
		for vi in mesh.bm.vertices:
			vi.deform

	#not thread safe, has to be done in serial
	def create_skeleton(self):
		#create armature, will be used as parent for meshes
		self.armature = self.skeleton.create_armature(
			self.name+"_armature",
			self.collection,
			True,
			(0, 1, 2)
		)

	def create_flver(self,cust_norms):
		
		#create armature, will be used as parent for meshes
		self.armature = self.skeleton.create_armature(
			self.name+"_armature",
			self.collection,
			True,
			(0, 1, 2)
		)

		#start_time = time.time()
		#print("Beginning: " + self.name)

		#meshes_start = time.time()
		mesh_objs = []

		for mesh in self.meshes:
			if bpy.data.meshes.find(mesh.full_name) == -1:
				#mesh_start = time.time()
				#temporarily only making the lod 0 meshes, highest res
				#cProfile.runctx('mesh.create_mesh(self.name + "profile")',globals(),locals())
				mesh_obj = mesh.create_mesh(self.name,mesh.facesets)
				mesh_objs.append(mesh_obj)

				#weight_start = time.time()
				self.weight_mesh_obj(mesh,mesh_obj)
				#weight_time = str(round(time.time() - weight_start, 2))

				#uv_start = time.time()
				mesh.apply_uvs_colors(mesh_obj)
				#mesh.apply_colors(mesh_obj)
				#uv_time = str(round(time.time() - uv_start, 2))					

				#cProfile.runctx('self.apply_normals(mesh,mesh_obj)',globals(),locals())
				#norm_start = time.time()
				if cust_norms:
					mesh.apply_normals(mesh_obj)
				#norm_time = str(round(time.time() - norm_start, 2))
				
				#check for if no materials are imported
				if len(self.materials) > 0:
					mat = self.materials[mesh.material_index].create_material(
						self.name,
						self.materials[mesh.material_index].mtd_params,
						mesh.material_index
					)
					mesh_obj.data.materials.append(mat)

				#parent to skeleton, and setup modifiers
				mesh_obj.parent = self.armature
				mesh_obj.modifiers.new(name='Armature',type='ARMATURE')
				mesh_obj.modifiers['Armature'].object = self.armature
				mesh_obj.modifiers['Armature'].use_deform_preserve_volume = True

				#mesh_time = str(round(time.time() - mesh_start,2))
				#totals = "\tm:" + mesh_time + "s\tw:" + weight_time + "s\tu:" + uv_time + "s\tn:" + norm_time + "s"
				#print("\tMesh: " + mesh.name + ": " + totals )
				
		#print("[" + self.name + "] Meshes took: " + str(round(time.time() - meshes_start,2)) + "s")

		for d in self.dummies:
			d.create(self.name,self.collection,self.armature)

		#rotate the rig 90 degrees on x axis, scale -1 on x, then apply the transformations.
		#by default the mesh would be looking down cause i don't flip the axis during generation.
		#it'd also be mirrored cause from flips their x axis
		self.armature.rotation_euler[0] = math.radians(90)
		self.armature.scale[0] = -1
		#TODO: figure out how to apply this without changing context to keep it thread safe
		#bpy.ops.object.transform_apply(location=False,rotation=True,scale=True,properties=False)

		#print(self.name + " took " + str(round(time.time() - start_time,2)) + "s total")

		return mesh_objs