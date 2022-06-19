import bpy
import mathutils
import numpy
import bmesh
from collections import defaultdict
from mathutils import Vector
from mathutils import Matrix
from os.path import exists
import math

from .DataTypes import *
from .mat_ds1 import *

def GenerateArmature(flver_bones, armature_name, collection, connect_bones):
	armature = bpy.data.objects.new(armature_name,bpy.data.armatures.new(armature_name))

	collection.objects.link(armature)

	armature.show_in_front = True
	armature.data.display_type = "WIRE"

	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.mode_set(mode="EDIT", toggle=False)

	root_bones = []

	for flver_bone in flver_bones:
		bone = armature.data.edit_bones.new(flver_bone.name)
		if flver_bone.parent_index < 0:
			root_bones.append(bone)

	for i in range(len(flver_bones)):
		flver_bone = flver_bones[i]

		if not flver_bone.bInitialized:
			break

		blender_bone = armature.data.edit_bones[i]

		# Set Parent
		if flver_bone.parent_index >= 0:
			blender_bone.parent = armature.data.edit_bones[flver_bone.parent_index]

		# Set transform
		blender_bone.head = flver_bone.head_pos
		blender_bone.tail = flver_bone.tail_pos

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

	#rotate and invert axis to correct for from axes differences
	armature.rotation_euler[0] = math.radians(90)
	armature.scale[0] = -1

	bpy.context.view_layer.objects.active = armature
	armature.select_set(state=True)
	bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
	armature.select_set(state=False)
	bpy.context.view_layer.objects.active = None

	return armature

def create_weight_layers(Flver, FlverMesh, BlenderMesh):
	for bone in Flver.bones:
		BlenderMesh.vertex_groups.new(name=bone.name)

def SetMeshWeights(Flver, FlverMesh, BlenderMesh):
	if len(FlverMesh.bone_indices) > 0:
		for bi in FlverMesh.bone_indices:
			bone_name = Flver.bones[bi].name
			BlenderMesh.vertex_groups[bone_name].add(range(len(FlverMesh.vertices)),0.0,'ADD')
	else:
		for vg in BlenderMesh.vertex_groups:
			vg.add(range(len(FlverMesh.vertices)),0.0,'ADD')

	bm = bmesh.new()
	bm.from_mesh(BlenderMesh.data)
	bm.verts.ensure_lookup_table()

	layer_deform = bm.verts.layers.deform.active
	use_mesh_indices = len(FlverMesh.bone_indices) > 0

	for vert in bm.verts:
		CurrFlverVert = FlverMesh.vertices[vert.index]

		for b_i in range(4):
			if use_mesh_indices:
				true_bone_index = FlverMesh.bone_indices[CurrFlverVert.bone_indices[b_i]]
			else:
				#DS3 seems to do this?
				true_bone_index = CurrFlverVert.bone_indices[b_i]

			bone_weight = CurrFlverVert.bone_weights[b_i]

			if bone_weight != 0:
				vert[layer_deform][true_bone_index] = bone_weight

	bm.to_mesh(BlenderMesh.data)

#modifies blendermesh
def create_uvs(FlverMesh,BlenderMesh):
	uv_layers = []

	for uv_index in range(len(FlverMesh.vertices[0].uvs)):	
		if uv_index == (len(FlverMesh.vertices[0].uvs) - 1) and uv_index > 0:
			#last one is for light map use
			uv_layers.append(BlenderMesh.data.uv_layers.new(name="lit_uv"))
		else:
			#naming them all the same thing allows for easier merging of meshes...
			uv_layers.append(BlenderMesh.data.uv_layers.new(name="UV Map"))

	return uv_layers

def apply_uvs(FlverMesh,bm,uv_layer,uv_index):
	uv_map = bm.loops.layers.uv[uv_layer.name]

	for face in bm.faces:
		for loop in face.loops:
			index = loop.vert.index
			loop[uv_map].uv = [
				FlverMesh.vertices[index].uvs[uv_index][0],
				0 - FlverMesh.vertices[index].uvs[uv_index][1]
			]
	return 0

def create_colors(FlverMesh,BlenderMesh):
	BlenderMesh.data.vertex_colors.new(name="Color")

def apply_colors(FlverMesh,bm):
	color_layer = bm.loops.layers.color['Color']

	for v in bm.verts:
		for loop in v.link_loops:
			loop[color_layer] = FlverMesh.vertices[v.index].colors[0]

