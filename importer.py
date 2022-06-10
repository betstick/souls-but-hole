from sys import stdout
import subprocess
import io

from .deserialization import *
from .model_generation import *

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

Job = None

def import_asset(context, asset_name, asset_type, load_mats, load_norms, overwrite, merge_verts, merge_meshes):
	prefs = context.preferences.addons['souls-but-hole'].preferences
	p = subprocess.Popen([prefs.tongue_path, prefs.ptde_data_path, prefs.yabber_path, AssetTypeToCommand[asset_type] + " " + asset_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	sr = io.BufferedReader(p.stdout)

	Job = ImportJob.Deserialize(sr)
	#print("C# IMPORT SUCCESS")

	#groups of objects
	obj_groups = []

	for i in range(len(Job.flvers)):
		CurrFlver = Job.flvers[i]
		print("CurrFlver = " + str(i))
		#obj_groups.append(CurrFlver.create_flver(load_norms))
		obj_groups.append(GenerateFlver(CurrFlver, load_norms))

#	for group in obj_groups:
#		if merge_verts:
#			for mesh_obj in group:
#				welder = mesh_obj.modifiers.new(name='Weld',type='WELD')
#				#TODO: apply the modifier
