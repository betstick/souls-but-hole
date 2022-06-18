from .DataTypes import Flver
import bpy
import mathutils
import numpy
import bmesh
from collections import defaultdict
from mathutils import Vector
from mathutils import Matrix
from os.path import exists
import math
import subprocess

#MTD lists for applying fixes
metals = ['P_Metal[DSB]_Edge.mtd','C_Metal[DSB].mtd','P_Metal[DSB].mtd']
seath = ['C_5290_Body[DSB][M].mtd','C_5290_Body[DSB].mtd']

diff_emission_tex_list = [
	'm10_grass_08.dds', #plant fixups in firelink near petrus
]

diff_emission_mtd_list = [
	'A19_mountains[Dn]_Edge.mtd', #firelink mountain backgrounds
]

no_mix_vert_color_mtd_list = [
	'M_4Stone[DSB][L].mtd', #bricks on floor in hallway cutscene of undead asylum
	'M[DB][L].mtd', #ceiling after first ladder in asylum
	'M_9Glass[DSB][L].mtd', #water room immediately after warden
]

#'glass' mtds seem to look more correct without specular being connected
no_spec_tex_mtd_list = [
	'M_9Glass[DSB][ML].mtd',
	'M_9Glass[DSB][L].mtd',
]

class Texan:
	def __init__(self, tex_type, x, y, clr_spc):
		self.name = ""
		self.type = tex_type	
		self.location = Vector((x,y))
		self.color_space = clr_spc
		self.node = None
	
	def init(self, path, mat):
		self.name = path.split("\\")[-1] #name of the texture
		
		if exists(path): #this kills the no character texture names
			#DS3 DDS images need to be converted to PNGs
			game_ver = bpy.context.scene.souls_plug_props.game_version
			magick_path = bpy.utils.user_resource('SCRIPTS',path="addons") + "\\souls-but-hole\\magick.exe"
			ffmpeg_path = bpy.utils.user_resource('SCRIPTS',path="addons") + "\\souls-but-hole\\ffmpeg.exe"
			if game_ver == 'DS3':
				path_png = path.replace(".dds",".png")
				if exists(path_png) == False:
					subprocess.run([magick_path,path,path_png])
					ffmpeg_fix = '-vf eq=gamma=0.5' #why is this needed? who knows!
					if exists(path_png) == False:
						subprocess.run(
							[ffmpeg_path,"-color_primaries","1","-color_trc","iec61966_2_1","-colorspace","1","-i",path,
							#"-vf","format=yuv444p12le,colorspace=all=bt709:trc=srgb:format=yuv422p",
							path_png]
						)
						#subprocess.run([ffmpeg_path,"-i",path,"-vf","eq=gamma=1:contrast=1:saturation=1",path_png])

				if exists(path_png):
					path = path_png

			img = bpy.data.images.load(path, check_existing = True)
			self.node = mat.node_tree.nodes.new(type="ShaderNodeTexImage") #handle of the texture node
			self.node.name = self.name + "_tex_node_" + self.type
			self.node.location = self.location
			self.node.image = img
			self.node.image.colorspace_settings.name = self.color_space
			self.node.image.alpha_mode = 'CHANNEL_PACKED' #always use this
			self.node.hide = True		

def create_mix_rgb(mat,x,y,mix_type='MIX'):
	mix = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
	mix.location =  Vector((x,y))
	mix.blend_type = mix_type
	mix.hide = True
	return mix

def init_material(name):
	mat = bpy.data.materials.new(name=name)
	mat.use_nodes = True
	mat.blend_method  = 'HASHED' #blended looks weird.
	mat.shadow_method = 'HASHED'
	return mat

