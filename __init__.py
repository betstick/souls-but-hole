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

if 'bpy' not in locals():
	import bpy
	from . import ui
	from . import tools
	from . import flver
else:
	#this being needed is criminal
	import imp
	imp.reload(ui)
	imp.reload(tools)
	imp.reload(flver)

import imp
imp.reload(ui)
imp.reload(tools)
imp.reload(tools.importer)
imp.reload(flver)
imp.reload(flver.flver)
imp.reload(flver.material)
imp.reload(flver.mesh)
imp.reload(flver.skeleton)
imp.reload(flver.util)
imp.reload(flver.from_dummy)
imp.reload(flver.mtd)

def register():
	print("registered")
	ui.register()
	#flver.register()

def unregister():
	print("unregistered")
	ui.unregister()
	#flver.unregister()