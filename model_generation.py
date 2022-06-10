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

def GenerateArmature(Flver, armature_name, collection, connect_bones):
	armature = bpy.data.objects.new(armature_name,bpy.data.armatures.new(armature_name))

	collection.objects.link(armature)

	armature.show_in_front = True
	armature.data.display_type = "WIRE"

	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.mode_set(mode="EDIT", toggle=False)

	def AddBones(bone_index, parent_matrix):
		if bone_index < 0:
			return

		flver_bone = Flver.bones[bone_index]
		blender_bone = armature.data.edit_bones.new(flver_bone.name)

		if flver_bone.parent_index >= 0:
			blender_bone.parent = Flver.bones[flver_bone.parent_index].blender_bone

		# set bone transform relative to parent
		T = flver_bone.translation
		R = ((
				Matrix.Rotation(flver_bone.rotation[1], 4, 'Y') @
				Matrix.Rotation(flver_bone.rotation[2], 4, 'Z') @
				Matrix.Rotation(flver_bone.rotation[0], 4, 'X')
			))
		#S = flver_bone.scale

		head = parent_matrix @ T
		tail = head + R @ Vector((0, 0.05, 0))

		blender_bone.head = (head.x, head.y, head.z)
		blender_bone.tail = (tail.x, tail.y, tail.z)

		flver_bone.blender_bone = blender_bone

		# recurse
		new_parent_matrix = parent_matrix @ Matrix.Translation(T) @ R

		CurrChildIndex = flver_bone.child_index
		while CurrChildIndex >= 0:
			AddBones(CurrChildIndex, new_parent_matrix)
			CurrChildIndex = Flver.bones[CurrChildIndex].next_sibling_index
			if CurrChildIndex == flver_bone.child_index:
				return

	# Spawn new bone, add to root bones if no valid parent
	for i in range(len(Flver.bones)):
		flver_bone = Flver.bones[i]
		if flver_bone.parent_index < 0:
			AddBones(i, Matrix())

	bpy.ops.object.mode_set(mode="OBJECT",toggle=False)
	return armature

def SetMeshWeights(Flver, FlverMesh, BlenderMesh):
	for bone in Flver.bones:
		BlenderMesh.vertex_groups.new(name=bone.name)

	for vi in range(len(FlverMesh.vertices)):
		CurrVert = FlverMesh.vertices[vi]

		for bi in range(len(CurrVert.bone_indices)): # its always 4
			# TODO: rename vert bone indices to indicate that it is an index for the MESH bone indices
			CurrBoneIndex = FlverMesh.bone_indices[CurrVert.bone_indices[bi]]
			CurrBoneWeight = CurrVert.bone_weights[bi]

			bone_name = Flver.bones[CurrBoneIndex].name
			BlenderMesh.vertex_groups[bone_name].add([vi],CurrBoneWeight,'ADD')

# TODO: split this up
def ApplyUVColors(FlverMesh,BlenderMesh):
		vertex_map = None
		colors_done = False
		for uv_index in range(len(FlverMesh.vertices[0].uvs)):
			if uv_index == (len(FlverMesh.vertices[0].uvs) - 1) and uv_index > 0:
				#last one is for light map use
				uv_layer = BlenderMesh.data.uv_layers.new(name="lit_uv") 
			else:
				#naming them all the same thing allows for easier merging of meshes...
				uv_layer = BlenderMesh.data.uv_layers.new(name="UV Map")

			BlenderMesh.data.uv_layers.active = uv_layer

			if colors_done == False:
				BlenderMesh.data.vertex_colors.new(name="Color")
				vertex_map = defaultdict(list)

			#TODO: optimize this, its kinda slow
			for face in BlenderMesh.data.polygons:
				for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
					#making this one assignment seems to be MUCH faster
					uv_layer.data[loop_idx].uv = [
						FlverMesh.vertices[vert_idx].uvs[uv_index][0],
						0 - FlverMesh.vertices[vert_idx].uvs[uv_index][1]
					]
					#y has to be inverted for some reason idk why
					if colors_done == False:
						vertex_map[vert_idx].append(loop_idx)

			#a FOREACH might work here...
			# obj.data.vertex_colors['Color'].data.foreach_set(color, vi.colors[0] in vertexmap)???
			if colors_done == False:
				for vi in range(len(FlverMesh.vertices)):
					for l_i in vertex_map[vi]:
						BlenderMesh.data.vertex_colors['Color'].data[l_i].color = FlverMesh.vertices[vi].colors[0]

			colors_done = True #the color code only needs to run once