def create_ptde_material(FlverMat, full_mat_name):
	mtd_name = FlverMat.mtd.split("\\")[-1]

	#create new material and configure defaults
	mat = init_material(full_mat_name)

	#delete default principled bsdf node
	default_node = mat.node_tree.nodes['Principled BSDF']
	mat.node_tree.nodes.remove(default_node)

	#base textures
	diff_tex_1 = Texan('g_Diffuse',    -940,320,'sRGB')
	diff_tex_2 = Texan('g_Diffuse_2',  -940,280,'sRGB')
	spec_tex_1 = Texan('g_Specular',   -940,240,'Non-Color')
	spec_tex_2 = Texan('g_Specular_2', -940,200,'Non-Color')
	bump_tex_1 = Texan('g_Bumpmap',    -940,160,'Non-Color')
	bump_tex_2 = Texan('g_Bumpmap_2',  -940,120,'Non-Color')
	dbmp_tex_1 = None #TODO: get these added in
	dbmp_tex_2 = None
	lite_tex_1 = Texan('g_Lightmap',   -940,  0,'Non-Color')

	#values we need to use
	spc_pwr = None
	spc_clr_pwr = None
	blend_mode = None

	for entry in FlverMat.textures:
		#add in custom properties for verification
		mat[str(entry.type)] = str(entry.path)
		print(str(entry.type) + " : " + str(entry.path))

		if entry.type == 'g_Diffuse':
			diff_tex_1.init(entry.path,mat)
		elif entry.type == 'g_Diffuse_2':
			diff_tex_2.init(entry.path,mat)
		elif entry.type == 'g_Specular':
			spec_tex_1.init(entry.path,mat)
		elif entry.type == 'g_Specular_2':
			spec_tex_2.init(entry.path,mat)
		elif entry.type == 'g_Bumpmap':
			bump_tex_1.init(entry.path,mat)
		elif entry.type == 'g_Bumpmap_2':
			bump_tex_2.init(entry.path,mat)
		elif entry.type == 'g_Lightmap':
			lite_tex_1.init(entry.path,mat)
	
	for p in FlverMat.mtd_params:
		if p.name == 'g_SpecularPower':
			spc_pwr_val = float(p.value)
		elif p.name == 'g_SpecularMapColorPower':
			spc_clr_pwr_val = float(p.value)
		elif p.name == 'g_BlendMode':
			blend_mode = int(p.value)
	
	#fixes color/roughness issues for specific materials
	if mtd_name in metals:
		spc_clr_pwr_val = spc_clr_pwr_val * 0.66
	elif mtd_name in seath:
		spc_clr_pwr_val = spc_clr_pwr_val * 2
		spc_pwr_val = spc_pwr_val / 10 #TODO: verify if this looks right?

	#create and configure main node depending on things
	main = None
	main_color = None
	if "Sky" not in mtd_name:
		#create specular or emission as main node
		main = mat.node_tree.nodes.new(type="ShaderNodeEeveeSpecular")
		main_color = main.inputs['Base Color']
		main_output = main.outputs['BSDF']

		#specular fixups
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
	else:
		main = mat.node_tree.nodes.new(type="ShaderNodeEmission")
		main_color = main.inputs['Color']
		main_output = main.outputs['Emission']

		#emission fixups
		main.inputs['Strength'].default_value = 1
	main.location = Vector((-160.0, 240.0))

	#insert mix nodes and ShaderNodeBsdfTransparent
	mix = mat.node_tree.nodes.new(type="ShaderNodeMixShader")
	mix.location = Vector((100.0, 300.0))
	mix.inputs['Fac'].default_value = 1.0 #just in case
	tpn = mat.node_tree.nodes.new(type="ShaderNodeBsdfTransparent")
	tpn.location = Vector((-160.0, 340.0))

	mat.node_tree.links.new(tpn.outputs['BSDF'],mix.inputs[1])
	mat.node_tree.links.new(main_output,mix.inputs[2])
	mat.node_tree.links.new(mix.outputs['Shader'],mat.node_tree.nodes['Material Output'].inputs['Surface'])

	#create and setup vertex color system
	vert_color = mat.node_tree.nodes.new(type="ShaderNodeVertexColor")
	vert_color.location = Vector((-840.0, 360.0))
	vert_color.layer_name = "Color"
	vert_color.hide = True

	vert_mult = create_mix_rgb(mat,-640,360,'MULTIPLY')
	vert_mult.inputs['Fac'].default_value = 1.0
	mat.node_tree.links.new(vert_color.outputs['Color'],vert_mult.inputs['Color2'])

	#this has to be here for lighting to work
	diff_output = None

	#use diff_alpha and vert_alpha if only one diff_tex? use diff_alpha if two?
	if diff_tex_1.node != None:
		#fixes for some "oddball" things like the skulls in the stray demon pit
		diff_tex_1.node.image.colorspace_settings.name = "sRGB"
		diff_output = diff_tex_1.node.outputs['Color']
		alph_output = diff_tex_1.node.outputs['Alpha']
		
		#check if mix diff/alpha are needed
		if diff_tex_2.node != None:
			diff_tex_2.node.image.colorspace_settings.name = "sRGB"
			diff_mix = create_mix_rgb(mat,-640,320)
			alph_mix = create_mix_rgb(mat,-640,280)
			#color mixing the diffuse maps
			mat.node_tree.links.new(vert_color.outputs['Alpha'],diff_mix.inputs['Fac'])
			mat.node_tree.links.new(diff_tex_1.node.outputs['Color'],diff_mix.inputs['Color1'])
			mat.node_tree.links.new(diff_tex_2.node.outputs['Color'],diff_mix.inputs['Color2'])
			#alpha mixing the diffuse textures
			mat.node_tree.links.new(vert_color.outputs['Alpha'],alph_mix.inputs['Fac'])
			mat.node_tree.links.new(diff_tex_1.node.outputs['Alpha'],alph_mix.inputs['Color1'])
			mat.node_tree.links.new(diff_tex_2.node.outputs['Alpha'],alph_mix.inputs['Color2'])

			diff_output = diff_mix.outputs['Color']
			alph_output = alph_mix.outputs['Color']
		else:
			min_math = mat.node_tree.nodes.new("ShaderNodeMath")
			min_math.operation = 'MINIMUM'
			min_math.location = Vector((-160.0, 500.0))
			min_math.inputs[0].default_value = 1.0
			min_math.inputs[0].default_value = 1.0

			if mtd_name not in no_mix_vert_color_mtd_list:
				mat.node_tree.links.new(vert_color.outputs['Alpha'],min_math.inputs[0])
			
			mat.node_tree.links.new(alph_output,min_math.inputs[1])
			alph_output = min_math.outputs['Value']

		mat.node_tree.links.new(alph_output,mix.inputs['Fac'])
		mat.node_tree.links.new(diff_output,vert_mult.inputs['Color1'])
		mat.node_tree.links.new(vert_mult.outputs['Color'],main_color)

		if mtd_name in diff_emission_mtd_list or diff_tex_1.node.image.name in diff_emission_tex_list:
			mat.node_tree.links.new(vert_mult.outputs['Color'],main.inputs['Emissive Color'])

	#check if specular system is needed, if so spawn it in
	if spec_tex_1.node != None:
		spec_output = spec_tex_1.node.outputs['Color']

		#check if mix rgb needed for diff
		if spec_tex_2.node != None:
			spec_mix = create_mix_rgb(mat,-640,240)
			mat.node_tree.links.new(vert_color.outputs['Alpha'],spec_mix.inputs['Fac'])
			mat.node_tree.links.new(spec_tex_1.node.outputs['Color'],spec_mix.inputs['Color1'])
			mat.node_tree.links.new(spec_tex_2.node.outputs['Color'],spec_mix.inputs['Color2'])

			spec_output = spec_mix.outputs['Color']

		#specular COLOR MAP power (plugs into specular)
		spc_clr_pwr = mat.node_tree.nodes.new(type="ShaderNodeGamma")
		spc_clr_pwr.name = "spc_clr_pwr"
		spc_clr_pwr.label = "spc_clr_pwr"
		spc_clr_pwr.hide = True
		spc_clr_pwr.location = Vector((-480.0, 240.0))
		spc_clr_pwr.inputs['Gamma'].default_value = spc_clr_pwr_val

		#inverter, needed for spec -> roughness conversion
		invert = mat.node_tree.nodes.new(type="ShaderNodeInvert")
		invert.location = Vector((-480.0, 200.0))
		invert.hide = True

		#specular power (plugs into roughness)
		spc_pwr = mat.node_tree.nodes.new(type="ShaderNodeGamma")
		spc_pwr.name = "spc_pwr"
		spc_pwr.label = "spc_pwr"
		spc_pwr.hide = True
		spc_pwr.location = Vector((-320.0, 200.0))
		spc_pwr.inputs['Gamma'].default_value = spc_pwr_val

		mat.node_tree.links.new(spec_output,spc_clr_pwr.inputs['Color'])

		if mtd_name not in no_spec_tex_mtd_list:
			mat.node_tree.links.new(spc_clr_pwr.outputs['Color'],main.inputs['Specular'])

		mat.node_tree.links.new(spec_output,invert.inputs['Color'])
		mat.node_tree.links.new(invert.outputs['Color'],spc_pwr.inputs['Color'])
		mat.node_tree.links.new(spc_pwr.outputs['Color'],main.inputs['Roughness'])

		#seath fixes
		if mtd_name == 'C_5290_Wing[DSB]_Alp.mtd':
			mat.node_tree.links.new(spec_output.outputs['Color'],main.inputs['Emissive Color'])
		
		#manus fixes
		if mtd_name == 'C_4500_Eyes1[DSB].mtd' or mtd_name == 'C_4500_Eyes2[DSB].mtd':
			mat.node_tree.links.new(spc_clr_pwr.outputs['Color'],main.inputs['Emissive Color'])
	
	if bump_tex_1.node != None:
		bump_output = bump_tex_1.node.outputs['Color']

		if bump_tex_2.node != None:
			bump_mix = create_mix_rgb(mat,-640,160)
			mat.node_tree.links.new(bump_tex_1.node.outputs['Color'],bump_mix.inputs['Color1'])
			mat.node_tree.links.new(bump_tex_2.node.outputs['Color'],bump_mix.inputs['Color2'])
			bump_output = bump_mix.outputs['Color']

		#RGB curve to invert normal map R and G channels
		rgb_curve = mat.node_tree.nodes.new(type="ShaderNodeRGBCurve")
		rgb_curve.location =  Vector((-640.0, 120.0))
		rgb_curve.hide = True
		#Curves: 0 is R, 1 is G, 2 is B, 3 is C 
		rgb_curve.mapping.curves[0].points[0].location = Vector((0.0,1.0))
		rgb_curve.mapping.curves[0].points[1].location = Vector((1.0,0.0))
		rgb_curve.mapping.curves[1].points[0].location = Vector((0.0,1.0))
		rgb_curve.mapping.curves[1].points[1].location = Vector((1.0,0.0))

		#create normal map node
		bump_node = mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
		bump_node.location = Vector((-480.0, 160.0))
		bump_node.name = mat.name + "_bumpmap_node"
		bump_node.hide = True
		bump_node.space = "TANGENT"

		mat.node_tree.links.new(bump_output,rgb_curve.inputs['Color'])
		mat.node_tree.links.new(rgb_curve.outputs['Color'],bump_node.inputs['Color'])
		mat.node_tree.links.new(bump_node.outputs['Normal'],main.inputs['Normal'])

	if lite_tex_1.node != None:
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

		lit_mix_rgb =  create_mix_rgb(mat,-900.0, -400.0,'MULTIPLY')
		lit_mix_rgb.inputs['Fac'].default_value = 1.0

		mat.node_tree.links.new(uv_map.outputs['UV'],lite_tex_1.node.inputs['Vector'])
		mat.node_tree.links.new(lite_tex_1.node.outputs['Color'],lit_pwr.inputs['Color'])
		mat.node_tree.links.new(lit_pwr.outputs['Color'],lit_mix_rgb.inputs['Color2'])
		mat.node_tree.links.new(diff_output,lit_mix_rgb.inputs['Color1'])
		mat.node_tree.links.new(lit_mix_rgb.outputs['Color'],main.inputs['Emissive Color'])

	#assign custom properties to the material relating to the MTD its based on
	mat["MTD_NAME"] = mtd_name
	for param in FlverMat.mtd_params:
		mat[str(param.name)] = str(param.value)

	return mat

