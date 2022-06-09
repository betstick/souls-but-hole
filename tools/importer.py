from sys import stdout
import subprocess

from ..flver.flver import *
from .deserialization import *

from .. import flver

#list of "good enough" mtd support. shouldn't need to see in console any more.
#mtds not in this list will have their params printed out
known_mtds = [
	'C_Leather[DSB].mtd',
	'P_Leather[DSB].mtd',
	'C_DullLeather[DSB].mtd',
	'C_DullLeather[DSB]_Alp.mtd',
	'C_DullLeather[DSB]_Edge.mtd',
	'C_Metal[DSB].mtd',
	'P_Metal[DSB].mtd',
	'P_Metal[DSB]_Edge.mtd',
	'C_5290_Body[DSB].mtd',
	'C_5290_Body[DSB][M].mtd',
	'C_5290_Wing[DSB]_Alp.mtd',
	'C_4500_Eyes1[DSB].mtd',
	'C_4500_Eyes2[DSB].mtd',
]

AssetTypeToCommand = {}
AssetTypeToCommand["Character"] = "chr"
AssetTypeToCommand["Part"] = "part"
AssetTypeToCommand["Map"] = "map"
AssetTypeToCommand["Object"] = "obj"

class ImportJob:
	@staticmethod
	def Deserialize(p):
		self = ImportJob()
		self.flvers = ReadArray(p, Flver.Deserialize)
		return self

def import_asset(context, asset_name, asset_type, load_mats, load_norms, overwrite, merge_verts, merge_meshes):
	prefs = context.preferences.addons['souls-but-hole'].preferences
	p = subprocess.Popen([prefs.tongue_path, prefs.ptde_data_path, prefs.yabber_path, AssetTypeToCommand[asset_type] + " " + asset_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	#sr = io.open(p.stdout)

	Job = ImportJob.Deserialize(p)
	#print("C# IMPORT SUCCESS")

	#groups of objects
	obj_groups = []

	i = 1

	for flver in Job.flvers:
		#print('Imported FLVER ' + str(i) + ' of ' + str(len(Job.flvers)), end="\r")
		obj_groups.append(flver.create_flver(load_norms))
		#cProfile.runctx('obj_groups.append(flver.create_flver(load_norms))',globals(),locals())
		i += 1

	for group in obj_groups:
		if merge_verts:
			for mesh_obj in group:
				welder = mesh_obj.modifiers.new(name='Weld',type='WELD')
				#TODO: apply the modifier

		#select all meshes and merge them into one
		#if merge_meshes:
		#	for obj in group:
		#		obj.select_set(True)
		#		bpy.context.view_layer.objects.active = obj
		#	bpy.ops.object.join()
		#	bpy.ops.object.mode_set(mode = 'EDIT')
		#	bpy.ops.mesh.select_all(action='SELECT')
		#	bpy.ops.mesh.remove_doubles(threshold = 0.0001)
		#	bpy.ops.mesh.select_all(action='DESELECT')
		#	bpy.ops.object.mode_set(mode = 'OBJECT')
		#	bpy.ops.object.select_all(action='DESELECT')
	
	#print("Transaction took " + str(round(time.time() - import_time,2)) + "s" )