from sys import stdout
import subprocess
import io
import math

from .deserialization import *
from .model_generation import *

from .msb1 import *

import cProfile

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
	# Call tongue server with specified asset id
	prefs = context.preferences.addons['souls-but-hole'].preferences

	game_ver = bpy.context.scene.souls_plug_props.game_version
	data_path = ""
	cache_path = ""

	if game_ver == 'PTDE':
		data_path = prefs.ptde_data_path
		cache_path = bpy.utils.user_resource('SCRIPTS',path="addons") + "\\souls-but-hole\\dds_paths.txt"
	elif game_ver == 'DS3':
		data_path = prefs.ds3_data_path
		cache_path = bpy.utils.user_resource('SCRIPTS',path="addons") + "\\souls-but-hole\\dds_paths_ds3.txt"

	p = subprocess.Popen([prefs.tongue_path, data_path, prefs.yabber_path, cache_path, AssetTypeToCommand[asset_type] + " " + asset_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

	# Parse output
	sr = io.BufferedReader(p.stdout)

	if asset_type == 'Map':
		msb = MSB1.Deserialize(sr)

		for mp in msb.parts.map_pieces:
			print(mp.part.name + " " + str(mp.part.position) + " " + str(mp.part.rotation))

	Job = ImportJob.Deserialize(sr)

	# load_norms is somehow not in scope?? ugly workaround
	#cProfile.runctx("[GenerateFlver(CurrFlver, " + str(load_norms) + ") for CurrFlver in Job.flvers]",globals(),locals())

	flvers = [GenerateFlver(CurrFlver, load_norms) for CurrFlver in Job.flvers]

	if asset_type == 'Map':
		for flver in flvers:
			"""for emo in msb.events.map_offsets:
				if emo.event.part_name in flver.name:
					flver.location = emo.position
					if mp.part.rotation[0] != 0:
						flver.rotation_axis_angle[0] = math.radians(emo.degree)"""
			for mp in msb.parts.map_pieces:
				if mp.part.name[(len(mp.part.name) - 5):] == "_0000":
					if mp.part.name[:(len(mp.part.name) - 5)] in flver.name:
						flver.location = mp.part.position
						if mp.part.rotation[0] != 0:
							flver.rotation_euler[0] = math.radians(mp.part.rotation[0])
						if mp.part.rotation[2] != 0:
							flver.rotation_euler[1] = math.radians(mp.part.rotation[2])
						if mp.part.rotation[1] != 0:
							flver.rotation_euler[2] = math.radians(0 - mp.part.rotation[1])
				elif "_" not in mp.part.name:
					if mp.part.name in flver.name:
						flver.location = mp.part.position
						if mp.part.rotation[0] != 0:
							flver.rotation_euler[0] = math.radians(mp.part.rotation[0])
						if mp.part.rotation[2] != 0:
							flver.rotation_euler[1] = math.radians(mp.part.rotation[2])
						if mp.part.rotation[1] != 0:
							flver.rotation_euler[2] = math.radians(0 - mp.part.rotation[1])