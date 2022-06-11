from asyncio import subprocess
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
import time
import socket
import subprocess
from os.path import basename
from os.path import dirname

from . import importer
from . import verify

class SoulsPlugPanelSettings(bpy.types.PropertyGroup):
	#bl_idname = __package__.split('.')[0]
	spServerIp: StringProperty(
		name = "Address",
		subtype = 'NONE',
		default = '127.0.0.1',
	)

	spServerPort: StringProperty(
		name = "Port",
		subtype = 'NONE',
		default = '13131',
	)

	#TODO: figure out how to make this input smaller
	asset_id: StringProperty(
		name = "Asset ID",
		subtype = 'NONE',
		maxlen = 12,
	)

	asset_type: EnumProperty(
		items=(
			("Character", "Character", "Character"),
			("Map", "Map", "Map"),
			("Part", "Part", "Part"),
		),
		name="Type",
		default="Character",
		description="Type of Asset to Load"
	)

	asset_load_mats: BoolProperty(
		name = "Load Materials",
		default = True,
		description="Load Materials"
	)

	asset_mat_type: EnumProperty(
		items=(
			("Eevee", "Eevee", "Eevee"),
			("Cycles", "Cycles", "Cycles"),
			("LuxCore", "LuxCore", "LuxCore"), #only if the user has it installed?
		),
		name="Engine",
		default="Eevee",
		description="Eevee for accuracy, Cycles for compatibility, LuxCore for looking cool"
	)

	game_version: EnumProperty(
		items=(
			("PTDE", "PTDE", "PTDE"),
			("DSR", "DSR", "DSR"),
			("DS2", "DS2", "DS2"),
			("DS3", "DS3", "DS3"),
		),
		name="Game",
		default="PTDE",
		description="Which game to import from"
	)

	#if yabber should overwrite existing extractions
	asset_over_write : BoolProperty(
		name = "Overwrite Existing Extractions",
		default = False,
		description="Force Yabber to extract over top of existing files"
	)

	#whether to run merge on dist for each sub mesh
	asset_merge_verts : BoolProperty(
		name = "Merge Verts",
		default = True,
		description="Merge Overlapping/Zero Distance Verts (Recommended)"
	)

	#whether to merge all meshes into a single one to simply editing
	asset_merge_meshes : BoolProperty(
		name = "Merge Meshes",
		default = False,
		description="Merge All FLVER Submeshes into a single mesh (Not Recommmended)"
	)

	#whether to set norms from the flver
	asset_load_norms : BoolProperty(
		name = "Load Custom Normals",
		default = True,
		description="Load Normals from FLVER"
	)

	#prints unkown mtds to console just in case. for debugging only
	print_unkown_mtds : BoolProperty(
		name = "Print Unkown MTDs",
		default = False,
		description="Print Unkown MTDs"
	)

class SoulsPlugPanel(bpy.types.Panel):
	bl_idname = 'TEST_PT_souls_plug'
	bl_label = 'Souls Plug'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Souls Plug'

	#addon_key = __package__.split('.')[0]

	#@classmethod
	#def poll(cls, context):
	#	return context.mode == 'OBJECT'

	def draw(self,context):
		#addon = context.preferences.addons[self.addon_key]
		#addon_props = addon.preferences
		layout = self.layout

		box = layout.box()

		box = layout.box()
		box.label(text="Sample Text")
		#box.operator('object.verify_mesh', text='Verify Selected Meshes')

class ServerPanel(bpy.types.Panel):
	bl_idname = 'TEST_PT_souls_plug_panel_server'
	bl_label = 'Server'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Souls Plug'

	def draw(self,context):
		layout = self.layout
		layout.label(text="Tongue Server")
		layout.prop(context.scene.souls_plug_props, "spServerIp")
		layout.prop(context.scene.souls_plug_props, "spServerPort")
		layout.operator('context.start_sp_server', text='Start Server')
		layout.operator('context.stop_sp_server', text='Stop Server')