def ApplyNormals(FlverMesh,BlenderMesh):
	bm = bmesh.new()
	bm.from_mesh(BlenderMesh.data)
	BlenderMesh.data.use_auto_smooth = True
	BlenderMesh.data.calc_normals_split()
	BlenderMesh.data.normals_split_custom_set_from_vertices(
		[FlverMesh.vertices[v].normal for v in range(len(BlenderMesh.data.vertices))]
	)
	BlenderMesh.data.free_normals_split()

	bm.normal_update()

def GenerateMaterials(Flver):
	game_ver = bpy.context.scene.souls_plug_props.game_version
	
	if game_ver == 'PTDE':
		return [create_ptde_material(Flver.materials[i], Flver.name  + "_mat_" + str(i)) for i in range(len(Flver.materials))]
	elif game_ver == 'DS3':
		return [create_ds3_material(Flver.materials[i], Flver.name  + "_mat_" + str(i)) for i in range(len(Flver.materials))]

def GenerateMesh(Flver, FlverMesh, FlverMeshName, Armature, Materials, load_norms, collection):
	FullName = Flver.name + "_" + FlverMeshName + "_f0" #faceset 0

	# add to blender
	BlenderMesh = bpy.data.objects.new(FullName,bpy.data.meshes.new("mesh"))

	#parent to skeleton, and setup modifiers
	BlenderMesh.parent = Armature
	BlenderMesh.modifiers.new(name='Armature',type='ARMATURE')
	BlenderMesh.modifiers['Armature'].object = Armature
	BlenderMesh.modifiers['Armature'].use_deform_preserve_volume = True

	#gotta create uvs here so mesh is up to data?
	layers = create_uvs(FlverMesh,BlenderMesh)
	create_colors(FlverMesh,BlenderMesh)
	create_weight_layers(Flver, FlverMesh, BlenderMesh)

	#actually build the mesh
	mesh = bmesh.new()
	mesh.from_mesh(BlenderMesh.data)

	for v in FlverMesh.vertices:
		mesh.verts.new(v.position)

	mesh.verts.ensure_lookup_table()

	for ft in FlverMesh.facesets.indices:
		try:
			mesh.faces.new((
				mesh.verts[ft[0]],
				mesh.verts[ft[1]],
				mesh.verts[ft[2]],
			))
		except:
			#literally do nothing if there's an error, it doesn't matter
			1 + 1

	#dunno what or why, but this makes it work
	mesh.faces.ensure_lookup_table()
	mesh.verts.ensure_lookup_table()
	mesh.faces.index_update()
	mesh.verts.index_update()

	#apply uvs HERE after mesh built	
	for i in range(len(layers)):
		apply_uvs(FlverMesh,mesh,layers[i],i)

	apply_colors(FlverMesh,mesh)

	mesh.to_mesh(BlenderMesh.data)	
	collection.objects.link(BlenderMesh)

	SetMeshWeights(Flver,FlverMesh,BlenderMesh)

	if load_norms:
		ApplyNormals(FlverMesh,BlenderMesh)

	#remove doubles via modifier, apply later
	BlenderMesh.modifiers.new(name='Weld',type='WELD')

	# apply material
	BlenderMesh.data.materials.append(Materials[FlverMesh.material_index])
	
	return BlenderMesh

def GenerateDummy(FlverDummy, Name, Armature, collection):
	empty = bpy.data.objects.new(Name, None)
	#actually spawn it in, needs to happen before we modify anything in it?
	collection.objects.link(empty)

	empty.empty_display_size = 0.15
	empty.empty_display_type = 'SINGLE_ARROW'

	#this is stupid. to parent an object you need the OBJECT reference.
	empty.parent = Armature

	empty.parent_type = "BONE"
	empty.parent_bone = Armature.data.bones[FlverDummy.attach_bone_index].name

	proper_location = mathutils.Matrix.Translation(FlverDummy.position)
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

def GenerateFlver(Flver, bLoadNormals):
	flver_col = bpy.data.collections.new(Flver.name)
	bpy.context.collection.children.link(flver_col)

	Armature = GenerateArmature(Flver.bones, Flver.name+"_armature", flver_col, True)
	mats = GenerateMaterials(Flver)
	Meshes = [GenerateMesh(Flver, FlverMesh, "m" + str(i), Armature, mats, bLoadNormals, flver_col) for i, FlverMesh in enumerate(Flver.meshes)]

	for i in range(len(Flver.dummies)):
		Dummy = Flver.dummies[i]
		DummyName = Flver.name + "_d" + str(i) + "_" + str(Dummy.refid)

		GenerateDummy(Dummy, DummyName, Armature, flver_col)

	return Armature