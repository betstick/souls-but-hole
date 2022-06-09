import bpy
#from . import importer
#from . import verify
#from bpy_extras.io_utils import ImportHelper
from os.path import basename, dirname
from bpy.props import StringProperty, BoolProperty

class SoulsPlugPreferences(bpy.types.AddonPreferences):
	# this must match the add-on name, use '__package__'
	# when defining this in a submodule of a python package.
	bl_idname = basename(dirname(dirname(__file__)))

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