class Asset_Import_Panel(bpy.types.Panel):
	bl_idname = 'TEST_PT_souls_plug_panel_import'
	bl_label = 'Importer'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Souls Plug'

	def draw(self,context):
		layout = self.layout
		layout.prop(context.scene.souls_plug_props, "game_version")
		layout.prop(context.scene.souls_plug_props, "asset_type")
		layout.prop(context.scene.souls_plug_props, "asset_id")
		#layout.prop(context.scene.souls_plug_props, "asset_mat_type")
		layout.prop(context.scene.souls_plug_props, "asset_over_write")
		layout.prop(context.scene.souls_plug_props, "asset_merge_verts")
		layout.prop(context.scene.souls_plug_props, "asset_merge_meshes")
		layout.prop(context.scene.souls_plug_props, "asset_load_mats")
		layout.prop(context.scene.souls_plug_props, "asset_load_norms")
		layout.prop(context.scene.souls_plug_props, "print_unkown_mtds")
		layout.operator("scene.import_from_asset", text='Import Asset')
		layout.operator("scene.import_gauntlet", text="Import Gauntlet")

class Asset_Export_Panel(bpy.types.Panel):
	bl_idname = 'TEST_PT_souls_plug_panel_export'
	bl_label = 'Exporter'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Souls Plug'

	def draw(self,context):
		layout = self.layout
		layout.label(text="To be completed at some point...")

class Asset_Tools_Panel(bpy.types.Panel):
	bl_idname = 'TEST_PT_souls_plug_panel_tools'
	bl_label = 'Tools'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Souls Plug'

	def draw(self,context):
		layout = self.layout
		layout.label(text="To be completed at some point...")
		layout.operator("object.scrub_mesh_weights", text='Scrub Mesh Weights')
		layout.operator("object.select_overweighted_verts", text='Select Overweighted Verts')

