#from flver import util
from bpy.utils import register_class, unregister_class

if 'bpy' not in locals():
	import bpy
	from . import (
		preferences,
		utils
	)
else:
	import imp
	imp.reload(preferences)
	imp.reload(utils)

classes = (
	preferences.SoulsPlugPreferences,
	preferences.SoulsPlugLoadPrefs,
	utils.SoulsPlugPanelSettings,
	#utils.SoulsPlugPanel,
	utils.ServerPanel,
	utils.Asset_Import_Panel,
	utils.Asset_Tools_Panel,
	utils.Asset_Export_Panel,
	utils.Scrub_Mesh_Weights,
	utils.Select_Overweighted_Verts,
	utils.ImportAsset,
	utils.StartSpServer,
	utils.StopSpServer,
	utils.Gauntlet,
)

def register():
	for cls in classes:
		register_class(cls)

	bpy.types.Scene.souls_plug_props = bpy.props.PointerProperty(type=utils.SoulsPlugPanelSettings)

def unregister():
	for cls in classes:
		unregister_class(cls)

	del bpy.types.Scene.souls_plug_props