def ApplyNormals(FlverMesh,BlenderMesh):
	BMesh = bmesh.new()
	BMesh.from_mesh(BlenderMesh.data)

	BMesh.verts.ensure_lookup_table()

	norms = []
	for v in range(len(BlenderMesh.data.vertices)):
		norms.append(FlverMesh.vertices[v].normal * -1)

	BlenderMesh.data.use_auto_smooth = True
	BlenderMesh.data.calc_normals_split()
	BlenderMesh.data.normals_split_custom_set_from_vertices(norms)
	BlenderMesh.data.free_normals_split()

	BMesh.normal_update()

#if len(self.materials) > 0:
#				mat = self.materials[mesh.material_index].create_material(
#					self.name,
#					self.materials[mesh.material_index].mtd_params,
#					mesh.material_index
#				)
#				mesh_obj.data.materials.append(mat)
#def create_material(self,parent_name,mtd_params,index):
#MTD lists for applying fixes

metals = ['P_Metal[DSB]_Edge.mtd','C_Metal[DSB].mtd','P_Metal[DSB].mtd']
seath = ['C_5290_Body[DSB][M].mtd','C_5290_Body[DSB].mtd']

def GenerateSingleMaterial(FlverMat, full_mat_name):
	#TODO: 2750 doesn't load face textures, presumably from NPC stuff?
	#TODO: 2811 missing boulder textures!
	#full_mat_name = parent_name + "_mat" + str(index) + "_" + FlverMat.name
	mtd_name = FlverMat.mtd.split("\\")[-1]

	#create new material and configure defaults
	mat = bpy.data.materials.new(name=full_mat_name)
	mat.use_nodes = True
	mat.blend_method  = 'HASHED' #blended looks weird.
	mat.shadow_method = 'HASHED'

	#insert mix nodes and ShaderNodeBsdfTransparent
	mix = mat.node_tree.nodes.new(type="ShaderNodeMixShader")
	mix.location = Vector((100.0, 300.0))
	mix2 = mat.node_tree.nodes.new(type="ShaderNodeMixShader")
	mix2.location = Vector((100.0, 440.0))
	mix2.inputs['Fac'].default_value = 1.0
	tpn = mat.node_tree.nodes.new(type="ShaderNodeBsdfTransparent")
	tpn.location = Vector((-160.0, 340.0))

	#link mix_node output to second mix node input
	mat.node_tree.links.new(mix.outputs['Shader'],mix2.inputs[2])

	#link mix2 output to material output
	mat.node_tree.links.new(mix2.outputs['Shader'],	mat.node_tree.nodes['Material Output'].inputs['Surface'])

	#link transparent_node to first slot in mix_node
	mat.node_tree.links.new(tpn.outputs['BSDF'],mix.inputs[1])

	#link transparent_node to first slot in mix_node2
	mat.node_tree.links.new(tpn.outputs['BSDF'],mix2.inputs[1])

	#create vertex color node and link it to the second mix node
	vert_color = mat.node_tree.nodes.new(type="ShaderNodeVertexColor")
	vert_color.location = Vector((-840.0, 360.0))
	vert_color.layer_name = "Color" #TODO: verify this!
	vert_color.hide = True

	#delete default principled bsdf node, add specular
	default_node = mat.node_tree.nodes['Principled BSDF']
	mat.node_tree.nodes.remove(default_node)
	main = mat.node_tree.nodes.new(type="ShaderNodeEeveeSpecular")
	main.location = Vector((-160.0, 240.0))

	if mtd_name == 'C_DullLeather[DSB].mtd':
		main.inputs['Roughness'].default_value = 1.0
		main.inputs['Specular'].default_value = [0.0,0.0,0.0,1.0]
	elif mtd_name == 'C_Leather[DSB].mtd':
		main.inputs['Roughness'].default_value = 0.7
		main.inputs['Specular'].default_value = [0.0,0.0,0.0,1.0]
	elif mtd_name == 'C_Wet[DSB][M].mtd':
		main.inputs['Roughness'].default_value = 0.25
		main.inputs['Specular'].default_value = [0.006,0.006,0.006,1.000]
	elif mtd_name == 'C[D]_Alp.mtd':
		main.inputs['Roughness'].default_value = 1.0
		main.inputs['Specular'].default_value = [0.0,0.0,0.0,1.0]
	else:
		main.inputs['Specular'].default_value = [0.0,0.0,0.0,1.0]
		main.inputs['Roughness'].default_value = 0.8

	#link main_shader to second slot in mix_node
	mat.node_tree.links.new(
		main.outputs['BSDF'],
		mix.inputs[2]
	)

	diff_tex_1 = None
	diff_tex_2 = None
	spec_tex_1 = None
	spec_tex_2 = None
	bump_tex_1 = None
	bump_tex_2 = None
	dbmp_tex_1 = None #TODO: get these added in
	dbmp_tex_2 = None
	lite_tex_1 = None

	spc_pwr_val = 0
	spc_clr_pwr_val = 0
	blend_mode = 0

	for p in FlverMat.mtd_params:
			if p.name == 'g_SpecularPower':
				spc_pwr_val = float(p.value)
			elif p.name == 'g_SpecularMapColorPower':
				spc_clr_pwr_val = float(p.value)
			elif p.name == 'g_BlendMode':
				blend_mode = int(p.value)

	if blend_mode == 2:
		mat.node_tree.links.new(vert_color.outputs['Alpha'],mix2.inputs['Fac'])

	#fixes color/roughness issues for specific materials
	if mtd_name in metals:
		spc_clr_pwr_val = spc_clr_pwr_val * 0.66
	elif mtd_name in seath:
		spc_clr_pwr_val = spc_clr_pwr_val * 2
		spc_pwr_val = spc_pwr_val / 10 #verify if this looks right?

	#predfine these for later use
	diff_mix_rgb = None
	alph_mix_rgb = None
	spec_mix_rgb = None
	spc_clr_pwr  = None
	spc_pwr      = None
	invert       = None
	bump_mix_rgb = None

	for entry in FlverMat.textures:
		if exists(entry.path):
			img = bpy.data.images.load(entry.path, check_existing = True)
			tex_node = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
			tex_node.name = img.name + "_tex_node" +  "-" + str(entry.type)
			tex_node.image = img
			tex_node.image.colorspace_settings.name = "sRGB" #sane default
			tex_node.image.alpha_mode = 'CHANNEL_PACKED' #always use this
			tex_node.hide = True #makes them smaller and easier to manage

			#add in custom properties for verification
			mat[str(entry.type)] = str(entry.path)

			if entry.type == 'g_Diffuse':
				tex_node.location = Vector((-940.0, 320.0))
				diff_tex_1 = tex_node
			elif entry.type == 'g_Diffuse_2':
				tex_node.location = Vector((-940.0, 280.0))
				diff_tex_2 = tex_node
			elif entry.type == 'g_Specular':
				tex_node.location = Vector((-940.0, 240.0))
				tex_node.image.colorspace_settings.name = "Non-Color"
				spec_tex_1 = tex_node
			elif entry.type == 'g_Specular_2':
				tex_node.location = Vector((-940.0, 200.0))
				tex_node.image.colorspace_settings.name = "Non-Color"
				spec_tex_2 = tex_node
			elif entry.type == 'g_Bumpmap':
				tex_node.location = Vector((-940.0, 160.0))
				tex_node.image.colorspace_settings.name = "Non-Color"
				bump_tex_1 = tex_node
			elif entry.type == 'g_Bumpmap_2':
				tex_node.location = Vector((-940.0, 120.0))
				tex_node.image.colorspace_settings.name = "Non-Color"
				bump_tex_2 = tex_node
			elif entry.type == 'g_DetailBumpmap':
				tex_node.location = Vector((-940.0,  80.0))
				tex_node.image.colorspace_settings.name = "Non-Color"
				dbmp_tex_1 = tex_node
			elif entry.type == 'g_DetailBumpmap_2':
				tex_node.location = Vector((-940.0,  40.0))
				tex_node.image.colorspace_settings.name = "Non-Color"
				dbmp_tex_2 = tex_node
			elif entry.type == 'g_Lightmap':
				tex_node.location = Vector((-940.0,   0.0))
				tex_node.image.colorspace_settings.name = "Non-Color"
				lite_tex_1 = tex_node
		elif len(entry.path) > 2: #do this to avoid printing null paths
			print("Failed to load: " + entry.path)

	if diff_tex_1 is not None:
		diff_mix_rgb = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
		diff_mix_rgb.location =  Vector((-640.0, 320.0))
		diff_mix_rgb.blend_type = 'MIX'
		diff_mix_rgb.hide = True

		alph_mix_rgb = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
		alph_mix_rgb.location =  Vector((-640.0, 280.0))
		alph_mix_rgb.blend_type = 'MIX'
		alph_mix_rgb.hide = True

		#link texture to mix node and vertex color to factor, and diff to base
		mat.node_tree.links.new(vert_color.outputs['Alpha'],diff_mix_rgb.inputs['Fac'])
		mat.node_tree.links.new(diff_tex_1.outputs['Color'],diff_mix_rgb.inputs['Color1'])
		mat.node_tree.links.new(diff_mix_rgb.outputs['Color'],main.inputs['Base Color'])

		#link texture alphas to inputs, and mix to shader mixer
		mat.node_tree.links.new(vert_color.outputs['Alpha'],alph_mix_rgb.inputs['Fac'])
		mat.node_tree.links.new(diff_tex_1.outputs['Alpha'],alph_mix_rgb.inputs['Color1'])
		mat.node_tree.links.new(alph_mix_rgb.outputs['Color'],mix.inputs['Fac'])

		if diff_tex_2 is not None:
			mat.node_tree.links.new(diff_tex_2.outputs['Color'],diff_mix_rgb.inputs['Color2'])
			mat.node_tree.links.new(diff_tex_2.outputs['Alpha'],alph_mix_rgb.inputs['Color2'])
		else:
			mat.node_tree.links.new(diff_tex_1.outputs['Color'],diff_mix_rgb.inputs['Color2'])
			mat.node_tree.links.new(diff_tex_1.outputs['Alpha'],alph_mix_rgb.inputs['Color2'])

	if spec_tex_1 is not None:
		spec_mix_rgb = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
		spec_mix_rgb.location =  Vector((-640.0, 240.0))
		spec_mix_rgb.blend_type = 'MIX'
		spec_mix_rgb.hide = True

		#specular COLOR MAP power (plugs into specular)
		spc_clr_pwr = mat.node_tree.nodes.new(type="ShaderNodeGamma")
		spc_clr_pwr.name = "spc_clr_pwr"
		spc_clr_pwr.label = "spc_clr_pwr"
		spc_clr_pwr.hide = True
		spc_clr_pwr.location = Vector((-480.0, 240.0))
		spc_clr_pwr.inputs['Gamma'].default_value = spc_clr_pwr_val

		#specular power (plugs into roughness)
		spc_pwr = mat.node_tree.nodes.new(type="ShaderNodeGamma")
		spc_pwr.name = "spc_pwr"
		spc_pwr.label = "spc_pwr"
		spc_pwr.hide = True
		spc_pwr.location = Vector((-320.0, 200.0))
		spc_pwr.inputs['Gamma'].default_value = spc_pwr_val

		#inverter, needed for spec -> roughness conversion
		invert = mat.node_tree.nodes.new(type="ShaderNodeInvert")
		invert.location = Vector((-480.0, 200.0))
		invert.hide = True

		#link texture to mix node and vertex color to factor
		mat.node_tree.links.new(vert_color.outputs['Alpha'],spec_mix_rgb.inputs['Fac'])
		mat.node_tree.links.new(spec_tex_1.outputs['Color'],spec_mix_rgb.inputs['Color1'])

		#link spec mix to gamma adjust then base specular
		mat.node_tree.links.new(spec_mix_rgb.outputs['Color'],spc_clr_pwr.inputs['Color'])
		mat.node_tree.links.new(spc_clr_pwr.outputs['Color'],main.inputs['Specular'])

		#link spec mix to inverter, gamma adjust, then base roughness
		mat.node_tree.links.new(spec_mix_rgb.outputs['Color'],invert.inputs['Color'])
		mat.node_tree.links.new(invert.outputs['Color'],spc_pwr.inputs['Color'])
		mat.node_tree.links.new(spc_pwr.outputs['Color'],main.inputs['Roughness'])

		if spec_tex_2 is not None:
			mat.node_tree.links.new(spec_tex_2.outputs['Color'],spec_mix_rgb.inputs['Color2'])
		else:
			mat.node_tree.links.new(spec_tex_1.outputs['Color'],spec_mix_rgb.inputs['Color2'])

		#seath fixes
		if mtd_name == 'C_5290_Wing[DSB]_Alp.mtd':
			mat.node_tree.links.new(spec_mix_rgb.outputs['Color'],main.inputs['Emissive Color'])

		#manus fixes
		if mtd_name == 'C_4500_Eyes1[DSB].mtd':
			mat.node_tree.links.new(spc_clr_pwr.outputs['Color'],main.inputs['Emissive Color'])

		if mtd_name == 'C_4500_Eyes2[DSB].mtd':
			mat.node_tree.links.new(spc_clr_pwr.outputs['Color'],main.inputs['Emissive Color'])

	if bump_tex_1 is not None:
		bump_mix_rgb = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
		bump_mix_rgb.location =  Vector((-640.0, 160.0))
		bump_mix_rgb.blend_type = 'MIX'
		bump_mix_rgb.hide = True

		#link texture to mix node and vertex color to factor
		mat.node_tree.links.new(vert_color.outputs['Alpha'],bump_mix_rgb.inputs['Fac'])
		mat.node_tree.links.new(bump_tex_1.outputs['Color'],bump_mix_rgb.inputs['Color1'])

		#create normal map node
		bump_node = mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
		bump_node.location = Vector((-480.0, 160.0))
		bump_node.name = mat.name + "_bumpmap_node"
		bump_node.hide = True
		bump_node.space = "TANGENT"

		mat.node_tree.links.new(bump_mix_rgb.outputs['Color'],bump_node.inputs['Color'])
		mat.node_tree.links.new(bump_node.outputs['Normal'],main.inputs['Normal'])

		if bump_tex_2 is not None:
			mat.node_tree.links.new(bump_tex_2.outputs['Color'],bump_mix_rgb.inputs['Color2'])
		else:
			mat.node_tree.links.new(bump_tex_1.outputs['Color'],bump_mix_rgb.inputs['Color2'])

	if lite_tex_1 is not None:
		uv_map = mat.node_tree.nodes.new(type="ShaderNodeUVMap")
		uv_map.location = Vector((-1040.0, 0.0))
		uv_map.name = "lit_uv"
		uv_map.label = "lit_uv"
		uv_map.uv_map = "lit_uv" #yay

		lit_pwr = mat.node_tree.nodes.new(type="ShaderNodeGamma")
		lit_pwr.name = "lit_pwr"
		lit_pwr.label = "lit_pwr"
		lit_pwr.location = Vector((-920.0, -400.0))
		lit_pwr.inputs['Gamma'].default_value = 1.0

		lit_mix_rgb = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
		lit_mix_rgb.blend_type = 'MULTIPLY'
		lit_mix_rgb.location = Vector((-900.0, -400.0))
		lit_mix_rgb.inputs['Fac'].default_value = 1.0

		mat.node_tree.links.new(uv_map.outputs['UV'],lite_tex_1.inputs['Vector'])
		mat.node_tree.links.new(lite_tex_1.outputs['Color'],lit_pwr.inputs['Color'])
		mat.node_tree.links.new(lit_pwr.outputs['Color'],lit_mix_rgb.inputs['Color2'])
		mat.node_tree.links.new(diff_mix_rgb.outputs['Color'],lit_mix_rgb.inputs['Color1'])
		mat.node_tree.links.new(lit_mix_rgb.outputs['Color'],main.inputs['Emissive Color'])

	#assign custom properties to the material relating to the MTD its based on
	mat["MTD_NAME"] = mtd_name
	for param in FlverMat.mtd_params:
		mat[str(param.name)] = str(param.value)

	return mat