def create_ds3_material(FlverMat, full_mat_name):
	mtd_name = FlverMat.mtd.split("\\")[-1]

	#create new material and configure defaults
	mat = init_material(full_mat_name)

	#delete default principled bsdf node
	default_node = mat.node_tree.nodes['Principled BSDF']
	mat.node_tree.nodes.remove(default_node)

	#base textures
	diff_tex_1 = Texan('g_DiffuseTexture',       -940,320,'sRGB')
	spec_tex_1 = Texan('g_SpecularTexture',      -940,280,'sRGB')
	shin_tex_1 = Texan('g_ShininessTexture',     -940,240,'Non-Color')
	bump_tex_1 = Texan('g_BumpmapTexture',       -940,200,'Non-Color')
	dbmp_tex_1 = Texan('g_DetailBumpmapTexture', -940,160,'Non-Color')
	disp_tex_1 = Texan('g_DisplacementTexture',  -940,120,'Non-Color')
	blod_tex_1 = Texan('g_BloodMaskTexture',     -940, 80,'Non-Color')
	#lite_tex_1 = Texan('g_Lightmap',   -940,  0,'Non-Color')

	#values we need to use
	spc_pwr = None
	spc_clr_pwr = None
	blend_mode = None

	for entry in FlverMat.textures:
		#add in custom properties for verification
		mat[str(entry.type)] = str(entry.path)
		print(str(entry.type) + " : " + str(entry.path))

		if entry.type == 'g_DiffuseTexture':
			diff_tex_1.init(entry.path,mat)
		elif entry.type == 'g_SpecularTexture':
			spec_tex_1.init(entry.path,mat)
		elif entry.type == 'g_ShininessTexture':
			shin_tex_1.init(entry.path,mat)
		elif entry.type == 'g_BumpmapTexture':
			bump_tex_1.init(entry.path,mat)
		elif entry.type == 'g_DetailBumpmapTexture':
			dbmp_tex_1.init(entry.path,mat)
		elif entry.type == 'g_DisplacementTexture':
			disp_tex_1.init(entry.path,mat)
		elif entry.type == 'g_BloodMaskTexture':
			blod_tex_1.init(entry.path,mat)

	main = mat.node_tree.nodes.new(type="ShaderNodeEeveeSpecular")
	main_color = main.inputs['Base Color']
	main_output = main.outputs['BSDF']
	main.location = Vector((-160.0, 240.0))

	#insert mix nodes and ShaderNodeBsdfTransparent
	mix = mat.node_tree.nodes.new(type="ShaderNodeMixShader")
	mix.location = Vector((100.0, 300.0))
	mix.inputs['Fac'].default_value = 1.0 #just in case
	tpn = mat.node_tree.nodes.new(type="ShaderNodeBsdfTransparent")
	tpn.location = Vector((-160.0, 340.0))

	mat.node_tree.links.new(tpn.outputs['BSDF'],mix.inputs[1])
	mat.node_tree.links.new(main_output,mix.inputs[2])
	mat.node_tree.links.new(mix.outputs['Shader'],mat.node_tree.nodes['Material Output'].inputs['Surface'])

	#create and setup vertex color system
	vert_color = mat.node_tree.nodes.new(type="ShaderNodeVertexColor")
	vert_color.location = Vector((-840.0, 360.0))
	vert_color.layer_name = "Color"
	vert_color.hide = True

	vert_mult = create_mix_rgb(mat,-640,360,'MULTIPLY')
	vert_mult.inputs['Fac'].default_value = 1.0
	mat.node_tree.links.new(vert_color.outputs['Color'],vert_mult.inputs['Color2'])

	if diff_tex_1.node != None:
		mat.node_tree.links.new(diff_tex_1.node.outputs['Color'],main_color)
	if spec_tex_1.node != None:
		mat.node_tree.links.new(spec_tex_1.node.outputs['Color'],main.inputs['Specular'])
	if shin_tex_1.node != None:
		mat.node_tree.links.new(shin_tex_1.node.outputs['Color'],main.inputs['Roughness'])
	if bump_tex_1.node != None:
		#TODO: NEED TO SPLIT RGB, pull B and adjust by .454 gamma for roughness?
		#THEN COMBINE RG AND push into normal map
		bump_output = bump_tex_1.node.outputs['Color']

		#first need to split color into RGB channels
		rgb_split = mat.node_tree.nodes.new(type='ShaderNodeSeparateRGB')
		rgb_split.location = Vector((-680,200))
		rgb_split.hide = True

		#then combine only the R and G channels
		rgb_combn = mat.node_tree.nodes.new(type='ShaderNodeCombineRGB')
		rgb_combn.location = Vector((-500,200))
		rgb_combn.inputs['B'].default_value = 1.0
		rgb_combn.hide = True

		#specular COLOR MAP power (plugs into specular)
		rough_gamma = mat.node_tree.nodes.new(type="ShaderNodeGamma")
		rough_gamma.hide = True
		rough_gamma.location = Vector((-480.0, 240.0))
		rough_gamma.inputs['Gamma'].default_value = 0.454

		mat.node_tree.links.new(bump_tex_1.node.outputs['Color'],rgb_split.inputs['Image'])
		mat.node_tree.links.new(rgb_split.outputs['R'],rgb_combn.inputs['R'])
		mat.node_tree.links.new(rgb_split.outputs['G'],rgb_combn.inputs['G'])
		mat.node_tree.links.new(rgb_split.outputs['B'],rough_gamma.inputs['Color'])
		mat.node_tree.links.new(rough_gamma.outputs['Color'],main.inputs['Roughness'])

		#RGB curve to invert normal map R and G channels
		rgb_curve = mat.node_tree.nodes.new(type="ShaderNodeRGBCurve")
		rgb_curve.location =  Vector((-640.0, 120.0))
		rgb_curve.hide = True
		#Curves: 0 is R, 1 is G, 2 is B, 3 is C 
		rgb_curve.mapping.curves[0].points[0].location = Vector((0.0,1.0))
		rgb_curve.mapping.curves[0].points[1].location = Vector((1.0,0.0))
		rgb_curve.mapping.curves[1].points[0].location = Vector((0.0,1.0))
		rgb_curve.mapping.curves[1].points[1].location = Vector((1.0,0.0))

		#create normal map node
		bump_node = mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
		bump_node.location = Vector((-480.0, 160.0))
		bump_node.name = mat.name + "_bumpmap_node"
		bump_node.hide = True
		bump_node.space = "TANGENT"

		mat.node_tree.links.new(rgb_combn.outputs['Image'],rgb_curve.inputs['Color'])
		mat.node_tree.links.new(rgb_curve.outputs['Color'],bump_node.inputs['Color'])
		mat.node_tree.links.new(bump_node.outputs['Normal'],main.inputs['Normal'])
	
	#assign custom properties to the material relating to the MTD its based on
	mat["MTD_NAME"] = mtd_name
	for param in FlverMat.mtd_params:
		mat[str(param.name)] = str(param.value)

	return mat