class StartSpServer(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "context.start_sp_server" # <- put this string in layout.operator()
	bl_label = "Start SP Server" # <- button name
	bl_description = "Start SP Server"

	@classmethod
	def poll(cls, context):
		# TODO: check if server is running
		return context.mode == 'OBJECT'

	def execute(self, context):
		p = subprocess.Popen([
			context.preferences.addons['souls-but-hole'].preferences.tongue_path,
			'"' + context.preferences.addons['souls-but-hole'].preferences.ptde_data_path + '"',
			'"' + context.preferences.addons['souls-but-hole'].preferences.yabber_path + '"',
		])

		return {'FINISHED'}

class StopSpServer(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "context.stop_sp_server" # <- put this string in layout.operator()
	bl_label = "Stop SP Server" # <- button name
	bl_description = "Stop SP Server"

	@classmethod
	def poll(cls, context):
		# TODO: check if server is running
		return context.mode == 'OBJECT'

	def execute(self, context):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			host="127.0.0.1" #TODO: read from preferences, if they're set
			port=13131

			sock.connect((host, port))
			message = "stop"
			sock.sendall(message.encode('utf-8'))

		return {'FINISHED'}

class Scrub_Mesh_Weights(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "object.scrub_mesh_weights" # <- put this string in layout.operator()
	bl_label = "Scrub Mesh Weights" # <- button name
	bl_description = "Removes unused vertex groups from selected meshes"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		op_time = time.time()

		verify.scrub_mesh_weights(bpy.context)

		print("Scrubbing meshes took: " + str(round(time.time() - op_time,2)) + "s")
		return {'FINISHED'}

#TODO: confirm that this actually works, or does anything.... 
class Select_Overweighted_Verts(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "object.select_overweighted_verts" # <- put this string in layout.operator()
	bl_label = "Select Overweighted Verts" # <- button name
	bl_description = "Selects vertices with more than four weights"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.mode == 'OBJECT'

	def execute(self, context):
		op_time = time.time()

		verify.select_overweighted_verts(bpy.context)

		print("Selection took: " + str(round(time.time() - op_time,2)) + "s")
		return {'FINISHED'}

class ImportAsset(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "scene.import_from_asset" # <- put this string in layout.operator()
	bl_label = "Import Souls Asset" # <- button name
	bl_description = "What do you think it does?"

	@classmethod
	def poll(cls, context):
		return context.mode == 'OBJECT'

	def execute(self, context):
		op_time = time.time()
		importer.import_asset(
			context,
			context.scene.souls_plug_props.asset_id,
			context.scene.souls_plug_props.asset_type,
			context.scene.souls_plug_props.asset_load_mats,
			context.scene.souls_plug_props.asset_load_norms,
			context.scene.souls_plug_props.asset_over_write,
			context.scene.souls_plug_props.asset_merge_verts,
			context.scene.souls_plug_props.asset_merge_meshes
		)
		print("Total import operation took: " + str(round(time.time() - op_time,2)) + "s")
		return {'FINISHED'}

class ExportAsset(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "scene.export_from_asset" # <- put this string in layout.operator()
	bl_label = "Export Souls Asset" # <- button name
	bl_description = "What do you think it does?"

	@classmethod
	def poll(cls, context):
		return context.mode == 'OBJECT'

	def execute(self, context):
		op_time = time.time()
		exporter.export_flver(
			context,
			context.scene.souls_plug_props.asset_id,
			context.scene.souls_plug_props.asset_type
		)
		print("Total operation took: " + str(round(time.time() - op_time,2)) + "s")
		return {'FINISHED'}

class Gauntlet(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "scene.import_gauntlet"
	bl_label = "Run Import Gauntlet"
	bl_description = "Runs a handful of difficult imports to test performance and accuracy"

	@classmethod
	def poll(cls, context):
		return context.mode == 'OBJECT'

	def execute(self, context):
		op_time = time.time()

		test_ids = ["5370","5220","4500","5290","2920","2790","5340"]

		for id in test_ids:
			importer.import_asset(
				context,
				id,
				"Character",
				True,
				True,
				False,
				False,
				False
			)

		print("Guantlet took: " + str(round(time.time() - op_time,2)) + "s")
		return {'FINISHED'}

class SoulsPlugPreferences(bpy.types.AddonPreferences):
	# this must match the add-on name, use '__package__'
	# when defining this in a submodule of a python package.
	#bl_idname = basename(dirname(dirname(__file__)))
	bl_idname = basename(dirname(__file__))

	"""Display example preferences"""
	#bl_idname = "object.souls_plug_prefs_settings"

	yabber_path: StringProperty(
		name="Yabber Binary Path",
		subtype='FILE_PATH',
        default='C:/Users/batman/Desktop/yabber/Yabber.exe',
	)

	tongue_path: StringProperty(
		name="Souls Tongue Binary Path",
		subtype='FILE_PATH',
        default='C:/Users/batman/source/repos/souls-plug/souls-tongue/souls-tongue/bin/Debug/net5.0/souls-tongue.exe',
	)

	ptde_data_path: StringProperty(
		name="Dark Souls PTDE Data Path",
		subtype='FILE_PATH',
        default='C:/Program Files (x86)/Steam/steamapps/common/Dark Souls Prepare to Die Edition/DATA',
	)

	ds3_data_path: StringProperty(
		name="Dark Souls 3 Data Path",
		subtype='FILE_PATH',
        default='D:/SteamLibrary/steamapps/common/DARK SOULS III',
	)

	def draw(self, context):
		layout = self.layout
		layout.label(text="Sample Text")

		layout.prop(self, "yabber_path")
		layout.prop(self, "tongue_path")
		layout.prop(self, "ptde_data_path")
		#layout.prop(self, "dsr_data_path")
		#layout.prop(self, "ds2_data_path")
		layout.prop(self, "ds3_data_path")

#does this even do anything???
class SoulsPlugLoadPrefs(bpy.types.Operator):
	"""Display example preferences"""
	bl_idname = "object.souls_plug_prefs"
	bl_label = "Add-on Preferences Example"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		preferences = context.preferences
		addon_prefs = preferences.addons[__name__].preferences

		info = ("Path: %s, Number: %d, Boolean %r" %
				(addon_prefs.filepath, addon_prefs.number, addon_prefs.boolean))

		self.report({'INFO'}, info)
		return {'FINISHED'}