#			if len(self.materials) > 0:
#				mat = self.materials[mesh.material_index].create_material(
#					self.name,
#					self.materials[mesh.material_index].mtd_params,
#					mesh.material_index
#				)
#				mesh_obj.data.materials.append(mat)

def GenerateMaterials(Flver):
	Materials = []
	for i in range(len(Flver.materials)):
		#parent_name + "_mat" + str(index) + "_" + FlverMat.name
		Materials.append(GenerateSingleMaterial(Flver.materials[i], Flver.name  + "_mat_" + str(i)))

	return Materials

def GenerateMesh(Flver, FlverMesh, FlverName, Armature, Materials):
	FullName = FlverName + "_" + FlverMesh.name + "_f"

	VertPositions = []
	for V in FlverMesh.vertices:
		VertPositions.append(V.position)

	# what the hell does this do
	FaceTris = (numpy.array(FlverMesh.facesets.indices)).reshape(-1,3).tolist()

	# add to blender
	MeshData = bpy.data.meshes.new("mesh")
	MeshData.from_pydata(VertPositions,[],FaceTris)
	MeshData.update

	BlenderMesh = bpy.data.objects.new(FullName,MeshData)
	bpy.context.collection.objects.link(BlenderMesh)
	FlverMesh.bm.from_mesh(BlenderMesh.data)

	SetMeshWeights(Flver, FlverMesh, BlenderMesh)
	ApplyUVColors(FlverMesh, BlenderMesh)
	ApplyNormals(FlverMesh, BlenderMesh)


	# apply material
	BlenderMesh.data.materials.append(Materials[FlverMesh.material_index])

	#parent to skeleton, and setup modifiers
	BlenderMesh.parent = Armature
	BlenderMesh.modifiers.new(name='Armature',type='ARMATURE')
	BlenderMesh.modifiers['Armature'].object = Armature
	BlenderMesh.modifiers['Armature'].use_deform_preserve_volume = True
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

	proper_location = mathutils.Matrix.Translation((-FlverDummy.position[0],FlverDummy.position[2],-FlverDummy.position[1]))
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
	collection = bpy.context.collection

	Armature = GenerateArmature(Flver, Flver.name+"_armature", collection, True)

	Materials = GenerateMaterials(Flver)

	Meshes = []
	for FlverMesh in Flver.meshes:
		Meshes.append(GenerateMesh(Flver, FlverMesh, Flver.name, Armature, Materials))

	for i in range(len(Flver.dummies)):
		Dummy = Flver.dummies[i]
		DummyName = Flver.name + "_d" + str(i) + "_" + str(Dummy.refid)

		GenerateDummy(Dummy, DummyName, Armature, collection)


	Armature.rotation_euler[0] = math.radians(90)
	Armature.scale[0] = -1