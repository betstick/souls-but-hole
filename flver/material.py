import bpy
import sys
import bmesh
import subprocess
import mathutils
import math
from mathutils import Vector
import time
import cProfile
import collections
from os.path import exists

# custom stuff ripped from YAVNE
from . import util

from ..tools.deserialization import *
from .mtd import *


#MTD lists for applying fixes
metals = ['P_Metal[DSB]_Edge.mtd','C_Metal[DSB].mtd','P_Metal[DSB].mtd']
seath = ['C_5290_Body[DSB][M].mtd','C_5290_Body[DSB].mtd']

class Texture_Entry:
	@staticmethod
	def Deserialize(p):
		self = Texture_Entry()
		self.path = ReadString(p)
		self.scale_x = ReadFloat(p)
		self.scale_y = ReadFloat(p)
		self.type = ReadString(p)
		return self

class Material:
	@staticmethod
	def Deserialize(p):
		self = Material()
		self.name = ReadString(p)
		self.mtd = ReadString(p)
		self.flags = ReadInt(p)
		self.gx_index = ReadInt(p)
		self.textures = ReadArray(p, Texture_Entry.Deserialize)
		self.mtd_params = ReadArray(p, MtdParam.Deserialize)
		return self

	#this is overly complex i think :/
	#TODO: figure out if this is even a good idea
	def compare_materials(self,new_mat_name):
		#if name found, check if textures are different
		if bpy.data.materials.find(new_mat_name) != -1:
			new_images = []

			for entry in self.textures:
				new_images.append(entry.path.replace(".tga","").replace(".TGA","").split("\\")[-1])

			old_images = []
			existing = bpy.data.materials[bpy.data.materials.find(new_mat_name)]
			for node in existing.node_tree.nodes:
				if node.bl_idname == 'ShaderNodeTexImage':
					old_images.append(node.image.name)
				
			if set(new_images) == set(old_images):
				print("Duplicate material found for: " + new_mat_name)
				return 0 #just do this to get out of the rest of the function :/
			else:
				print("Reused name for different material, renaming: " + new_mat_name)
				new_mat_name += "_a"
				name = self.compare_materials(new_mat_name)
				
				#keep looping thru till name is unique?
				while(name == 0):
					name = self.compare_materials(new_mat_name)
				
				return name
		else:
			return new_mat_name

	#TODO: 2750 doesn't load face textures, presumably from NPC stuff?
	#TODO: 2811 missing boulder textures!
	def create_material(self,parent_name,mtd_params,index):
		full_mat_name = parent_name + "_mat" + str(index) + "_" + self.name
		mtd_name = self.mtd.split("\\")[-1]

		#check for existing materials of the same name, some meshes reuse names for diff materials
		if bpy.data.materials.find(full_mat_name) != -1:
			exist = bpy.data.materials[bpy.data.materials.find(full_mat_name)]

			used_textures = []
			is_duplicate = False

			#compile list of used textures for materials with matching names
			for node in exist.node_tree.nodes:
				if node.bl_idname == 'ShaderNodeTexImage':
					used_textures.append(node.image.name)

			#if any textures aren't in the previous material, then it should be unique?
			for tex in self.textures:
				if tex.path.lower().replace(".tga","").split("\\")[-1] + ".dds" not in used_textures:
					is_duplicate = False

			#create a unique name by continuously increasing the number
			if is_duplicate == False:
				i = 1
				
				while bpy.data.materials.find(full_mat_name + '_' + str(i)) != -1:
					i += 1

				#set name to newly made unique name 
				full_mat_name = full_mat_name + '_' + str(i)

			else:
				return 0 #need to have this return original material

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

		for p in mtd_params:
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

		for entry in self.textures:
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
		for param in mtd_params:
			mat[str(param.name)] = str(param.value)

		return mat