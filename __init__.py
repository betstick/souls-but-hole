bl_info = {
	"name": "Souls-But-Hole",
	"description": "Fromsoftware Asset Importer",
	"author": "betstick",
	"version": (0, 1, 0),
	"blender": (2, 80, 0),
	"category": "Import-Export",
	"location": "File > Import",
	"support": "COMMUNITY",
}

import bpy
from bpy.utils import register_class
from bpy.utils import unregister_class

from . import DataTypes
from . import deserialization
from . import exporter
from . import importer
from . import model_generation
from . import ui
from . import verify
from . import msb1
from . import mat_ds1

import imp
imp.reload(DataTypes)
imp.reload(deserialization)
imp.reload(exporter)
imp.reload(importer)
imp.reload(model_generation)
imp.reload(ui)
imp.reload(verify)
imp.reload(msb1)
imp.reload(mat_ds1)


classes = (
	ui.SoulsPlugPreferences,
	ui.SoulsPlugLoadPrefs,
	ui.SoulsPlugPanelSettings,
#	ui.ServerPanel,
	ui.Asset_Import_Panel,
	ui.Asset_Tools_Panel,
	ui.Asset_Export_Panel,
	ui.Scrub_Mesh_Weights,
	ui.Select_Overweighted_Verts,
	ui.ImportAsset,
#	ui.StartSpServer,
#	ui.StopSpServer,
	ui.Gauntlet,
)

def register():
	for c in classes:
		register_class(c)

	bpy.types.Scene.souls_plug_props = bpy.props.PointerProperty(type=ui.SoulsPlugPanelSettings)

def unregister():
	for c in classes:
		unregister_class(c)

	del bpy.types.Scene.souls_plug_props